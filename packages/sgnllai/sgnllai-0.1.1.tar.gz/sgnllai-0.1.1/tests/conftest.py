"""Pytest fixtures for sgnllai tests."""

import base64
from unittest.mock import MagicMock, patch

import pytest

# Mock XML data for all test events
MOCK_XML = base64.b64encode(b"<xml>mock</xml>").decode()


@pytest.fixture
def sample_event():
    """A sample GW event matching the MockGWEventSource format."""
    return {
        "gpstime": 1412546713.52,
        "pipeline": "gstlal",
        "snr": 12.5,
        "ifos": "H1,L1,V1",
        "far": 1e-10,
        "event_id": 1,
        "xml": MOCK_XML,
    }


@pytest.fixture
def sample_event_higher_snr():
    """A sample GW event with higher SNR."""
    return {
        "gpstime": 1412546713.75,
        "pipeline": "gstlal",
        "snr": 15.0,
        "ifos": "H1,L1,V1",
        "far": 1e-11,
        "event_id": 2,
        "xml": MOCK_XML,
    }


@pytest.fixture
def sample_event_lower_snr():
    """A sample GW event with lower SNR."""
    return {
        "gpstime": 1412546713.60,
        "pipeline": "gstlal",
        "snr": 10.0,
        "ifos": "H1,L1,V1",
        "far": 1e-9,
        "event_id": 3,
        "xml": MOCK_XML,
    }


@pytest.fixture
def sample_event_different_window():
    """A sample GW event in a different time window."""
    return {
        "gpstime": 1412546720.00,
        "pipeline": "gstlal",
        "snr": 11.0,
        "ifos": "H1,L1,V1",
        "far": 1e-10,
        "event_id": 4,
        "xml": MOCK_XML,
    }


@pytest.fixture
def sample_burst_event():
    """A sample burst event."""
    return {
        "gpstime": 1412546713.52,
        "pipeline": "cwb",
        "snr": 8.5,
        "ifos": "H1,L1",
        "far": 1e-8,
        "event_id": 5,
        "xml": MOCK_XML,
    }


@pytest.fixture
def mock_gracedb():
    """Mock GraceDb client that returns fake IDs."""
    mock = MagicMock()

    # Counter for generating unique IDs
    event_counter = [0]
    superevent_counter = [0]

    def create_event(**kwargs):
        event_counter[0] += 1
        response = MagicMock()
        response.json.return_value = {"graceid": f"G{event_counter[0]}"}
        return response

    def create_superevent(**kwargs):
        superevent_counter[0] += 1
        response = MagicMock()
        response.json.return_value = {"superevent_id": f"S{superevent_counter[0]}"}
        return response

    def update_superevent(*args, **kwargs):
        response = MagicMock()
        response.json.return_value = {"status": "ok"}
        return response

    def write_log_wrapper(*args, **kwargs):
        # Return a GraceDBResponse-like object
        response = MagicMock()
        response.success = True
        response.error = None
        response.data = {"status": "ok"}
        response.graceid = kwargs.get("graceid")
        return response

    def create_event_wrapper(*args, **kwargs):
        # Return a GraceDBResponse-like object
        event_counter[0] += 1
        response = MagicMock()
        response.success = True
        response.error = None
        response.graceid = f"G{event_counter[0]}"
        response.data = {"graceid": response.graceid}
        return response

    def create_superevent_wrapper(*args, **kwargs):
        # Return a GraceDBResponse-like object
        superevent_counter[0] += 1
        response = MagicMock()
        response.success = True
        response.error = None
        response.superevent_id = f"S{superevent_counter[0]}"
        response.data = {"superevent_id": response.superevent_id}
        return response

    def update_superevent_wrapper(*args, **kwargs):
        # Return a GraceDBResponse-like object
        response = MagicMock()
        response.success = True
        response.error = None
        response.data = {"status": "ok"}
        return response

    # Raw API methods (for tests that check these directly)
    mock.createEvent.side_effect = create_event
    mock.createSuperevent.side_effect = create_superevent
    mock.updateSuperevent.side_effect = update_superevent
    mock.writeLog.return_value = MagicMock()

    # Wrapper methods that return GraceDBResponse (what the mixin actually calls)
    mock.create_event.side_effect = create_event_wrapper
    mock.create_superevent.side_effect = create_superevent_wrapper
    mock.update_superevent.side_effect = update_superevent_wrapper
    mock.write_log.side_effect = write_log_wrapper

    return mock


@pytest.fixture
def mock_gracedb_patch(mock_gracedb):
    """Patch GraceDbClient to return mock client."""
    with patch("sgnllai.gracedb.mixin.GraceDbClient", return_value=mock_gracedb):
        yield mock_gracedb
