"""GraceDBUploader: Uploads files (FITS, PNG) to GraceDB events.

A transform element that uploads file data to GraceDB and passes through
the event for downstream processing. Configurable for different file types.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar, Optional

from sgn.base import SinkPad, SourcePad, TransformElement
from sgn.frames import Frame
from sgneskig.metrics import MetricsCollectorMixin, metrics

from sgnllai.gracedb import GraceDBMixin, get_nested

_logger = logging.getLogger("sgn.sgnllai.gracedb_uploader")


@dataclass
class GraceDBUploader(TransformElement, MetricsCollectorMixin, GraceDBMixin):
    """Uploads files to GraceDB events and passes through data.

    Configurable for different file types (FITS, PNG, etc.). Extracts
    file data from a configurable field, uploads to GraceDB using writeLog,
    and passes through the event dict for downstream processing.

    Pads:
    - Sink: "in" (configurable)
    - Sources: "out" (pass-through), "metrics"
    """

    # Declarative metrics schema
    metrics_schema: ClassVar = metrics(
        [
            ("gevent_upload_time", "timing", ["file_type"], "G-event upload duration"),
            (
                "gevent_upload_success",
                "counter",
                ["file_type"],
                "Successful G-event uploads",
            ),
            (
                "gevent_upload_failure",
                "counter",
                ["file_type"],
                "Failed G-event uploads",
            ),
        ]
    )

    # GraceDB settings
    gracedb_url: str = "https://gracedb-test.ligo.org/api/"

    # Override mixin metric names for unique tracking (uploads to G events)
    upload_time_metric: str = "gevent_upload_time"
    upload_success_metric: str = "gevent_upload_success"
    upload_failure_metric: str = "gevent_upload_failure"

    # File configuration
    file_data_field: str = "fits_data"  # Dict key containing file bytes
    filename_template: str = "{graceid}.fits"  # Filename pattern
    tag_name: str = "sky_loc"  # GraceDB tag for the file
    file_type: str = "fits"  # For metrics labeling

    # Path to graceid within event dict (dot notation)
    graceid_path: str = "g_event.graceid"

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

        # Initialize GraceDB client (from GraceDBMixin)
        self._init_gracedb()

        # Current state
        self._current_frame: Optional[Frame] = None
        self._output_data: list[dict] = []

        self._logger.info(
            f"GraceDBUploader initialized: {self.file_type} -> {self.gracedb_url}"
        )

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive frame from upstream."""
        self._current_frame = frame

    def internal(self) -> None:
        """Upload files from frame data to GraceDB."""
        self._output_data = []
        frame = self._current_frame

        if frame is None or frame.is_gap or not frame.data:
            return

        # Process events (handle both single dict and list)
        events = frame.data if isinstance(frame.data, list) else [frame.data]

        for event in events:
            self._process_event(event)

    def _process_event(self, event: dict) -> None:
        """Upload file for a single event."""
        # Get file data
        file_data = event.get(self.file_data_field)
        if file_data is None:
            self._logger.warning(f"No {self.file_data_field} in event, skipping upload")
            self._output_data.append(event)
            return

        # Get graceid using shared utility
        graceid = get_nested(event, self.graceid_path)
        if not graceid:
            self._logger.error(f"No graceid at path '{self.graceid_path}' in event")
            self._output_data.append(event)
            return

        # Generate filename
        filename = self.filename_template.format(graceid=graceid)

        # Upload to GraceDB using mixin method
        self._gracedb_write_log(
            graceid=graceid,
            filecontents=file_data,
            filename=filename,
            message=f"Uploaded {self.file_type} sky map",
            tag_name=self.tag_name,
            file_type=self.file_type,
        )

        # Pass through event (with or without successful upload)
        self._output_data.append(event)

    def new(self, pad: SourcePad) -> Frame:
        """Return output frame for the requested pad."""
        eos = self._current_frame.EOS if self._current_frame else False

        # Pass through data
        return Frame(
            data=self._output_data if self._output_data else None,
            is_gap=not self._output_data,
            EOS=eos,
        )
