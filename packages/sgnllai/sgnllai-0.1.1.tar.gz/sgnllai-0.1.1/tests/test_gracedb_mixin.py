"""Tests for GraceDB mixin functionality."""

import base64
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from sgneskig.metrics import MetricsCollectorMixin

from sgnllai.gracedb.client import GraceDBResponse
from sgnllai.gracedb.mixin import GraceDBMixin

# Mock XML data for tests
MOCK_XML = base64.b64encode(b"<xml>test</xml>").decode()


@dataclass
class MockElement(MetricsCollectorMixin, GraceDBMixin):
    """Mock element for testing GraceDBMixin."""

    name: str = "test_element"
    gracedb_url: str = "http://mock-gracedb/api/"
    metrics_enabled: bool = True

    def __post_init__(self):
        self._init_metrics()
        # Don't call _init_gracedb here - we'll mock it in tests


class TestGraceDBMixinCreateEvent:
    """Tests for _gracedb_create_event method."""

    @pytest.fixture
    def element(self):
        """Create mock element with mocked GraceDB client."""
        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            elem = MockElement()
            elem._gracedb = MagicMock()
            elem._logger = MagicMock()
            return elem

    def test_create_event_success(self, element):
        """Test successful event creation."""
        element._gracedb.create_event.return_value = GraceDBResponse(
            success=True,
            data={"graceid": "G123456"},
            graceid="G123456",
        )

        event = {"pipeline": "SGNL", "xml": MOCK_XML}
        graceid = element._gracedb_create_event(event)

        assert graceid == "G123456"
        element._gracedb.create_event.assert_called_once()

    def test_create_event_missing_xml(self, element):
        """Test event creation with missing XML field."""
        event = {"pipeline": "SGNL"}  # No xml field
        graceid = element._gracedb_create_event(event)

        assert graceid is None
        element._logger.error.assert_called()
        assert "No xml field" in str(element._logger.error.call_args)

    def test_create_event_failure(self, element):
        """Test event creation failure."""
        element._gracedb.create_event.return_value = GraceDBResponse(
            success=False,
            data={},
            error="API error",
        )

        event = {"pipeline": "SGNL", "xml": MOCK_XML}
        graceid = element._gracedb_create_event(event)

        assert graceid is None
        element._logger.error.assert_called()

    def test_create_event_custom_fields(self, element):
        """Test event creation with custom field names."""
        element._gracedb.create_event.return_value = GraceDBResponse(
            success=True,
            data={"graceid": "G789"},
            graceid="G789",
        )

        event = {"pipe": "custom", "data": MOCK_XML}
        graceid = element._gracedb_create_event(
            event, xml_field="data", pipeline_field="pipe"
        )

        assert graceid == "G789"

    def test_create_event_default_pipeline(self, element):
        """Test event creation with missing pipeline uses 'unknown'."""
        element._gracedb.create_event.return_value = GraceDBResponse(
            success=True,
            data={"graceid": "G999"},
            graceid="G999",
        )

        event = {"xml": MOCK_XML}  # No pipeline field
        graceid = element._gracedb_create_event(event)

        assert graceid == "G999"
        call_kwargs = element._gracedb.create_event.call_args.kwargs
        assert call_kwargs["pipeline"] == "unknown"


class TestGraceDBMixinCreateSuperevent:
    """Tests for _gracedb_create_superevent method."""

    @pytest.fixture
    def element(self):
        """Create mock element with mocked GraceDB client."""
        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            elem = MockElement()
            elem._gracedb = MagicMock()
            elem._logger = MagicMock()
            return elem

    def test_create_superevent_success(self, element):
        """Test successful superevent creation."""
        element._gracedb.create_superevent.return_value = GraceDBResponse(
            success=True,
            data={"superevent_id": "S240101abc"},
            superevent_id="S240101abc",
        )

        superevent_id = element._gracedb_create_superevent(
            t_0=1000.0,
            t_start=997.5,
            t_end=1002.5,
            preferred_event="G123456",
        )

        assert superevent_id == "S240101abc"

    def test_create_superevent_failure(self, element):
        """Test superevent creation failure."""
        element._gracedb.create_superevent.return_value = GraceDBResponse(
            success=False,
            data={},
            error="Creation failed",
        )

        superevent_id = element._gracedb_create_superevent(
            t_0=1000.0,
            t_start=997.5,
            t_end=1002.5,
            preferred_event="G123456",
        )

        assert superevent_id is None
        element._logger.error.assert_called()

    def test_create_superevent_test_category(self, element):
        """Test superevent creation with Test group uses 'test' category."""
        element.gracedb_group = "Test"
        element._gracedb.create_superevent.return_value = GraceDBResponse(
            success=True,
            data={"superevent_id": "S240101abc"},
            superevent_id="S240101abc",
        )

        element._gracedb_create_superevent(
            t_0=1000.0,
            t_start=997.5,
            t_end=1002.5,
            preferred_event="G123456",
        )

        call_kwargs = element._gracedb.create_superevent.call_args.kwargs
        assert call_kwargs["category"] == "test"


