"""Enhanced GraceDB client with unified interface and standardized responses.

WARNING: This uses hardcoded credentials for local Docker GraceDB instances.
In production, replace with SciTokens authentication.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Optional

from ligo.gracedb.rest import GraceDb as _GraceDb

# Hardcoded test credentials for local Docker GraceDB
_LOCAL_USERNAME = "test_user"
_LOCAL_PASSWORD = "test_password"  # noqa: S105


@dataclass
class GraceDBResponse:
    """Standardized response from GraceDB operations.

    Attributes:
        success: Whether the operation succeeded
        data: Raw response data from GraceDB
        graceid: G event ID if applicable (e.g., "G123456")
        superevent_id: Superevent ID if applicable (e.g., "S123456")
        error: Error message if operation failed
    """

    success: bool
    data: dict
    graceid: Optional[str] = None
    superevent_id: Optional[str] = None
    error: Optional[str] = None


class GraceDbClient(_GraceDb):
    """Enhanced GraceDB client with unified interface.

    Wraps ligo.gracedb.rest.GraceDb with:
    - Consistent error handling
    - Standardized response parsing via GraceDBResponse
    - Operation-specific methods with clear return types

    WARNING: Uses hardcoded credentials for local Docker development.
    """

    def __init__(self, service_url: str, **kwargs):
        # Force no auth - we'll set basic auth manually
        kwargs["force_noauth"] = True
        super().__init__(service_url, **kwargs)

        # Inject basic auth header for local dev
        creds = base64.b64encode(
            f"{_LOCAL_USERNAME}:{_LOCAL_PASSWORD}".encode()
        ).decode()
        self.headers["Authorization"] = f"Basic {creds}"

    def create_event(
        self,
        group: str,
        pipeline: str,
        filecontents: bytes,
        search: str = "AllSky",
        filename: str = "coinc.xml.gz",
    ) -> GraceDBResponse:
        """Create a G event in GraceDB.

        Args:
            group: GraceDB group (e.g., "CBC", "Test")
            pipeline: Pipeline name (e.g., "SGNL", "pycbc")
            filecontents: Event file contents (coinc.xml.gz)
            search: Search type (default: "AllSky")
            filename: Filename for the event file

        Returns:
            GraceDBResponse with graceid on success
        """
        try:
            response = self.createEvent(
                group=group,
                pipeline=pipeline,
                filename=filename,
                filecontents=filecontents,
                search=search,
            )
            result = response.json()
            graceid = result.get("graceid")
            if not graceid:
                return GraceDBResponse(
                    success=False,
                    data=result,
                    error=f"Response missing graceid: {result}",
                )
            return GraceDBResponse(success=True, data=result, graceid=graceid)
        except Exception as e:
            return GraceDBResponse(success=False, data={}, error=str(e))

    def create_superevent(
        self,
        t_0: float,
        t_start: float,
        t_end: float,
        preferred_event: str,
        category: str = "production",
    ) -> GraceDBResponse:
        """Create a superevent in GraceDB.

        Args:
            t_0: Central trigger time (GPS)
            t_start: Window start time (GPS)
            t_end: Window end time (GPS)
            preferred_event: Initial preferred G event ID
            category: "test" or "production"

        Returns:
            GraceDBResponse with superevent_id on success
        """
        try:
            response = self.createSuperevent(
                t_start=t_start,
                t_0=t_0,
                t_end=t_end,
                preferred_event=preferred_event,
                category=category,
            )
            result = response.json()
            superevent_id = result.get("superevent_id")
            if not superevent_id:
                return GraceDBResponse(
                    success=False,
                    data=result,
                    error=f"Response missing superevent_id: {result}",
                )
            return GraceDBResponse(
                success=True, data=result, superevent_id=superevent_id
            )
        except Exception as e:
            return GraceDBResponse(success=False, data={}, error=str(e))

    def update_superevent(
        self, superevent_id: str, preferred_event: str
    ) -> GraceDBResponse:
        """Update a superevent's preferred event.

        Args:
            superevent_id: Superevent to update
            preferred_event: New preferred G event ID

        Returns:
            GraceDBResponse with success status
        """
        try:
            self.updateSuperevent(superevent_id, preferred_event=preferred_event)
            return GraceDBResponse(
                success=True,
                data={"superevent_id": superevent_id},
                superevent_id=superevent_id,
            )
        except Exception as e:
            return GraceDBResponse(success=False, data={}, error=str(e))

    def write_log(
        self,
        graceid: str,
        message: str,
        filename: str,
        filecontents: bytes,
        tag_name: str = "sky_loc",
    ) -> GraceDBResponse:
        """Upload a file to a GraceDB event.

        Args:
            graceid: G event ID or superevent ID
            message: Log message describing the upload
            filename: Filename for the uploaded file
            filecontents: File data as bytes
            tag_name: GraceDB tag for the file (default: "sky_loc")

        Returns:
            GraceDBResponse with success status
        """
        try:
            self.writeLog(
                graceid,
                message=message,
                filename=filename,
                filecontents=filecontents,
                tag_name=tag_name,
            )
            return GraceDBResponse(
                success=True,
                data={"graceid": graceid, "filename": filename},
                graceid=graceid,
            )
        except Exception as e:
            return GraceDBResponse(success=False, data={}, error=str(e))
