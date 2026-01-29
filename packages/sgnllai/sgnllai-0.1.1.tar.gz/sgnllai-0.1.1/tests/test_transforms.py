"""Tests for transform elements."""

import pytest
from sgn.frames import Frame

from sgnllai.transforms.gracedb_uploader import GraceDBUploader


class TestGraceDBUploader:
    """Tests for GraceDBUploader transform."""

    @pytest.fixture
    def uploader(self, mock_gracedb_patch):
        """Create a GraceDBUploader with mocked GraceDB."""
        return GraceDBUploader(
            name="test_uploader",
            gracedb_url="http://mock-gracedb/api/",
            file_data_field="fits_data",
            graceid_path="g_event.graceid",
        )

    def test_init(self, uploader):
        """Test initialization."""
        assert uploader._gracedb is not None
        assert uploader.file_data_field == "fits_data"
        assert uploader.graceid_path == "g_event.graceid"

    def test_pull_stores_frame(self, uploader):
        """Test that pull stores the frame."""
        frame = Frame(data=None, is_gap=True, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        assert uploader._current_frame is frame

    def test_internal_with_file_data(self, uploader):
        """Test processing an event with file data."""
        event = {
            "g_event": {"graceid": "G123456"},
            "fits_data": b"fake fits data",
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        # Verify write_log was called (our wrapper method)
        uploader._gracedb.write_log.assert_called_once()

        # Event should be passed through
        assert len(uploader._output_data) == 1

    def test_internal_missing_file_data(self, uploader):
        """Test processing an event without file data."""
        event = {
            "g_event": {"graceid": "G123456"},
            # No fits_data
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        # No write_log call
        uploader._gracedb.write_log.assert_not_called()

        # Event should still be passed through
        assert len(uploader._output_data) == 1

    def test_internal_missing_graceid(self, uploader):
        """Test processing an event without graceid."""
        event = {
            "fits_data": b"fake fits data",
            # No g_event.graceid
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        # No write_log call
        uploader._gracedb.write_log.assert_not_called()

        # Event should still be passed through
        assert len(uploader._output_data) == 1

    def test_internal_with_gap_frame(self, uploader):
        """Test processing a gap frame."""
        frame = Frame(data=None, is_gap=True, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        # No output data
        assert len(uploader._output_data) == 0

    def test_internal_without_pull(self, uploader):
        """Test internal() when no frame was pulled."""
        uploader.internal()

        # No output data
        assert len(uploader._output_data) == 0

    def test_internal_with_batch(self, uploader):
        """Test processing a batch of events."""
        events = [
            {"g_event": {"graceid": "G1"}, "fits_data": b"data1"},
            {"g_event": {"graceid": "G2"}, "fits_data": b"data2"},
        ]
        frame = Frame(data=events, is_gap=False, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        # Should call write_log for each event
        assert uploader._gracedb.write_log.call_count == 2

        # Both events should be passed through
        assert len(uploader._output_data) == 2

    def test_internal_single_event_dict(self, uploader):
        """Test processing a single event dict (not in a list)."""
        event = {
            "g_event": {"graceid": "G123456"},
            "fits_data": b"fake fits data",
        }
        frame = Frame(data=event, is_gap=False, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        uploader._gracedb.write_log.assert_called_once()
        assert len(uploader._output_data) == 1

    def test_new_returns_output(self, uploader):
        """Test that new() returns processed output."""
        event = {
            "g_event": {"graceid": "G123456"},
            "fits_data": b"fake fits data",
        }
        frame = Frame(data=[event], is_gap=False, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        output_frame = uploader.new(uploader.source_pads[0])
        assert output_frame.data is not None
        assert len(output_frame.data) == 1
        assert output_frame.is_gap is False

    def test_new_returns_gap_when_empty(self, uploader):
        """Test that new() returns gap frame when no output."""
        frame = Frame(data=None, is_gap=True, EOS=False)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        output_frame = uploader.new(uploader.source_pads[0])
        assert output_frame.data is None
        assert output_frame.is_gap is True

    def test_new_propagates_eos(self, uploader):
        """Test that new() propagates EOS."""
        event = {"g_event": {"graceid": "G1"}, "fits_data": b"data"}
        frame = Frame(data=[event], is_gap=False, EOS=True)
        uploader.pull(uploader.sink_pads[0], frame)
        uploader.internal()

        output_frame = uploader.new(uploader.source_pads[0])
        assert output_frame.EOS is True

    def test_new_without_pull(self, uploader):
        """Test new() when no frame was ever pulled."""
        output_frame = uploader.new(uploader.source_pads[0])
        assert output_frame.is_gap is True
        assert output_frame.EOS is False
