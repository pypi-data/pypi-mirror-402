"""SuperEventCreator: Clusters GW events by GPS time and manages GraceDB superevents.

Input: Frame(data=list[dict]) - batch of events from KafkaSource
Output:
- supers pad: Superevent + triggering G event (events that were uploaded to GraceDB)
- skipped pad: Events that were NOT uploaded (lower SNR than current preferred)
"""

from __future__ import annotations

import bisect
import logging
import time
from dataclasses import dataclass
from typing import ClassVar, Optional

from sgn.base import SinkPad, SourcePad, TransformElement
from sgn.frames import Frame
from sgneskig.metrics import MetricsCollectorMixin, metrics

from sgnllai.gracedb import GraceDBMixin

# Use sgn.sgnllai hierarchy for SGNLOGLEVEL control
_logger = logging.getLogger("sgn.sgnllai.superevent_creator")


@dataclass
class SuperEventCreator(TransformElement, MetricsCollectorMixin, GraceDBMixin):
    """Clusters GW events by GPS time and manages GraceDB superevents.

    Behavior:
    - New event outside existing windows → Create G event + superevent in GraceDB
    - Event within window with better SNR → Upload G event, update superevent preferred
    - Event within window with lower SNR → Skip GraceDB upload, emit to skipped pad

    Outputs:
    - [supers] pad: Superevent + triggering G event (uploaded to GraceDB)
    - [skipped] pad: Events not uploaded (lower SNR than current preferred)
    """

    # Declarative metrics schema - discovered by MetricsPipeline
    # Timing metrics use points (sparse data) except elapsed which is continuous
    # NOTE: The elapsed metric name must match elapsed_metric_name below.
    # This allows auto-tracking to record the metric while the schema
    # provides the description for Grafana dashboard titles.
    _quarter = {"width": "quarter"}
    _quarter_both = {
        "width": "quarter",
        "visualizations": [
            {"type": "timeseries", "draw_style": "points", "show_points": "always"},
            {"type": "histogram", "bucket_count": 20},
        ],
    }
    metrics_schema: ClassVar = metrics(
        [
            (
                "preferred_events_uploaded",
                "counter",
                ["pipeline"],
                "Preferred G events uploaded (immediate)",
                _quarter,
            ),
            (
                "events_skipped",
                "counter",
                ["pipeline"],
                "Events skipped (lower SNR)",
                _quarter,
            ),
            ("superevents_created", "counter", [], "Superevents created", _quarter),
            ("superevents_updated", "counter", [], "Superevents updated", _quarter),
            (
                "createEvent_time",
                "timing",
                ["pipeline"],
                "createEvent API duration",
                _quarter_both,
            ),
            (
                "createEvent_failure",
                "counter",
                ["pipeline"],
                "Failed createEvent calls",
                _quarter,
            ),
            (
                "createSuperevent_time",
                "timing",
                [],
                "createSuperevent API duration",
                _quarter_both,
            ),
            (
                "updateSuperevent_time",
                "timing",
                [],
                "updateSuperevent API duration",
                _quarter_both,
            ),
            (
                "superevent_creator_elapsed",
                "timing",
                [],
                "SuperEventCreator cycle time",
                _quarter_both,
            ),
        ]
    )

    # GraceDB settings
    gracedb_url: str = "https://gracedb-test.ligo.org/api/"
    gracedb_group: str = "CBC"
    gracedb_search: str = "AllSky"
    event_created_metric: str = "preferred_events_uploaded"  # Override mixin default

    # Event clustering parameters
    window_duration: float = 5.0  # ±2.5s window around first event
    max_event_time: int = 7200  # 2 hours

    # Configurable pad names (can be set to topic names for cleaner linking)
    input_pad_name: str = "in"
    supers_pad_name: str = "supers"
    skipped_pad_name: str = "skipped"

    # Metrics settings (from MetricsCollectorMixin)
    metrics_enabled: bool = True
    track_elapsed_time: bool = True
    # NOTE: Must match the name in metrics_schema above for proper Grafana titles
    elapsed_metric_name: str = "superevent_creator_elapsed"

    def __post_init__(self):
        # Set up pad names before super().__post_init__()
        self.sink_pad_names = [self.input_pad_name]
        self.source_pad_names = [
            self.supers_pad_name,
            self.skipped_pad_name,
        ]
        # Note: metrics written directly via MetricsWriter (no metrics pad)

        super().__post_init__()
        self._logger = _logger

        # Initialize metrics collection (from MetricsCollectorMixin)
        self._init_metrics()

        # Initialize GraceDB client (from GraceDBMixin)
        self._init_gracedb()

        # Event storage: t_0 → superevent state
        self._superevents: dict[float, dict] = {}
        # Sorted list of t_0 values for efficient bisect lookup
        self._superevent_times: list[float] = []

        # Output buffers for current iteration (pad_name → list of outputs)
        self._outputs: dict[str, list[dict]] = {
            self.supers_pad_name: [],
            self.skipped_pad_name: [],
        }

        # Current input state
        self._current_frame: Optional[Frame] = None

    # ─────────────────────────────────────────────────────────
    # SGN Element Methods
    # ─────────────────────────────────────────────────────────

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive event frame from KafkaSource."""
        self._current_frame = frame

    def internal(self) -> None:
        """Process batch of events: cluster, create/update in GraceDB."""
        for pad_name in self._outputs:
            self._outputs[pad_name] = []

        if self._current_frame is None:
            return

        if self._current_frame.is_gap or not self._current_frame.data:
            return

        # Process all events in batch
        for event in self._current_frame.data:
            self._process_event(event)

        # Cleanup old superevents
        self._cleanup_old_superevents()

    def new(self, pad: SourcePad) -> Frame:
        """Emit batch output on appropriate pad."""
        pad_name = pad.pad_name
        eos = self._current_frame.EOS if self._current_frame else False

        data = self._outputs.get(pad_name)
        return Frame(data=data or None, is_gap=not data, EOS=eos)

    # ─────────────────────────────────────────────────────────
    # Event Processing Logic
    # ─────────────────────────────────────────────────────────

    def _find_superevent(self, gpstime: float) -> Optional[float]:
        """Find existing superevent containing this GPS time, return t_0.

        Uses bisect to efficiently find the closest superevent t_0 within
        ±(window_duration/2) of the given GPS time. When multiple superevents
        could match (overlapping windows), returns the one with closest t_0.
        """
        if not self._superevent_times:
            return None

        half = self.window_duration / 2

        # Find insertion point for gpstime in sorted list
        idx = bisect.bisect_left(self._superevent_times, gpstime)

        # Check candidates: idx-1 and idx (the two closest t_0 values)
        candidates = []
        for i in [idx - 1, idx]:
            if 0 <= i < len(self._superevent_times):
                t_0 = self._superevent_times[i]
                if abs(gpstime - t_0) <= half:  # within window
                    candidates.append(t_0)

        if not candidates:
            return None

        # Return closest t_0
        return min(candidates, key=lambda t: abs(gpstime - t))

    def _process_event(self, event: dict) -> None:
        """Main logic: create new superevent or update existing one."""
        gpstime = event["gpstime"]
        existing_t0 = self._find_superevent(gpstime)

        if existing_t0 is None:
            self._create_new_superevent(event)
        else:
            superevent = self._superevents[existing_t0]
            if event["snr"] > superevent["preferred_snr"]:
                self._update_superevent(existing_t0, event)
            else:
                self._outputs[self.skipped_pad_name].append(
                    {
                        **event,
                        "reason": "lower_snr",
                        "superevent_id": superevent["superevent_id"],
                        "preferred_snr": superevent["preferred_snr"],
                    }
                )
                self.increment_counter(
                    "events_skipped", tags={"pipeline": event["pipeline"]}
                )

    def _emit_superevent(
        self,
        action: str,
        superevent: dict,
        event: dict,
        graceid: str,
        previous_preferred: Optional[str] = None,
    ) -> None:
        """Emit superevent + G event to output pad."""
        output = {
            "action": action,
            "superevent_id": superevent["superevent_id"],
            "preferred_event": graceid,
            "t_0": superevent["t_0"],
            "t_start": superevent["t_start"],
            "t_end": superevent["t_end"],
            "gw_events": list(superevent["gw_events"]),
            "g_event": {**event, "graceid": graceid},
        }
        if previous_preferred:
            output["previous_preferred"] = previous_preferred
        self._outputs[self.supers_pad_name].append(output)

    def _create_new_superevent(self, event: dict) -> None:
        """Create new G event and superevent in GraceDB."""
        gpstime = event["gpstime"]
        half = self.window_duration / 2
        t_start = gpstime - half
        t_end = gpstime + half

        self._logger.info(f"Creating new superevent for t_0={gpstime}")

        # Use GraceDBMixin methods
        graceid = self._gracedb_create_event(event)
        if not graceid:
            self._logger.error("Failed to create G event, skipping superevent creation")
            return

        superevent_id = self._gracedb_create_superevent(
            t_0=gpstime,
            t_start=t_start,
            t_end=t_end,
            preferred_event=graceid,
        )
        if not superevent_id:
            self._logger.error("Failed to create superevent")
            return

        self._superevents[gpstime] = {
            "superevent_id": superevent_id,
            "preferred_event": graceid,
            "preferred_snr": event["snr"],
            "t_0": gpstime,
            "t_start": t_start,
            "t_end": t_end,
            "gw_events": [graceid],
            "created_at": time.time(),
        }

        # Keep sorted list for bisect lookup
        bisect.insort(self._superevent_times, gpstime)

        self._emit_superevent("created", self._superevents[gpstime], event, graceid)
        self._logger.info(
            f"Created superevent {superevent_id} with preferred {graceid} "
            f"(SNR={event['snr']:.2f})"
        )

    def _update_superevent(self, t_0: float, event: dict) -> None:
        """Upload new G event and update superevent's preferred event."""
        superevent = self._superevents[t_0]

        self._logger.info(
            f"Updating superevent {superevent['superevent_id']}: "
            f"new SNR {event['snr']:.2f} > {superevent['preferred_snr']:.2f}"
        )

        # Use GraceDBMixin methods
        graceid = self._gracedb_create_event(event)
        if not graceid:
            self._logger.error("Failed to create G event, skipping superevent update")
            return

        success = self._gracedb_update_superevent(
            superevent_id=superevent["superevent_id"], preferred_event=graceid
        )
        if not success:
            self._logger.error("Failed to update superevent preferred event")
            # Event was created but superevent not updated - still track it
            superevent["gw_events"].append(graceid)
            return

        old_preferred = superevent["preferred_event"]
        superevent["preferred_event"] = graceid
        superevent["preferred_snr"] = event["snr"]
        superevent["gw_events"].append(graceid)

        self._emit_superevent("updated", superevent, event, graceid, old_preferred)

    # ─────────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────────

    def _cleanup_old_superevents(self) -> None:
        """Remove superevents older than max_event_time."""
        cutoff = time.time() - self.max_event_time

        for t_0 in list(self._superevents.keys()):
            if self._superevents[t_0]["created_at"] < cutoff:
                self._logger.info(f"Removing old superevent for t_0={t_0}")
                del self._superevents[t_0]
                self._superevent_times.remove(t_0)
