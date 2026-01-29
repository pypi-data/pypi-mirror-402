"""SkymapPlotter: Generates PNG visualizations from FITS sky maps.

Uses ligo.skymap.plot for all-sky visualization of Bayestar output.
"""

from __future__ import annotations

import io
import logging
import time
from dataclasses import dataclass, field
from typing import ClassVar, Optional

from sgn.base import SinkPad, SourcePad, TransformElement
from sgn.frames import Frame
from sgneskig.metrics import MetricsCollectorMixin, metrics

_logger = logging.getLogger("sgn.sgnllai.skymap_plotter")


@dataclass
class SkymapPlotter(TransformElement, MetricsCollectorMixin):
    """Generates PNG visualization from FITS sky map.

    Takes events with fits_data (bytes) and produces png_data (bytes).
    Uses ligo.skymap.plot for proper all-sky projections.

    Pads:
    - Sink: "in" (configurable)
    - Sources: "out", "metrics"
    """

    # Declarative metrics schema
    metrics_schema: ClassVar = metrics(
        [
            ("plot_time", "timing", [], "Plot generation time"),
            ("plots_generated", "counter", [], "Plots generated"),
            ("plots_failed", "counter", [], "Plot generation failures"),
        ]
    )

    # Plot configuration
    projection: str = "astro hours mollweide"
    dpi: int = 150
    figsize: tuple[float, float] = field(default_factory=lambda: (8.0, 5.0))
    contour_levels: list[int] = field(default_factory=lambda: [50, 90])
    colormap: str = "cylon"  # ligo.skymap default colormap

    # Field names
    fits_data_field: str = "fits_data"
    png_data_field: str = "png_data"

    # Pad names
    input_pad_name: str = "in"
    output_pad_name: str = "out"

    # Metrics settings
    metrics_enabled: bool = True

    def __post_init__(self):
        # Set up pad names before super().__post_init__()
        self.sink_pad_names = [self.input_pad_name]
        self.source_pad_names = [self.output_pad_name]
        # Note: metrics written directly via MetricsWriter (no metrics pad)

        super().__post_init__()
        self._logger = _logger

        # Initialize metrics collection
        self._init_metrics()

        # Current state
        self._current_frame: Optional[Frame] = None
        self._output_data: list[dict] = []

        self._logger.info(
            f"SkymapPlotter initialized (projection={self.projection}, dpi={self.dpi})"
        )

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive frame from upstream."""
        self._current_frame = frame

    def internal(self) -> None:
        """Generate PNG plots from FITS data."""
        self._output_data = []
        frame = self._current_frame

        if frame is None or frame.is_gap or not frame.data:
            return

        # Process events
        events = frame.data if isinstance(frame.data, list) else [frame.data]

        for event in events:
            self._process_event(event)

    def _process_event(self, event: dict) -> None:
        """Generate PNG plot for a single event."""
        # Get FITS data
        fits_data = event.get(self.fits_data_field)
        if fits_data is None:
            self._logger.warning(f"No {self.fits_data_field} in event, skipping plot")
            self._output_data.append(event)
            return

        graceid = event.get("g_event", {}).get("graceid", "unknown")

        try:
            start_time = time.time()

            # Generate PNG
            png_data = _generate_skymap_png(
                fits_data=fits_data,
                projection=self.projection,
                dpi=self.dpi,
                figsize=self.figsize,
                contour_levels=self.contour_levels,
                colormap=self.colormap,
            )

            elapsed = time.time() - start_time

            self.record_timing("plot_time", elapsed)
            self.increment_counter("plots_generated")

            self._logger.info(
                f"Generated PNG for {graceid} in {elapsed:.2f}s "
                f"({len(png_data)} bytes)"
            )

            # Add PNG to event
            self._output_data.append(
                {
                    **event,
                    self.png_data_field: png_data,
                    "plot_time": elapsed,
                }
            )

        except Exception as e:
            self.increment_counter("plots_failed")
            self._logger.error(f"Failed to generate PNG for {graceid}: {e}")
            # Pass through without PNG
            self._output_data.append({**event, "plot_error": str(e)})

    def new(self, pad: SourcePad) -> Frame:
        """Return output frame for the requested pad."""
        eos = self._current_frame.EOS if self._current_frame else False

        # Pass through data
        return Frame(
            data=self._output_data if self._output_data else None,
            is_gap=not self._output_data,
            EOS=eos,
        )


def _generate_skymap_png(
    fits_data: bytes,
    projection: str,
    dpi: int,
    figsize: tuple[float, float],
    contour_levels: list[int],
    colormap: str,
) -> bytes:
    """Generate PNG bytes from FITS sky map data.

    Extracted as module-level function for easier testing.
    """
    import gzip

    # Import matplotlib with non-interactive backend
    import matplotlib

    matplotlib.use("Agg")
    # Import ligo.skymap plotting (registers projections)
    import ligo.skymap.plot  # noqa: F401
    import matplotlib.pyplot as plt
    from ligo.skymap import postprocess
    from ligo.skymap.io import fits as skymap_fits

    # Decompress if gzipped
    if fits_data[:2] == b"\x1f\x8b":
        fits_data = gzip.decompress(fits_data)

    # Read sky map from bytes - use moc=False to get flat HEALPix array
    fits_io = io.BytesIO(fits_data)
    skymap, _ = skymap_fits.read_sky_map(fits_io, moc=False)

    # Create figure with all-sky projection
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111, projection=projection)

    # Plot the sky map (imshow_hpx added by ligo.skymap.plot)
    ax.imshow_hpx(skymap, cmap=colormap)  # type: ignore[attr-defined]

    # Add contours if levels specified
    if contour_levels:
        try:
            # Find credible levels
            cls = postprocess.find_greedy_credible_levels(skymap)
            # Add contours
            for level in contour_levels:
                ax.contour_hpx(  # type: ignore[attr-defined]
                    cls,
                    levels=[level / 100.0],
                    colors="k",
                    linewidths=0.5,
                )
        except Exception:  # noqa: S110
            # Contours are optional - don't fail if they can't be drawn
            pass

    # Add grid
    ax.grid()

    # Save to PNG bytes
    png_io = io.BytesIO()
    fig.savefig(png_io, format="png", bbox_inches="tight")
    plt.close(fig)

    png_io.seek(0)
    return png_io.read()
