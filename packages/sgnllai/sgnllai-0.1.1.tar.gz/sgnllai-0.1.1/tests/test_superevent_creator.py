"""Tests for SuperEventCreator transform element."""

import base64
from unittest.mock import MagicMock

import pytest
from sgn.frames import Frame

from sgnllai.transforms.superevent_creator import SuperEventCreator

# Mock XML data for test events
MOCK_XML = base64.b64encode(b"<xml>mock</xml>").decode()


class TestSuperEventCreator:
    """Tests for SuperEventCreator with mocked GraceDB."""

    @pytest.fixture
    def creator(self, mock_gracedb_patch):
        """Create a SuperEventCreator with mocked GraceDB."""
        return SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            window_duration=1.0,  # ±0.5s window
        )

    def test_init(self, creator):
        """Test initialization."""
        assert creator._gracedb is not None
        assert creator.window_duration == 1.0
        assert len(creator._superevents) == 0

    def test_find_superevent_empty(self, creator):
        """Test _find_superevent returns None when no superevents exist."""
        assert creator._find_superevent(1412546713.52) is None

    def test_find_superevent_within_window(self, creator, sample_event):
        """Test _find_superevent finds matching superevent."""
        # Create a superevent first
        frame = Frame(data=[sample_event], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # With window_duration=1.0 (±0.5s), event at 1412546713.52
        # should match anything within [1412546713.02, 1412546714.02]
        t_0 = sample_event["gpstime"]
        assert creator._find_superevent(t_0) == t_0
        assert creator._find_superevent(t_0 + 0.4) == t_0
        assert creator._find_superevent(t_0 - 0.4) == t_0

        # Outside window should return None
        assert creator._find_superevent(t_0 + 0.6) is None
        assert creator._find_superevent(t_0 - 0.6) is None

    def test_create_new_superevent(self, creator, sample_event):
        """Test creation of new superevent."""
        frame = Frame(data=[sample_event], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # Check superevent was created
        assert len(creator._superevents) == 1

        # Check outputs were set
        assert len(creator._outputs["supers"]) == 1
        assert creator._outputs["supers"][0]["action"] == "created"
        # G event info is nested in super output
        assert creator._outputs["supers"][0]["g_event"]["snr"] == 12.5

        assert len(creator._outputs["skipped"]) == 0

    def test_update_superevent_higher_snr(
        self, creator, sample_event, sample_event_higher_snr
    ):
        """Test superevent update when higher SNR event arrives."""
        # First event
        frame1 = Frame(data=[sample_event], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame1)
        creator.internal()

        first_preferred = creator._outputs["supers"][0]["preferred_event"]

        # Higher SNR event in same window
        frame2 = Frame(data=[sample_event_higher_snr], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame2)
        creator.internal()

        # Should still have only 1 superevent
        assert len(creator._superevents) == 1

        # Should have updated
        assert len(creator._outputs["supers"]) == 1
        assert creator._outputs["supers"][0]["action"] == "updated"
        assert creator._outputs["supers"][0]["previous_preferred"] == first_preferred
        # G event info is nested in super output
        assert creator._outputs["supers"][0]["g_event"]["snr"] == 15.0

    def test_no_update_lower_snr(self, creator, sample_event, sample_event_lower_snr):
        """Test no update when lower SNR event arrives."""
        # First event (SNR=12.5)
        frame1 = Frame(data=[sample_event], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame1)
        creator.internal()

        first_preferred = creator._outputs["supers"][0]["preferred_event"]

        # Lower SNR event in same window (SNR=10.0)
        frame2 = Frame(data=[sample_event_lower_snr], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame2)
        creator.internal()

        # Should still have only 1 superevent
        assert len(creator._superevents) == 1

        # Should NOT have super outputs (no update), but should have skipped output
        assert len(creator._outputs["supers"]) == 0
        assert len(creator._outputs["skipped"]) == 1
        assert creator._outputs["skipped"][0]["reason"] == "lower_snr"
        assert creator._outputs["skipped"][0]["snr"] == 10.0

        # Preferred should remain unchanged
        t_0 = list(creator._superevents.keys())[0]
        assert creator._superevents[t_0]["preferred_event"] == first_preferred

    def test_separate_superevents_different_windows(
        self, creator, sample_event, sample_event_different_window
    ):
        """Test that events in different windows create separate superevents."""
        # First event at gpstime=1412546713.52
        frame1 = Frame(data=[sample_event], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame1)
        creator.internal()

        # Second event at gpstime=1412546720.00 (different window)
        frame2 = Frame(data=[sample_event_different_window], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame2)
        creator.internal()

        # Should have 2 superevents
        assert len(creator._superevents) == 2

    def test_gap_frame_handling(self, creator):
        """Test that gap frames are handled gracefully."""
        frame = Frame(data=None, is_gap=True, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # No superevents should be created
        assert len(creator._superevents) == 0

    def test_internal_without_pull(self, creator):
        """Test that internal() returns early when no frame has been pulled."""
        # Call internal() without first calling pull()
        # This covers line 177 where _current_frame is None
        creator.internal()

        # No superevents should be created
        assert len(creator._superevents) == 0
        assert len(creator._outputs["supers"]) == 0
        assert len(creator._outputs["skipped"]) == 0

    def test_output_pads(self, creator, sample_event):
        """Test that output pads emit correct frames."""
        frame = Frame(data=[sample_event], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # Get supers pad output (superevent + g_event)
        supers_pad = creator.srcs["supers"]
        supers_frame = creator.new(supers_pad)
        assert supers_frame.is_gap is False
        assert isinstance(supers_frame.data, list)
        assert supers_frame.data[0]["action"] == "created"
        assert "g_event" in supers_frame.data[0]

        # Get skipped pad output (should be empty for first event)
        skipped_pad = creator.srcs["skipped"]
        skipped_frame = creator.new(skipped_pad)
        assert skipped_frame.is_gap is True  # No skipped events

    def test_output_pads_gap_when_no_output(self, creator):
        """Test that output pads emit gap frames when no output."""
        # Process a gap frame
        frame = Frame(data=None, is_gap=True, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        supers_pad = creator.srcs["supers"]
        supers_frame = creator.new(supers_pad)
        assert supers_frame.is_gap is True

        skipped_pad = creator.srcs["skipped"]
        skipped_frame = creator.new(skipped_pad)
        assert skipped_frame.is_gap is True

    def test_batch_processing(self, creator):
        """Test processing multiple events in a single frame."""
        events = [
            {
                "gpstime": 1412546713.52,
                "pipeline": "gstlal",
                "snr": 12.5,
                "xml": MOCK_XML,
            },
            {
                "gpstime": 1412546713.52,
                "pipeline": "pycbc",
                "snr": 15.0,
                "xml": MOCK_XML,
            },  # higher SNR
            {
                "gpstime": 1412546720.00,
                "pipeline": "spiir",
                "snr": 20.0,
                "xml": MOCK_XML,
            },  # different window
        ]

        frame = Frame(data=events, is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # Should have 2 superevents (two different windows)
        assert len(creator._superevents) == 2

        # Should have 3 super outputs (create + update + create)
        # Each super output includes nested g_event info
        assert len(creator._outputs["supers"]) == 3
        for output in creator._outputs["supers"]:
            assert "g_event" in output

        # No skipped outputs (all events either created or updated superevent)
        assert len(creator._outputs["skipped"]) == 0


class TestSuperEventCreatorIntegration:
    """Integration tests simulating MockGWEventSource scenarios."""

    @pytest.fixture
    def creator(self, mock_gracedb_patch):
        """Create a SuperEventCreator with mocked GraceDB."""
        return SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            window_duration=5.0,  # ±2.5s window (default)
        )

    def test_multiple_pipelines_same_coalescence(self, creator):
        """Test multiple pipeline triggers for the same coalescence.

        Scenario: One coalescence at GPS 1000.0 detected by 4 pipelines
        with different latencies and SNRs.

        Expected behavior:
        - First trigger creates superevent
        - Higher SNR triggers update the preferred event
        - Lower SNR triggers are skipped (emitted to skipped pad)
        - Only one superevent should exist
        """
        coalescence_gps = 1000.0

        # Simulate triggers arriving in order of pipeline latency
        triggers = [
            # (pipeline, arrival_order, snr) - SGNL arrives first
            {
                "gpstime": coalescence_gps,
                "pipeline": "SGNL",
                "snr": 24.0,
                "xml": MOCK_XML,
            },
            {
                "gpstime": coalescence_gps,
                "pipeline": "spiir",
                "snr": 23.0,
                "xml": MOCK_XML,
            },
            {
                "gpstime": coalescence_gps,
                "pipeline": "MBTA",
                "snr": 26.0,
                "xml": MOCK_XML,
            },  # highest
            {
                "gpstime": coalescence_gps,
                "pipeline": "pycbc",
                "snr": 25.0,
                "xml": MOCK_XML,
            },
        ]

        super_outputs = []
        skipped_outputs = []

        for trigger in triggers:
            frame = Frame(data=[trigger], is_gap=False, EOS=False)
            creator.pull(creator.sink_pads[0], frame)
            creator.internal()

            super_outputs.extend(creator._outputs["supers"])
            skipped_outputs.extend(creator._outputs["skipped"])

        # Should have exactly 1 superevent
        assert len(creator._superevents) == 1

        # Check final state
        t_0 = list(creator._superevents.keys())[0]
        superevent = creator._superevents[t_0]

        # Preferred should be MBTA (highest SNR=26.0)
        assert superevent["preferred_snr"] == 26.0

        # Current behavior: 2 super outputs (first + one update)
        # SGNL (first, SNR=24) -> creates superevent
        # spiir (SNR=23 < 24) -> skipped
        # MBTA (SNR=26 > 24) -> updates superevent
        # pycbc (SNR=25 < 26) -> skipped
        assert len(super_outputs) == 2

        # 2 events were skipped (spiir and pycbc)
        assert len(skipped_outputs) == 2
        assert all(s["reason"] == "lower_snr" for s in skipped_outputs)

    def test_multiple_pipelines_batch(self, creator):
        """Test multiple pipeline triggers arriving in same batch.

        This tests the new batch processing behavior where all 4 triggers
        arrive in a single frame.
        """
        coalescence_gps = 1000.0

        triggers = [
            {
                "gpstime": coalescence_gps,
                "pipeline": "SGNL",
                "snr": 24.0,
                "xml": MOCK_XML,
            },
            {
                "gpstime": coalescence_gps,
                "pipeline": "spiir",
                "snr": 23.0,
                "xml": MOCK_XML,
            },
            {
                "gpstime": coalescence_gps,
                "pipeline": "MBTA",
                "snr": 26.0,
                "xml": MOCK_XML,
            },  # highest
            {
                "gpstime": coalescence_gps,
                "pipeline": "pycbc",
                "snr": 25.0,
                "xml": MOCK_XML,
            },
        ]

        # All triggers in one batch
        frame = Frame(data=triggers, is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # Should have exactly 1 superevent
        assert len(creator._superevents) == 1

        # Preferred should be MBTA (highest SNR=26.0)
        t_0 = list(creator._superevents.keys())[0]
        assert creator._superevents[t_0]["preferred_snr"] == 26.0

        # Should have 2 super outputs (SGNL creates, MBTA updates)
        # Each includes nested g_event info
        assert len(creator._outputs["supers"]) == 2
        assert creator._outputs["supers"][0]["g_event"]["snr"] == 24.0  # SGNL
        assert creator._outputs["supers"][1]["g_event"]["snr"] == 26.0  # MBTA

        # 2 events skipped (spiir and pycbc)
        assert len(creator._outputs["skipped"]) == 2

    def test_two_coalescences_separate_superevents(self, creator):
        """Test two separate coalescences create two superevents.

        Scenario: Coalescences at GPS 1000.0 and GPS 1020.0
        Each should get its own superevent.
        """
        # First coalescence
        triggers_1 = [
            {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML},
            {"gpstime": 1000.0, "pipeline": "MBTA", "snr": 26.0, "xml": MOCK_XML},
        ]

        # Second coalescence (20 seconds later)
        triggers_2 = [
            {"gpstime": 1020.0, "pipeline": "SGNL", "snr": 35.0, "xml": MOCK_XML},
            {"gpstime": 1020.0, "pipeline": "pycbc", "snr": 38.0, "xml": MOCK_XML},
        ]

        for trigger in triggers_1 + triggers_2:
            frame = Frame(data=[trigger], is_gap=False, EOS=False)
            creator.pull(creator.sink_pads[0], frame)
            creator.internal()

        # Should have 2 superevents
        assert len(creator._superevents) == 2

        # Check each superevent has correct preferred SNR
        snrs = [se["preferred_snr"] for se in creator._superevents.values()]
        assert 26.0 in snrs  # First coalescence preferred
        assert 38.0 in snrs  # Second coalescence preferred

    def test_multiple_triggers_per_pipeline(self, creator):
        """Test multiple triggers from same pipeline (template multiplicity).

        Scenario: SGNL produces 3 triggers for one coalescence
        (different template bank matches).
        """
        coalescence_gps = 1000.0

        triggers = [
            {
                "gpstime": coalescence_gps,
                "pipeline": "SGNL",
                "snr": 24.0,
                "xml": MOCK_XML,
            },
            {
                "gpstime": coalescence_gps,
                "pipeline": "SGNL",
                "snr": 24.5,
                "xml": MOCK_XML,
            },  # same pipeline, higher
            {
                "gpstime": coalescence_gps,
                "pipeline": "SGNL",
                "snr": 23.8,
                "xml": MOCK_XML,
            },  # same pipeline, lower
        ]

        for trigger in triggers:
            frame = Frame(data=[trigger], is_gap=False, EOS=False)
            creator.pull(creator.sink_pads[0], frame)
            creator.internal()

        # Should still have 1 superevent
        assert len(creator._superevents) == 1

        # Preferred should be highest SNR (24.5)
        t_0 = list(creator._superevents.keys())[0]
        assert creator._superevents[t_0]["preferred_snr"] == 24.5

    def test_window_boundary_behavior(self, creator):
        """Test events near window boundaries.

        With window_duration=5.0 (±2.5s):
        Event at GPS 1000.0 creates window [997.5, 1002.5]
        Event at GPS 1002.0 should fall in same window (within ±2.5s)
        Event at GPS 1010.0 should create new window (outside ±2.5s)
        """
        triggers = [
            {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 20.0, "xml": MOCK_XML},
            {
                "gpstime": 1002.0,
                "pipeline": "MBTA",
                "snr": 25.0,
                "xml": MOCK_XML,
            },  # same window
            {
                "gpstime": 1010.0,
                "pipeline": "SGNL",
                "snr": 30.0,
                "xml": MOCK_XML,
            },  # new window
        ]

        for trigger in triggers:
            frame = Frame(data=[trigger], is_gap=False, EOS=False)
            creator.pull(creator.sink_pads[0], frame)
            creator.internal()

        # Should have 2 superevents
        assert len(creator._superevents) == 2

        # First superevent should have preferred SNR=25.0 (MBTA)
        # Second superevent should have preferred SNR=30.0
        snrs = sorted([se["preferred_snr"] for se in creator._superevents.values()])
        assert snrs == [25.0, 30.0]

    def test_overlapping_windows_selects_closest(self, creator):
        """Test that when windows overlap, the closest t_0 is selected.

        With window_duration=5.0 (±2.5s):
        Event at GPS 1000.0 creates window [997.5, 1002.5]
        Event at GPS 1004.0 creates window [1001.5, 1006.5]
        These windows overlap in [1001.5, 1002.5]

        An event at GPS 1002.0 should match the first superevent (closer t_0=1000.0)
        An event at GPS 1003.5 should match the second superevent (closer t_0=1004.0)
        """
        # Create first superevent at t_0=1000.0
        frame1 = Frame(
            data=[
                {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 20.0, "xml": MOCK_XML}
            ],
            is_gap=False,
            EOS=False,
        )
        creator.pull(creator.sink_pads[0], frame1)
        creator.internal()

        # Create second superevent at t_0=1004.0 (windows overlap at [1001.5, 1002.5])
        frame2 = Frame(
            data=[
                {"gpstime": 1004.0, "pipeline": "SGNL", "snr": 22.0, "xml": MOCK_XML}
            ],
            is_gap=False,
            EOS=False,
        )
        creator.pull(creator.sink_pads[0], frame2)
        creator.internal()

        assert len(creator._superevents) == 2

        # Event at 1002.0 is in overlap region, closer to t_0=1000.0
        found = creator._find_superevent(1002.0)
        assert found == 1000.0

        # Event at 1003.5 is in overlap region, closer to t_0=1004.0
        found = creator._find_superevent(1003.5)
        assert found == 1004.0

        # Event at exactly 1002.5 (equidistant) - should return one of them
        # (min() will pick the first one found which depends on iteration order)
        found = creator._find_superevent(1002.0)
        assert found in [1000.0, 1004.0]


class TestSuperEventCreatorErrorHandling:
    """Tests for error handling in SuperEventCreator.

    These tests use direct mocking of the _gracedb client methods to simulate
    failures at different points in the event processing flow.
    """

    def test_create_event_failure_skips_superevent(self, mock_gracedb_patch):
        """Test that superevent is not created if G event creation fails."""
        from sgnllai.gracedb.client import GraceDBResponse

        creator = SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            window_duration=5.0,
        )

        # Mock create_event to return failure
        creator._gracedb.create_event = MagicMock(
            return_value=GraceDBResponse(success=False, data={}, error="API error")
        )

        trigger = {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML}
        frame = Frame(data=[trigger], is_gap=False, EOS=False)

        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # Should have no superevents created
        assert len(creator._superevents) == 0
        assert len(creator._outputs["supers"]) == 0

    def test_create_superevent_failure(self, mock_gracedb_patch):
        """Test handling of superevent creation failure."""
        from sgnllai.gracedb.client import GraceDBResponse

        creator = SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            window_duration=5.0,
        )

        # create_event succeeds, but create_superevent fails
        creator._gracedb.create_event = MagicMock(
            return_value=GraceDBResponse(
                success=True, data={"graceid": "G123456"}, graceid="G123456"
            )
        )
        creator._gracedb.create_superevent = MagicMock(
            return_value=GraceDBResponse(
                success=False, data={}, error="Superevent API error"
            )
        )

        trigger = {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML}
        frame = Frame(data=[trigger], is_gap=False, EOS=False)

        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # G event was created but superevent failed - should have no superevents tracked
        assert len(creator._superevents) == 0
        assert len(creator._outputs["supers"]) == 0

    def test_update_event_failure_no_change(self, mock_gracedb_patch):
        """Test that superevent preferred is unchanged when update G event fails."""
        from sgnllai.gracedb.client import GraceDBResponse

        creator = SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            window_duration=5.0,
        )

        # First call succeeds, subsequent calls fail
        call_count = [0]

        def create_event_mock(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return GraceDBResponse(
                    success=True, data={"graceid": "G1"}, graceid="G1"
                )
            return GraceDBResponse(success=False, data={}, error="API error")

        creator._gracedb.create_event = MagicMock(side_effect=create_event_mock)
        creator._gracedb.create_superevent = MagicMock(
            return_value=GraceDBResponse(
                success=True, data={"superevent_id": "S1"}, superevent_id="S1"
            )
        )

        # First event creates superevent
        trigger1 = {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML}
        frame1 = Frame(data=[trigger1], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame1)
        creator.internal()

        assert len(creator._superevents) == 1

        # Second event (higher SNR) - G event creation fails
        trigger2 = {"gpstime": 1000.0, "pipeline": "MBTA", "snr": 30.0, "xml": MOCK_XML}
        frame2 = Frame(data=[trigger2], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame2)
        creator.internal()

        # Superevent should still exist with original preferred
        superevent = list(creator._superevents.values())[0]
        assert superevent["preferred_event"] == "G1"
        assert superevent["preferred_snr"] == 24.0

    def test_update_superevent_failure_still_tracks_event(self, mock_gracedb_patch):
        """Test that update superevent failure still tracks the G event."""
        from sgnllai.gracedb.client import GraceDBResponse

        creator = SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            window_duration=5.0,
        )

        event_counter = [0]

        def create_event_mock(**kwargs):
            event_counter[0] += 1
            return GraceDBResponse(
                success=True,
                data={"graceid": f"G{event_counter[0]}"},
                graceid=f"G{event_counter[0]}",
            )

        creator._gracedb.create_event = MagicMock(side_effect=create_event_mock)
        creator._gracedb.create_superevent = MagicMock(
            return_value=GraceDBResponse(
                success=True, data={"superevent_id": "S1"}, superevent_id="S1"
            )
        )
        # update_superevent fails
        creator._gracedb.update_superevent = MagicMock(
            return_value=GraceDBResponse(success=False, data={}, error="Update failed")
        )

        # First event creates superevent
        trigger1 = {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML}
        frame1 = Frame(data=[trigger1], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame1)
        creator.internal()

        # Second event (higher SNR) - G event created but update fails
        trigger2 = {"gpstime": 1000.0, "pipeline": "MBTA", "snr": 30.0, "xml": MOCK_XML}
        frame2 = Frame(data=[trigger2], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame2)
        creator.internal()

        # G event should still be tracked even though update failed
        superevent = list(creator._superevents.values())[0]
        assert "G2" in superevent["gw_events"]
        # But preferred should be unchanged since update failed
        assert superevent["preferred_event"] == "G1"

    def test_cleanup_old_superevents(self, mock_gracedb_patch):
        """Test that old superevents are cleaned up."""
        from sgnllai.gracedb.client import GraceDBResponse

        creator = SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            window_duration=5.0,
        )

        # Setup mock responses
        creator._gracedb.create_event = MagicMock(
            return_value=GraceDBResponse(
                success=True, data={"graceid": "G1"}, graceid="G1"
            )
        )
        creator._gracedb.create_superevent = MagicMock(
            return_value=GraceDBResponse(
                success=True, data={"superevent_id": "S1"}, superevent_id="S1"
            )
        )

        # Create a superevent
        trigger = {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML}
        frame = Frame(data=[trigger], is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        assert len(creator._superevents) == 1

        # Manually age the superevent by setting created_at to 0 (epoch)
        # This is definitely older than any cutoff (time.time() - max_event_time)
        t_0 = list(creator._superevents.keys())[0]
        creator._superevents[t_0]["created_at"] = 0

        # Verify the modification took effect
        assert creator._superevents[t_0]["created_at"] == 0

        # Call cleanup directly (internal() returns early on empty/gap frames)
        creator._cleanup_old_superevents()

        # Old superevent should be removed
        assert len(creator._superevents) == 0
        assert t_0 not in creator._superevent_times


class TestSuperEventCreatorMetrics:
    """Tests for SuperEventCreator metrics collection.

    SuperEventCreator uses sgneskig.MetricsCollectorMixin in direct mode,
    which buffers metrics internally and writes to InfluxDB via MetricsWriter.
    Tests verify metrics are collected using flush_metrics() API.
    """

    @pytest.fixture
    def creator(self, mock_gracedb_patch):
        """Create a SuperEventCreator with metrics enabled."""
        return SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            window_duration=5.0,
            metrics_enabled=True,
        )

    def test_metrics_enabled(self, creator):
        """Test that metrics collection is enabled."""
        assert creator.metrics_enabled is True
        # Direct mode (default) - no metrics pad
        pad_names = [pad.pad_name for pad in creator.source_pads]
        assert pad_names == ["supers", "skipped"]

    def test_metrics_collected_on_create(self, creator):
        """Test that metrics are collected when creating events."""
        trigger = {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML}
        frame = Frame(data=[trigger], is_gap=False, EOS=False)

        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # Flush metrics from internal buffer
        metrics = creator.flush_metrics()

        assert len(metrics) > 0
        metric_names = [m.name for m in metrics]
        # Uses preferred_events_uploaded (configured via event_created_metric)
        assert "preferred_events_uploaded" in metric_names
        assert "superevents_created" in metric_names

    def test_metrics_with_pipeline_tag(self, creator):
        """Test that preferred_events_uploaded metric has pipeline tag."""
        trigger = {"gpstime": 1000.0, "pipeline": "MBTA", "snr": 24.0, "xml": MOCK_XML}
        frame = Frame(data=[trigger], is_gap=False, EOS=False)

        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        metrics = creator.flush_metrics()

        events_created = next(
            m for m in metrics if m.name == "preferred_events_uploaded"
        )
        assert events_created.tags == {"pipeline": "MBTA"}
        assert events_created.value == 1.0

    def test_skipped_events_counter(self, creator):
        """Test events_skipped metric is recorded."""
        triggers = [
            {
                "gpstime": 1000.0,
                "pipeline": "SGNL",
                "snr": 24.0,
                "xml": MOCK_XML,
            },  # creates superevent
            {
                "gpstime": 1000.0,
                "pipeline": "spiir",
                "snr": 20.0,
                "xml": MOCK_XML,
            },  # skipped (lower SNR)
        ]

        frame = Frame(data=triggers, is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        metrics = creator.flush_metrics()

        events_skipped = next((m for m in metrics if m.name == "events_skipped"), None)
        assert events_skipped is not None
        assert events_skipped.tags == {"pipeline": "spiir"}
        assert events_skipped.value == 1.0

    def test_multiple_events_metrics(self, creator):
        """Test metrics for multiple events in batch."""
        triggers = [
            {
                "gpstime": 1000.0,
                "pipeline": "SGNL",
                "snr": 24.0,
                "xml": MOCK_XML,
            },  # creates superevent
            {
                "gpstime": 1000.0,
                "pipeline": "spiir",
                "snr": 23.0,
                "xml": MOCK_XML,
            },  # skipped
            {
                "gpstime": 1000.0,
                "pipeline": "MBTA",
                "snr": 26.0,
                "xml": MOCK_XML,
            },  # updates preferred
            {
                "gpstime": 1000.0,
                "pipeline": "pycbc",
                "snr": 25.0,
                "xml": MOCK_XML,
            },  # skipped
        ]

        frame = Frame(data=triggers, is_gap=False, EOS=False)
        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        metrics = creator.flush_metrics()
        metric_names = [m.name for m in metrics]

        # Should have counters for: preferred_events_uploaded (2),
        # superevents_created (1), superevents_updated (1), events_skipped (2)
        assert metric_names.count("preferred_events_uploaded") == 2  # SGNL and MBTA
        assert metric_names.count("superevents_created") == 1
        assert metric_names.count("superevents_updated") == 1
        assert metric_names.count("events_skipped") == 2  # spiir and pycbc

    def test_metrics_disabled(self, mock_gracedb_patch):
        """Test that metrics are not collected when disabled."""
        creator = SuperEventCreator(
            name="test_creator",
            gracedb_url="http://mock-gracedb/api/",
            metrics_enabled=False,
        )

        trigger = {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML}
        frame = Frame(data=[trigger], is_gap=False, EOS=False)

        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # Should return empty list when disabled
        metrics = creator.flush_metrics()
        assert metrics == []

    def test_metrics_cleared_after_flush(self, creator):
        """Test that metrics buffer is cleared after flushing."""
        trigger = {"gpstime": 1000.0, "pipeline": "SGNL", "snr": 24.0, "xml": MOCK_XML}
        frame = Frame(data=[trigger], is_gap=False, EOS=False)

        creator.pull(creator.sink_pads[0], frame)
        creator.internal()

        # First flush should have metrics
        metrics1 = creator.flush_metrics()
        assert len(metrics1) > 0

        # Second flush should be empty (buffer cleared)
        metrics2 = creator.flush_metrics()
        assert metrics2 == []