class TestGraceDBMixinUpdateSuperevent:
    """Tests for _gracedb_update_superevent method."""

    @pytest.fixture
    def element(self):
        """Create mock element with mocked GraceDB client."""
        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            elem = MockElement()
            elem._gracedb = MagicMock()
            elem._logger = MagicMock()
            return elem

    def test_update_superevent_success(self, element):
        """Test successful superevent update."""
        element._gracedb.update_superevent.return_value = GraceDBResponse(
            success=True,
            data={},
        )

        result = element._gracedb_update_superevent(
            superevent_id="S240101abc",
            preferred_event="G123457",
        )

        assert result is True

    def test_update_superevent_failure(self, element):
        """Test superevent update failure."""
        element._gracedb.update_superevent.return_value = GraceDBResponse(
            success=False,
            data={},
            error="Update failed",
        )

        result = element._gracedb_update_superevent(
            superevent_id="S240101abc",
            preferred_event="G123457",
        )

        assert result is False
        element._logger.error.assert_called()


class TestGraceDBMixinWriteLog:
    """Tests for _gracedb_write_log method."""

    @pytest.fixture
    def element(self):
        """Create mock element with mocked GraceDB client."""
        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            elem = MockElement()
            elem._gracedb = MagicMock()
            elem._logger = MagicMock()
            return elem

    def test_write_log_success(self, element):
        """Test successful file upload."""
        element._gracedb.write_log.return_value = GraceDBResponse(
            success=True,
            data={},
        )

        result = element._gracedb_write_log(
            graceid="G123456",
            filecontents=b"fits data",
            filename="skymap.fits.gz",
            message="Uploaded skymap",
        )

        assert result is True

    def test_write_log_failure(self, element):
        """Test file upload failure."""
        element._gracedb.write_log.return_value = GraceDBResponse(
            success=False,
            data={},
            error="Upload failed",
        )

        result = element._gracedb_write_log(
            graceid="G123456",
            filecontents=b"fits data",
            filename="skymap.fits.gz",
            message="Uploaded skymap",
        )

        assert result is False
        element._logger.error.assert_called()

    def test_write_log_exception(self, element):
        """Test file upload with exception."""
        element._gracedb.write_log.side_effect = Exception("Network error")

        result = element._gracedb_write_log(
            graceid="G123456",
            filecontents=b"fits data",
            filename="skymap.fits.gz",
            message="Uploaded skymap",
        )

        assert result is False
        element._logger.error.assert_called()

    def test_write_log_custom_tag(self, element):
        """Test file upload with custom tag."""
        element._gracedb.write_log.return_value = GraceDBResponse(
            success=True,
            data={},
        )

        element._gracedb_write_log(
            graceid="G123456",
            filecontents=b"data",
            filename="test.png",
            message="Uploaded image",
            tag_name="custom_tag",
            file_type="image",
        )

        call_kwargs = element._gracedb.write_log.call_args.kwargs
        assert call_kwargs["tag_name"] == "custom_tag"


class TestGraceDBMixinValidation:
    """Tests for metric validation in GraceDBMixin."""

    def test_validate_warns_on_missing_metric(self, caplog):
        """Test that validation warns when metric not in schema."""
        import logging

        caplog.set_level(logging.WARNING)

        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            # Create element with custom metric name not in schema
            @dataclass
            class ElementWithBadMetric(MetricsCollectorMixin, GraceDBMixin):
                name: str = "bad_metric_element"
                gracedb_url: str = "http://mock/api/"
                event_created_metric: str = "nonexistent_metric"

                def __post_init__(self):
                    self._init_metrics()
                    self._init_gracedb()

            ElementWithBadMetric()  # Just instantiate, don't need to keep reference
            assert "nonexistent_metric" in caplog.text
            assert "not in metrics_schema" in caplog.text

    def test_no_warning_for_default_metrics(self, caplog):
        """Test that default metric names don't trigger warning."""
        import logging

        caplog.set_level(logging.WARNING)

        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            elem = MockElement()
            elem._init_gracedb()

        # Should not have any warnings about metrics_schema
        assert "not in metrics_schema" not in caplog.text


class TestGraceDBMixinLogger:
    """Tests for logger behavior in GraceDBMixin."""

    def test_uses_instance_logger_when_set(self):
        """Test that instance _logger is used when available."""
        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            elem = MockElement()
            instance_logger = MagicMock()
            elem._logger = instance_logger

            logger = elem._get_logger()
            assert logger is instance_logger

    def test_uses_module_logger_when_no_instance(self):
        """Test that module logger is used when no instance logger."""
        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            elem = MockElement()
            # Explicitly remove _logger to test fallback
            if hasattr(elem, "_logger"):
                delattr(elem, "_logger")

            logger = elem._get_logger()
            # Should return the module-level _logger
            assert logger.name == "sgn.sgnllai.gracedb_mixin"

    def test_uses_module_logger_when_instance_is_none(self):
        """Test module logger fallback when _logger is None."""
        with patch("sgnllai.gracedb.mixin.GraceDbClient"):
            elem = MockElement()
            elem._logger = None

            logger = elem._get_logger()
            assert logger.name == "sgn.sgnllai.gracedb_mixin"
