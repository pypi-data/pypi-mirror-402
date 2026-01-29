"""GraceDBSink: Uploads files (FITS, PNG) to GraceDB events.

A sink element that uploads file data to GraceDB. This is a terminal
node in the pipeline - data flows in but not out.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from sgn.base import SinkElement, SinkPad
from sgn.frames import Frame
from sgneskig.metrics import MetricsCollectorMixin, metrics

from sgnllai.gracedb import GraceDBMixin, get_nested

_logger = logging.getLogger("sgn.sgnllai.gracedb_sink")


@dataclass
class GraceDBSink(SinkElement, MetricsCollectorMixin, GraceDBMixin):
    """Uploads files to GraceDB events.

    A proper sink element for uploading files to GraceDB. Extracts
    file data from a configurable field and uploads using writeLog.

    Since SinkElements cannot have source pads, metrics are tracked
    internally and can be queried via get_metrics().

    Pads:
    - Sink: "in" (configurable)
    """

    # Declarative metrics schema
    # NOTE: The elapsed metric name must match elapsed_metric_name below.
    metrics_schema: ClassVar = metrics(
        [
            (
                "superevent_upload_time",
                "timing",
                ["file_type"],
                "Superevent upload duration",
            ),
            (
                "superevent_upload_success",
                "counter",
                ["file_type"],
                "Successful superevent uploads",
            ),
            (
                "superevent_upload_failure",
                "counter",
                ["file_type"],
                "Failed superevent uploads",
            ),
            ("gracedb_sink_elapsed", "timing", [], "GraceDBSink cycle time"),
        ]
    )

    # GraceDB settings
    gracedb_url: str = "https://gracedb-test.ligo.org/api/"

    # Override mixin metric names for unique tracking (uploads to superevents)
    upload_time_metric: str = "superevent_upload_time"
    upload_success_metric: str = "superevent_upload_success"
    upload_failure_metric: str = "superevent_upload_failure"

    # File configuration
    file_data_field: str = "fits_data"  # Dict key containing file bytes
    filename_template: str = "{graceid}.fits"  # Filename pattern
    tag_name: str = "sky_loc"  # GraceDB tag for the file
    file_type: str = "fits"  # For metrics labeling
    message_template: str = "Uploaded {file_type} sky map"  # Log message

    # Path to graceid within event dict (dot notation)
    graceid_path: str = "superevent_id"  # Default to superevent uploads

    # Pad names
    input_pad_name: str = "in"

    # Metrics settings
    metrics_enabled: bool = True
    track_elapsed_time: bool = True
    # NOTE: Must match the name in metrics_schema above for proper Grafana titles
    elapsed_metric_name: str = "gracedb_sink_elapsed"

    def __post_init__(self):
        # Set up pad names before super().__post_init__()
        self.sink_pad_names = [self.input_pad_name]

        super().__post_init__()
        self._logger = _logger

        # Initialize metrics collection
        self._init_metrics()

        # Initialize GraceDB client (from GraceDBMixin)
        self._init_gracedb()

        self._logger.info(
            f"GraceDBSink initialized: {self.file_type} -> {self.gracedb_url}"
        )

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive frame and upload files to GraceDB."""
        if frame.EOS:
            self.mark_eos(pad)

        if frame.is_gap or not frame.data:
            # Still emit metrics even for gap frames (elapsed time tracking)
            self.emit_metrics()
            return

        # Process events (handle both single dict and list)
        events = frame.data if isinstance(frame.data, list) else [frame.data]

        for event in events:
            self._process_event(event)

        # Emit metrics (records elapsed time + writes to InfluxDB in direct mode)
        self.emit_metrics()

    def _process_event(self, event: dict) -> None:
        """Upload file for a single event."""
        # Get file data
        file_data = event.get(self.file_data_field)
        if file_data is None:
            self._logger.debug(f"No {self.file_data_field} in event, skipping upload")
            return

        # Get graceid using shared utility
        graceid = get_nested(event, self.graceid_path)
        if not graceid:
            self._logger.error(f"No graceid at path '{self.graceid_path}' in event")
            return

        # Generate filename
        filename = self.filename_template.format(graceid=graceid)

        # Format message with available fields
        message = self.message_template.format(
            file_type=self.file_type,
            filename=filename,
            graceid=graceid,
        )

        # Upload to GraceDB using mixin method
        self._gracedb_write_log(
            graceid=graceid,
            filecontents=file_data,
            filename=filename,
            message=message,
            tag_name=self.tag_name,
            file_type=self.file_type,
        )

    def internal(self) -> None:
        """Called each iteration - nothing to do for this sink."""
        pass
