"""Tests for GraceDB sink elements."""

import base64
from unittest.mock import MagicMock

import pytest
from sgn.frames import Frame

from sgnllai.sinks.gracedb_event_sink import GraceDBEventSink
from sgnllai.sinks.gracedb_sink import GraceDBSink

# Mock XML data for test events
MOCK_XML = base64.b64encode(b"<xml>mock</xml>").decode()


class TestGraceDBEventSink:
    """Tests for GraceDBEventSink."""

    @pytest.fixture
    def sink(self, mock_gracedb_patch):
        """Create a GraceDBEventSink with mocked GraceDB."""
        return GraceDBEventSink(
            name="test_event_sink",
            gracedb_url="http://mock-gracedb/api/",
        )

    def test_init(self, sink):
        """Test initialization."""
        assert sink._gracedb is not None
        assert sink.gracedb_url == "http://mock-gracedb/api/"
        assert sink.input_pad_name == "in"

    def test_pull_with_event(self, sink):
        """Test processing a single event."""
        event = {
            "gpstime": 1412546713.52,
            "pipeline": "gstlal",
            "snr": 12.5,
            "xml": MOCK_XML,
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # Verify create_event was called (our wrapper method)
        sink._gracedb.create_event.assert_called_once()

    def test_pull_with_gap_frame(self, sink):
        """Test processing a gap frame."""
        frame = Frame(data=None, is_gap=True, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # No create_event call should be made
        sink._gracedb.create_event.assert_not_called()

    def test_pull_with_eos(self, sink):
        """Test EOS frame handling."""
        frame = Frame(data=None, is_gap=True, EOS=True)
        sink.pull(sink.sink_pads[0], frame)

        # EOS should be marked
        assert sink.at_eos is True

    def test_pull_with_batch(self, sink):
        """Test processing a batch of events."""
        events = [
            {
                "gpstime": 1412546713.52,
                "pipeline": "gstlal",
                "snr": 12.5,
                "xml": MOCK_XML,
            },
            {
                "gpstime": 1412546714.00,
                "pipeline": "gstlal",
                "snr": 11.0,
                "xml": MOCK_XML,
            },
        ]
        frame = Frame(data=events, is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # Should call create_event for each event
        assert sink._gracedb.create_event.call_count == 2

    def test_pull_single_event_dict(self, sink):
        """Test processing a single event dict (not in a list)."""
        event = {
            "gpstime": 1412546713.52,
            "pipeline": "gstlal",
            "snr": 12.5,
            "xml": MOCK_XML,
        }
        frame = Frame(data=event, is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # Should still call create_event
        sink._gracedb.create_event.assert_called_once()

    def test_upload_event_failure(self, sink):
        """Test handling of upload failure."""
        # Make create_event return a failure response
        failed_response = MagicMock()
        failed_response.success = False
        failed_response.error = "Network error"
        failed_response.graceid = None
        sink._gracedb.create_event.return_value = failed_response

        event = {
            "gpstime": 1412546713.52,
            "pipeline": "gstlal",
            "snr": 12.5,
            "xml": MOCK_XML,
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)

        # Should not raise - just log the error
        sink.pull(sink.sink_pads[0], frame)

    def test_internal_does_nothing(self, sink):
        """Test that internal() is a no-op."""
        sink.internal()  # Should not raise


class TestGraceDBSink:
    """Tests for GraceDBSink."""

    @pytest.fixture
    def sink(self, mock_gracedb_patch):
        """Create a GraceDBSink with mocked GraceDB."""
        return GraceDBSink(
            name="test_sink",
            gracedb_url="http://mock-gracedb/api/",
            file_data_field="fits_data",
            graceid_path="superevent_id",
            file_type="fits",
        )

    def test_init(self, sink):
        """Test initialization."""
        assert sink._gracedb is not None
        assert sink.file_data_field == "fits_data"
        assert sink.graceid_path == "superevent_id"

    def test_pull_with_file_data(self, sink):
        """Test processing an event with file data."""
        event = {
            "superevent_id": "S240101abc",
            "fits_data": b"fake fits data",
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # Verify write_log was called (our wrapper method)
        sink._gracedb.write_log.assert_called_once()

    def test_pull_missing_file_data(self, sink):
        """Test processing an event without file data."""
        event = {
            "superevent_id": "S240101abc",
            # No fits_data
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # No write_log call should be made
        sink._gracedb.write_log.assert_not_called()

    def test_pull_missing_graceid(self, sink):
        """Test processing an event without graceid."""
        event = {
            "fits_data": b"fake fits data",
            # No superevent_id
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # No write_log call should be made
        sink._gracedb.write_log.assert_not_called()

    def test_pull_with_gap_frame(self, sink):
        """Test processing a gap frame."""
        frame = Frame(data=None, is_gap=True, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # No write_log call
        sink._gracedb.write_log.assert_not_called()

    def test_pull_with_eos(self, sink):
        """Test EOS frame handling."""
        frame = Frame(data=None, is_gap=True, EOS=True)
        sink.pull(sink.sink_pads[0], frame)

        assert sink.at_eos is True

    def test_pull_with_batch(self, sink):
        """Test processing a batch of events."""
        events = [
            {"superevent_id": "S1", "fits_data": b"data1"},
            {"superevent_id": "S2", "fits_data": b"data2"},
        ]
        frame = Frame(data=events, is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # Should call write_log for each event
        assert sink._gracedb.write_log.call_count == 2

    def test_pull_single_event_dict(self, sink):
        """Test processing a single event dict (not in a list)."""
        event = {
            "superevent_id": "S240101abc",
            "fits_data": b"fake fits data",
        }
        frame = Frame(data=event, is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        sink._gracedb.write_log.assert_called_once()

    def test_nested_graceid_path(self, mock_gracedb_patch):
        """Test accessing graceid via nested path."""
        sink = GraceDBSink(
            name="test_sink",
            gracedb_url="http://mock-gracedb/api/",
            graceid_path="g_event.graceid",  # Nested path
        )
        event = {
            "g_event": {"graceid": "G123456"},
            "fits_data": b"fake fits data",
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        sink._gracedb.write_log.assert_called_once()

    def test_filename_template(self, mock_gracedb_patch):
        """Test custom filename template."""
        sink = GraceDBSink(
            name="test_sink",
            gracedb_url="http://mock-gracedb/api/",
            filename_template="skymap_{graceid}.fits.gz",
        )
        event = {
            "superevent_id": "S240101abc",
            "fits_data": b"fake fits data",
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        sink.pull(sink.sink_pads[0], frame)

        # Verify filename was templated
        call_kwargs = sink._gracedb.write_log.call_args[1]
        assert "skymap_S240101abc.fits.gz" in call_kwargs["filename"]

    def test_internal_does_nothing(self, sink):
        """Test that internal() is a no-op."""
        sink.internal()  # Should not raise
