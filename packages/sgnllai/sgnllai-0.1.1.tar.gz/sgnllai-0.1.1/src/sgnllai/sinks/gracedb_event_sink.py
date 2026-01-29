"""GraceDBEventSink: Uploads events as standalone G events to GraceDB.

A terminal sink element that uploads raw events to GraceDB as G events
without creating superevents. Useful for delayed upload of skipped events.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from sgn.base import SinkElement, SinkPad
from sgn.frames import Frame
from sgneskig.metrics import MetricsCollectorMixin, metrics

from sgnllai.gracedb import GraceDBMixin

_logger = logging.getLogger("sgn.sgnllai.gracedb_event_sink")


@dataclass
class GraceDBEventSink(SinkElement, MetricsCollectorMixin, GraceDBMixin):
    """Terminal sink that uploads events as standalone G events to GraceDB.

    Unlike SuperEventCreator, this does NOT create superevents. Events are
    uploaded as G events only. This is a terminal sink with no output pads.

    This is useful for delayed upload of "skipped" events that were not
    immediately uploaded because a higher-SNR event was already the
    preferred event in a superevent.

    Args:
        gracedb_url: GraceDB API URL
        gracedb_group: GraceDB group (e.g., "CBC", "Test")
        gracedb_search: Search type (e.g., "AllSky")
        input_pad_name: Name of the input pad (default: "in")
        xml_field: Event dict key containing base64-encoded XML
        pipeline_field: Event dict key containing pipeline name
        metrics_enabled: Whether to collect metrics (default: True)

    Pads:
        Sink: "in" (configurable)
    """

    # Declarative metrics schema
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
                "delayed_events_uploaded",
                "counter",
                ["pipeline"],
                "Delayed G events uploaded",
                _quarter,
            ),
            (
                "delayed_createEvent_time",
                "timing",
                ["pipeline"],
                "Delayed createEvent API duration",
                _quarter_both,
            ),
            (
                "delayed_createEvent_failure",
                "counter",
                ["pipeline"],
                "Failed delayed createEvent calls",
                _quarter,
            ),
            (
                "gracedb_event_sink_elapsed",
                "timing",
                [],
                "GraceDBEventSink cycle time",
                _quarter_both,
            ),
        ]
    )

    # GraceDB settings
    gracedb_url: str = "https://gracedb-test.ligo.org/api/"
    gracedb_group: str = "CBC"
    gracedb_search: str = "AllSky"

    # Override mixin metric names for unique tracking
    event_created_metric: str = "delayed_events_uploaded"
    create_event_time_metric: str = "delayed_createEvent_time"
    create_event_failure_metric: str = "delayed_createEvent_failure"

    # Event field configuration
    xml_field: str = "xml"
    pipeline_field: str = "pipeline"

    # Pad names
    input_pad_name: str = "in"

    # Metrics settings
    metrics_enabled: bool = True
    track_elapsed_time: bool = True
    # NOTE: Must match the name in metrics_schema above for proper Grafana titles
    elapsed_metric_name: str = "gracedb_event_sink_elapsed"

    def __post_init__(self):
        # Set up pad names before super().__post_init__()
        self.sink_pad_names = [self.input_pad_name]

        super().__post_init__()
        self._logger = _logger

        # Initialize mixins
        self._init_metrics()
        self._init_gracedb()

        self._logger.info(
            f"GraceDBEventSink initialized for standalone uploads to {self.gracedb_url}"
        )

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive frame and upload events to GraceDB."""
        if frame.EOS:
            self.mark_eos(pad)

        if frame.is_gap or not frame.data:
            # Still emit metrics even for gap frames (elapsed time tracking)
            self.emit_metrics()
            return

        # Process events (handle both single dict and list)
        events = frame.data if isinstance(frame.data, list) else [frame.data]

        for event in events:
            self._upload_event(event)

        # Emit metrics (records elapsed time + writes to InfluxDB in direct mode)
        self.emit_metrics()

    def _upload_event(self, event: dict) -> None:
        """Upload a single event as a standalone G event."""
        graceid = self._gracedb_create_event(
            event,
            xml_field=self.xml_field,
            pipeline_field=self.pipeline_field,
        )

        if graceid:
            pipeline = event.get(self.pipeline_field, "unknown")
            self._logger.info(
                f"Uploaded standalone G event {graceid} from {pipeline} pipeline"
            )
        else:
            pipeline = event.get(self.pipeline_field, "unknown")
            self._logger.error(
                f"Failed to upload standalone G event from {pipeline} pipeline"
            )

    def internal(self) -> None:
        """Called each iteration - nothing to do for this sink."""
        pass
