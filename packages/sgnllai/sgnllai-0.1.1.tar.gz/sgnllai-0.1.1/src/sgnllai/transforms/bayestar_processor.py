"""BayestarProcessor: Runs Bayestar sky localization in a background thread.

Uses SGN's ParallelizeTransformElement for concurrent processing with
the ligo.skymap.bayestar.localize() Python API.
"""

from __future__ import annotations

import base64
import gzip
import io
import logging
import os
import queue
import time
from dataclasses import dataclass
from typing import ClassVar

from sgn.base import SinkPad, SourcePad
from sgn.frames import Frame
from sgn.subprocess import ParallelizeTransformElement, WorkerContext
from sgneskig.metrics import MetricsCollectorMixin, metrics

_logger = logging.getLogger("sgn.sgnllai.bayestar_processor")


@dataclass
class BayestarProcessor(ParallelizeTransformElement, MetricsCollectorMixin):
    """Runs Bayestar sky localization in a background worker thread.

    Uses the ligo.skymap.bayestar.localize() Python API for sky localization.
    Input events should contain base64-encoded coinc.xml in the g_event.xml field.
    Output events are augmented with fits_data (bytes) containing the sky map.

    Pads:
    - Sink: "in" (configurable)
    - Sources: "out", "metrics"
    """

    # Declarative metrics schema
    metrics_schema: ClassVar = metrics(
        [
            ("bayestar_time", "timing", ["worker_id"], "Bayestar processing time"),
            ("bayestar_success", "counter", ["worker_id"], "Successful localizations"),
            ("bayestar_failure", "counter", ["worker_id"], "Failed localizations"),
        ]
    )

    # Bayestar configuration
    worker_id: int = 0
    f_low: float = 30.0
    waveform: str = (
        "IMRPhenomD"  # IMR waveform - handles all masses, no external ROM files
    )
    output_dir: str = "/tmp/bayestar"  # noqa: S108

    # Pad names
    input_pad_name: str = "in"
    output_pad_name: str = "out"

    # ParallelizeTransformElement settings
    _use_threading_override: bool = True  # Use threading (Python API is thread-safe)
    queue_maxsize: int = 10

    # Metrics settings
    metrics_enabled: bool = True

    def __post_init__(self):
        # Set up pad names before super().__post_init__()
        self.sink_pad_names = [self.input_pad_name]
        self.source_pad_names = [self.output_pad_name]
        # Note: metrics written directly via MetricsWriter (no metrics pad)

        # Must call TransformElement.__post_init__ before ParallelizeTransformElement
        from sgn.base import TransformElement

        TransformElement.__post_init__(self)

        # Initialize metrics (before parallelization which needs clean state)
        self._init_metrics()

        # Now initialize the parallelization
        from sgn.subprocess import _ParallelizeBase

        _ParallelizeBase.__post_init__(self)

        self._logger = _logger
        self._pending_output: Frame | None = None

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        self._logger.info(
            f"BayestarProcessor worker {self.worker_id} initialized "
            f"(f_low={self.f_low}, waveform={self.waveform})"
        )

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Send frame to worker thread."""
        if frame.EOS:
            self.at_eos = True

        # Put frame in input queue for worker
        if not frame.is_gap and frame.data:
            self.in_queue.put(frame)

    def worker_process(
        self,
        context: WorkerContext,
        worker_id: int,
        f_low: float,
        waveform: str,
        output_dir: str,
    ) -> None:
        """Background worker: run Bayestar localization.

        This runs in a separate thread, processing events from the input queue.
        """
        # Import heavy dependencies inside worker to avoid serialization
        from ligo.skymap.bayestar import localize
        from ligo.skymap.io import fits as skymap_fits
        from ligo.skymap.io.events.ligolw import LigoLWEventSource

        try:
            frame = context.input_queue.get(timeout=1.0)
        except queue.Empty:
            return

        if frame is None or frame.is_gap:
            context.output_queue.put(frame)
            return

        # Process events in batch
        events = frame.data if isinstance(frame.data, list) else [frame.data]
        results = []

        for event in events:
            try:
                result = _process_single_event(
                    event,
                    worker_id=worker_id,
                    f_low=f_low,
                    waveform=waveform,
                    output_dir=output_dir,
                    localize_fn=localize,
                    event_source_cls=LigoLWEventSource,
                    write_sky_map_fn=skymap_fits.write_sky_map,
                )
                results.append(result)
            except Exception as e:
                _logger.error(f"Worker {worker_id}: Bayestar failed for event: {e}")
                # Add event with error marker
                results.append({**event, "bayestar_error": str(e)})

        # Put results back
        output_frame = Frame(
            data=results if results else None,
            is_gap=not results,
            EOS=frame.EOS,
        )
        context.output_queue.put(output_frame)

    def internal(self) -> None:  # type: ignore[override]
        """Check worker status and collect pending output."""
        super().internal()

        # Try to get output from worker (non-blocking)
        try:
            self._pending_output = self.out_queue.get_nowait()
        except queue.Empty:
            self._pending_output = None

    def new(self, pad: SourcePad) -> Frame:
        """Return output frame for the requested pad."""
        # Return pending output or gap frame
        if self._pending_output is not None:
            frame = self._pending_output
            self._pending_output = None

            # Record metrics from results
            if frame.data:
                for event in (
                    frame.data if isinstance(frame.data, list) else [frame.data]
                ):
                    if "bayestar_error" in event:
                        self.increment_counter(
                            "bayestar_failure",
                            tags={"worker_id": str(self.worker_id)},
                        )
                    elif "bayestar_time" in event:
                        self.record_timing(
                            "bayestar_time",
                            event["bayestar_time"],
                            tags={"worker_id": str(self.worker_id)},
                        )
                        self.increment_counter(
                            "bayestar_success",
                            tags={"worker_id": str(self.worker_id)},
                        )

            return frame

        return Frame(data=None, is_gap=True, EOS=self.at_eos)


def _process_single_event(
    event: dict,
    worker_id: int,
    f_low: float,
    waveform: str,
    output_dir: str,
    localize_fn,
    event_source_cls,
    write_sky_map_fn,
) -> dict:
    """Process a single event with Bayestar.

    Extracted as a module-level function for easier testing.
    """
    start_time = time.time()

    # Get XML from event
    g_event = event.get("g_event", event)
    xml_b64 = g_event.get("xml")
    graceid = g_event.get("graceid", "unknown")

    if not xml_b64:
        raise ValueError(f"No XML data in event for {graceid}")

    # Decode XML (may be gzip compressed)
    xml_bytes = base64.b64decode(xml_b64)

    # Check if gzipped
    if xml_bytes[:2] == b"\x1f\x8b":
        xml_bytes = gzip.decompress(xml_bytes)

    # Parse events from XML
    # PSDs are embedded in the coinc.xml, so pass the same data as psd_file
    xml_io = io.BytesIO(xml_bytes)
    psd_io = io.BytesIO(xml_bytes)
    event_source = event_source_cls(xml_io, psd_file=psd_io, coinc_def=None)

    if not event_source:
        raise ValueError(f"No events found in XML for {graceid}")

    # Get first (usually only) event
    coinc_id, ligo_event = next(iter(event_source.items()))

    # Run Bayestar localization
    skymap = localize_fn(ligo_event, waveform=waveform, f_low=f_low)

    # Write FITS to temporary file
    fits_path = os.path.join(output_dir, f"{graceid}.fits.gz")
    write_sky_map_fn(fits_path, skymap)

    # Read FITS bytes
    with open(fits_path, "rb") as f:
        fits_data = f.read()

    elapsed = time.time() - start_time

    _logger.info(
        f"Worker {worker_id}: Bayestar completed for {graceid} "
        f"in {elapsed:.2f}s ({len(fits_data)} bytes)"
    )

    # Return augmented event
    return {
        **event,
        "fits_data": fits_data,
        "fits_path": fits_path,
        "bayestar_time": elapsed,
    }
