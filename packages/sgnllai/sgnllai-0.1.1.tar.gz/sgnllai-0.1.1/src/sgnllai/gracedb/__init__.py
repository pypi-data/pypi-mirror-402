"""GraceDB package: Shared client, mixin, and utilities for GraceDB operations.

This package provides a DRY architecture for all GraceDB interactions:
- GraceDbClient: Enhanced client with unified interface
- GraceDBResponse: Standardized response dataclass
- GraceDBMixin: Mixin for SGN elements with integrated metrics
- get_nested: Utility for extracting nested dict values
"""

from sgnllai.gracedb.client import GraceDbClient, GraceDBResponse
from sgnllai.gracedb.mixin import GraceDBMixin
from sgnllai.gracedb.utils import get_nested

# Backward compatible alias
GraceDb = GraceDbClient

__all__ = [
    "GraceDb",
    "GraceDbClient",
    "GraceDBResponse",
    "GraceDBMixin",
    "get_nested",
]
