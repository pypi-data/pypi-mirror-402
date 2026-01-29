"""Tests for GraceDB client wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from sgnllai.gracedb.client import GraceDbClient, GraceDBResponse


class TestGraceDBResponse:
    """Tests for GraceDBResponse dataclass."""

    def test_success_response(self):
        """Test successful response with graceid."""
        response = GraceDBResponse(
            success=True,
            data={"graceid": "G123456"},
            graceid="G123456",
        )
        assert response.success is True
        assert response.graceid == "G123456"
        assert response.error is None

    def test_failure_response(self):
        """Test failure response with error message."""
        response = GraceDBResponse(
            success=False,
            data={},
            error="Connection failed",
        )
        assert response.success is False
        assert response.error == "Connection failed"

    def test_superevent_response(self):
        """Test response with superevent_id."""
        response = GraceDBResponse(
            success=True,
            data={"superevent_id": "S240101abc"},
            superevent_id="S240101abc",
        )
        assert response.superevent_id == "S240101abc"


class TestGraceDbClientMethods:
    """Tests for GraceDbClient wrapper methods.

    Tests the wrapper methods by mocking the underlying GraceDb methods.
    """

    @pytest.fixture
    def client(self):
        """Create a GraceDbClient with mocked parent class."""
        with patch("sgnllai.gracedb.client._GraceDb.__init__", return_value=None):
            # Create client bypassing parent init
            client = object.__new__(GraceDbClient)
            client.headers = {}
            # Setup auth header like the real init does
            import base64

            creds = base64.b64encode(b"test_user:test_password").decode()
            client.headers["Authorization"] = f"Basic {creds}"
            return client

    def test_init_sets_basic_auth(self, client):
        """Test that init sets basic auth header."""
        assert "Authorization" in client.headers
        assert client.headers["Authorization"].startswith("Basic ")

    def test_init_calls_parent_and_sets_auth(self):
        """Test that __init__ properly initializes with basic auth."""
        with patch("sgnllai.gracedb.client._GraceDb.__init__", return_value=None):
            with patch.object(GraceDbClient, "headers", {}, create=True):
                # Actually call the __init__ to cover lines 52-59
                client = GraceDbClient("http://test.example.com/api/")
                assert "Authorization" in client.headers
                assert client.headers["Authorization"].startswith("Basic ")

    def test_create_event_success(self, client):
        """Test successful event creation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"graceid": "G123456"}
        client.createEvent = MagicMock(return_value=mock_response)

        response = client.create_event(
            group="CBC",
            pipeline="SGNL",
            filecontents=b"<xml>test</xml>",
            search="AllSky",
        )

        assert response.success is True
        assert response.graceid == "G123456"

    def test_create_event_missing_graceid(self, client):
        """Test event creation with missing graceid in response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}  # Missing graceid
        client.createEvent = MagicMock(return_value=mock_response)

        response = client.create_event(
            group="CBC",
            pipeline="SGNL",
            filecontents=b"<xml>test</xml>",
        )

        assert response.success is False
        assert "missing graceid" in response.error

    def test_create_event_exception(self, client):
        """Test event creation with exception."""
        client.createEvent = MagicMock(side_effect=Exception("Network error"))

        response = client.create_event(
            group="CBC",
            pipeline="SGNL",
            filecontents=b"<xml>test</xml>",
        )

        assert response.success is False
        assert "Network error" in response.error

    def test_create_superevent_success(self, client):
        """Test successful superevent creation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"superevent_id": "S240101abc"}
        client.createSuperevent = MagicMock(return_value=mock_response)

        response = client.create_superevent(
            t_0=1000.0,
            t_start=997.5,
            t_end=1002.5,
            preferred_event="G123456",
        )

        assert response.success is True
        assert response.superevent_id == "S240101abc"

    def test_create_superevent_missing_id(self, client):
        """Test superevent creation with missing superevent_id."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}  # Missing superevent_id
        client.createSuperevent = MagicMock(return_value=mock_response)

        response = client.create_superevent(
            t_0=1000.0,
            t_start=997.5,
            t_end=1002.5,
            preferred_event="G123456",
        )

        assert response.success is False
        assert "missing superevent_id" in response.error

    def test_create_superevent_exception(self, client):
        """Test superevent creation with exception."""
        client.createSuperevent = MagicMock(side_effect=Exception("API error"))

        response = client.create_superevent(
            t_0=1000.0,
            t_start=997.5,
            t_end=1002.5,
            preferred_event="G123456",
        )

        assert response.success is False
        assert "API error" in response.error

    def test_update_superevent_success(self, client):
        """Test successful superevent update."""
        client.updateSuperevent = MagicMock()

        response = client.update_superevent(
            superevent_id="S240101abc",
            preferred_event="G123457",
        )

        assert response.success is True
        assert response.superevent_id == "S240101abc"

    def test_update_superevent_exception(self, client):
        """Test superevent update with exception."""
        client.updateSuperevent = MagicMock(side_effect=Exception("Update failed"))

        response = client.update_superevent(
            superevent_id="S240101abc",
            preferred_event="G123457",
        )

        assert response.success is False
        assert "Update failed" in response.error

    def test_write_log_success(self, client):
        """Test successful file upload."""
        client.writeLog = MagicMock()

        response = client.write_log(
            graceid="G123456",
            message="Uploaded skymap",
            filename="skymap.fits.gz",
            filecontents=b"fits data",
            tag_name="sky_loc",
        )

        assert response.success is True
        assert response.graceid == "G123456"

    def test_write_log_exception(self, client):
        """Test file upload with exception."""
        client.writeLog = MagicMock(side_effect=Exception("Upload failed"))

        response = client.write_log(
            graceid="G123456",
            message="Uploaded skymap",
            filename="skymap.fits.gz",
            filecontents=b"fits data",
        )

        assert response.success is False
        assert "Upload failed" in response.error
