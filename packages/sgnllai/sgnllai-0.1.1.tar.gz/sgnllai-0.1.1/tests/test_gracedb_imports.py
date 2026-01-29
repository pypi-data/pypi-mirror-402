"""Tests for backward-compatible imports from sgnllai.gracedb."""


def test_gracedb_exports():
    """Test that backward-compatible exports are available."""
    from sgnllai.gracedb import GraceDb, GraceDBMixin, get_nested

    # Verify the exports are the correct types
    assert GraceDb is not None
    assert GraceDBMixin is not None
    assert get_nested is not None


def test_gracedb_alias():
    """Test that GraceDb is an alias for GraceDbClient."""
    from sgnllai.gracedb import GraceDb
    from sgnllai.gracedb.client import GraceDbClient

    assert GraceDb is GraceDbClient
