"""Tests for GraceDB utility functions."""

from sgnllai.gracedb.utils import get_nested


class TestGetNested:
    """Tests for get_nested utility function."""

    def test_simple_path(self):
        """Test simple single-level path."""
        data = {"a": 1}
        assert get_nested(data, "a") == 1

    def test_nested_path(self):
        """Test nested dot-notation path."""
        data = {"a": {"b": 2}}
        assert get_nested(data, "a.b") == 2

    def test_deeply_nested_path(self):
        """Test deeply nested path."""
        data = {"a": {"b": {"c": {"d": 3}}}}
        assert get_nested(data, "a.b.c.d") == 3

    def test_missing_key(self):
        """Test missing key returns None."""
        data = {"a": 1}
        assert get_nested(data, "b") is None

    def test_missing_nested_key(self):
        """Test missing nested key returns None."""
        data = {"a": {"b": 1}}
        assert get_nested(data, "a.c") is None

    def test_partial_path(self):
        """Test partial path with missing deeper key returns None."""
        data = {"a": {"b": 1}}
        assert get_nested(data, "a.b.c") is None

    def test_non_dict_intermediate(self):
        """Test non-dict intermediate value returns None."""
        data = {"a": "string_value"}
        assert get_nested(data, "a.b") is None

    def test_none_value(self):
        """Test key with None value returns None."""
        data = {"a": None}
        assert get_nested(data, "a") is None
        assert get_nested(data, "a.b") is None

    def test_empty_dict(self):
        """Test empty dict returns None for any path."""
        data = {}
        assert get_nested(data, "a") is None
        assert get_nested(data, "a.b.c") is None

    def test_list_value(self):
        """Test path ending at a list value returns the list."""
        data = {"a": [1, 2, 3]}
        assert get_nested(data, "a") == [1, 2, 3]

    def test_list_intermediate_returns_none(self):
        """Test list as intermediate value returns None."""
        data = {"a": [{"b": 1}]}
        assert get_nested(data, "a.b") is None

    def test_zero_value(self):
        """Test zero value is returned correctly (not None)."""
        data = {"a": {"b": 0}}
        assert get_nested(data, "a.b") == 0

    def test_false_value(self):
        """Test False value is returned correctly (not None)."""
        data = {"a": {"b": False}}
        assert get_nested(data, "a.b") is False

    def test_empty_string_value(self):
        """Test empty string is returned correctly (not None)."""
        data = {"a": {"b": ""}}
        assert get_nested(data, "a.b") == ""

    def test_practical_gracedb_example(self):
        """Test with realistic GraceDB-like data structure."""
        superevent = {
            "superevent_id": "S240101abc",
            "g_event": {
                "graceid": "G123456",
                "pipeline": "SGNL",
                "extra_attributes": {
                    "snr": 12.5,
                },
            },
        }
        assert get_nested(superevent, "g_event.graceid") == "G123456"
        assert get_nested(superevent, "g_event.extra_attributes.snr") == 12.5
        assert get_nested(superevent, "g_event.missing") is None
