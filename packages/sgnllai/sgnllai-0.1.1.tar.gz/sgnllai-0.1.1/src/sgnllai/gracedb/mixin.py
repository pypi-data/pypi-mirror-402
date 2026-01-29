"""GraceDBMixin: Reusable mixin for SGN elements that interact with GraceDB.

Provides shared GraceDB functionality with integrated metrics collection.
"""

from __future__ import annotations

import base64
import logging
from typing import Any, Optional

from sgnllai.gracedb.client import GraceDbClient

_logger = logging.getLogger("sgn.sgnllai.gracedb_mixin")


class GraceDBMixin:
    """Mixin providing shared GraceDB functionality for SGN elements.

    Provides:
    - _init_gracedb() - Initialize GraceDB client
    - _gracedb_create_event() - Create G event with metrics
    - _gracedb_create_superevent() - Create superevent with metrics
    - _gracedb_update_superevent() - Update superevent with metrics
    - _gracedb_write_log() - Upload file with metrics

    Requires:
    - MetricsCollectorMixin (for time_operation, increment_counter)
    - gracedb_url attribute
    - _logger attribute (optional, uses module logger if not set)

    Optional attributes (with defaults):
    - gracedb_group: str = "CBC"
    - gracedb_search: str = "AllSky"

    Usage:
        @dataclass
        class MyElement(TransformElement, MetricsCollectorMixin, GraceDBMixin):
            gracedb_url: str = "https://gracedb-test.ligo.org/api/"

            def __post_init__(self):
                super().__post_init__()
                self._init_gracedb()  # Initialize GraceDB client
    """

    # Type hints for methods provided by MetricsCollectorMixin
    # (actual implementations come from the mixin)
    time_operation: Any  # Context manager for timing operations
    increment_counter: Any  # Method to increment counter metrics

    # Default GraceDB configuration (can be overridden in subclass)
    gracedb_url: str = "https://gracedb-test.ligo.org/api/"
    gracedb_group: str = "CBC"
    gracedb_search: str = "AllSky"

    # Metric names (override in subclass for unique tracking)
    event_created_metric: str = "events_created"
    create_event_time_metric: str = "createEvent_time"
    create_event_failure_metric: str = "createEvent_failure"
    upload_time_metric: str = "gracedb_upload_time"
    upload_success_metric: str = "gracedb_upload_success"
    upload_failure_metric: str = "gracedb_upload_failure"

    def _init_gracedb(self) -> None:
        """Initialize GraceDB client. Call in __post_init__."""
        self._gracedb = GraceDbClient(self.gracedb_url)
        self._validate_gracedb_metrics()

    def _validate_gracedb_metrics(self) -> None:
        """Validate that configured metric names exist in the element's metrics_schema.

        Logs a warning for any metric name that won't have a dashboard panel.
        This helps catch typos or missing schema entries early.
        """
        # Get schema metric names (check instance-level first, then class-level)
        metrics_schema = getattr(self, "_metrics_schema", None)
        if metrics_schema is None:
            metrics_schema = getattr(self.__class__, "metrics_schema", [])

        schema_names = {m.name for m in metrics_schema}

        # Configurable metrics to validate (may not all be used by every element)
        configurable_metrics = [
            ("event_created_metric", self.event_created_metric),
            ("create_event_time_metric", self.create_event_time_metric),
            ("create_event_failure_metric", self.create_event_failure_metric),
            ("upload_time_metric", self.upload_time_metric),
            ("upload_success_metric", self.upload_success_metric),
            ("upload_failure_metric", self.upload_failure_metric),
        ]

        # Check each configured metric against the schema
        for attr_name, metric_name in configurable_metrics:
            # Skip if using the default value (not overridden)
            default_value = getattr(GraceDBMixin, attr_name, None)
            if metric_name == default_value:
                continue

            # Warn if overridden but not in schema
            if metric_name not in schema_names:
                element_name = getattr(self, "name", self.__class__.__name__)
                self._get_logger().warning(
                    f"{element_name}: Metric '{metric_name}' (from {attr_name}) "
                    f"is not in metrics_schema. It will be recorded but have no "
                    f"dashboard panel. Add it to metrics_schema or fix the name."
                )

    def _gracedb_create_event(
        self,
        event: dict,
        xml_field: str = "xml",
        pipeline_field: str = "pipeline",
    ) -> Optional[str]:
        """Create a G event in GraceDB from event dict.

        Args:
            event: Event dict containing xml and pipeline fields
            xml_field: Key for base64-encoded XML data
            pipeline_field: Key for pipeline name

        Returns:
            graceid on success, None on failure
        """
        pipeline = event.get(pipeline_field, "unknown")
        xml_data = event.get(xml_field)

        if not xml_data:
            self._get_logger().error(f"No {xml_field} field in event")
            return None

        filecontents = base64.b64decode(xml_data)

        self._get_logger().debug(
            f"Calling createEvent with group={self.gracedb_group}, "
            f"pipeline={pipeline}, search={self.gracedb_search}"
        )

        with self.time_operation(
            self.create_event_time_metric, tags={"pipeline": pipeline}
        ):
            response = self._gracedb.create_event(
                group=self.gracedb_group,
                pipeline=pipeline,
                filecontents=filecontents,
                search=self.gracedb_search,
            )

        if not response.success:
            self._get_logger().error(f"createEvent failed: {response.error}")
            self.increment_counter(
                self.create_event_failure_metric, tags={"pipeline": pipeline}
            )
            return None

        self.increment_counter(self.event_created_metric, tags={"pipeline": pipeline})
        self._get_logger().info(f"Created GraceDB event: {response.graceid}")
        return response.graceid

    def _gracedb_create_superevent(
        self,
        t_0: float,
        t_start: float,
        t_end: float,
        preferred_event: str,
    ) -> Optional[str]:
        """Create a superevent in GraceDB.

        Args:
            t_0: Central trigger time (GPS)
            t_start: Window start time (GPS)
            t_end: Window end time (GPS)
            preferred_event: Initial preferred G event ID

        Returns:
            superevent_id on success, None on failure
        """
        category = "test" if self.gracedb_group == "Test" else "production"

        with self.time_operation("createSuperevent_time"):
            response = self._gracedb.create_superevent(
                t_0=t_0,
                t_start=t_start,
                t_end=t_end,
                preferred_event=preferred_event,
                category=category,
            )

        if not response.success:
            self._get_logger().error(f"createSuperevent failed: {response.error}")
            return None

        self.increment_counter("superevents_created")
        self._get_logger().info(f"Created GraceDB superevent: {response.superevent_id}")
        return response.superevent_id

    def _gracedb_update_superevent(
        self,
        superevent_id: str,
        preferred_event: str,
    ) -> bool:
        """Update a superevent's preferred event.

        Args:
            superevent_id: Superevent to update
            preferred_event: New preferred G event ID

        Returns:
            True on success, False on failure
        """
        with self.time_operation("updateSuperevent_time"):
            response = self._gracedb.update_superevent(
                superevent_id, preferred_event=preferred_event
            )

        if not response.success:
            self._get_logger().error(f"updateSuperevent failed: {response.error}")
            return False

        self.increment_counter("superevents_updated")
        self._get_logger().info(
            f"Updated GraceDB superevent {superevent_id} preferred -> {preferred_event}"
        )
        return True

    def _gracedb_write_log(
        self,
        graceid: str,
        filecontents: bytes,
        filename: str,
        message: str,
        tag_name: str = "sky_loc",
        file_type: str = "file",
    ) -> bool:
        """Upload a file to a GraceDB event.

        Args:
            graceid: G event ID or superevent ID
            filecontents: File data as bytes
            filename: Filename for the upload
            message: Log message
            tag_name: GraceDB tag for the file
            file_type: Type label for metrics

        Returns:
            True on success, False on failure
        """
        try:
            with self.time_operation(
                self.upload_time_metric, tags={"file_type": file_type}
            ):
                response = self._gracedb.write_log(
                    graceid=graceid,
                    message=message,
                    filename=filename,
                    filecontents=filecontents,
                    tag_name=tag_name,
                )

            if not response.success:
                self.increment_counter(
                    self.upload_failure_metric, tags={"file_type": file_type}
                )
                self._get_logger().error(f"writeLog failed: {response.error}")
                return False

            self.increment_counter(
                self.upload_success_metric, tags={"file_type": file_type}
            )
            self._get_logger().info(f"Uploaded {filename} to {graceid}")
            return True

        except Exception as e:
            self.increment_counter(
                self.upload_failure_metric, tags={"file_type": file_type}
            )
            self._get_logger().error(f"Failed to upload {filename} to {graceid}: {e}")
            return False

    def _get_logger(self) -> logging.Logger:
        """Get logger, using instance _logger if available."""
        if hasattr(self, "_logger") and self._logger is not None:
            return self._logger
        return _logger
