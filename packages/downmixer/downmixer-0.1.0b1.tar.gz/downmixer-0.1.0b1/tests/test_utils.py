"""Unit types for the downmixer.utils module."""

from downmixer.utils import merge_dicts_with_priority


class TestMergeDictsWithPriority:
    """Tests for the merge_dicts_with_priority function."""

    def test_basic_merge(self):
        """Test basic merging of two dicts."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        result = merge_dicts_with_priority(dict1, dict2)
        assert result == {"a": 1, "b": 2, "c": 3, "d": 4}

    def test_priority_to_dict1(self):
        """Test that dict1 values take priority over dict2."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"a": 100, "c": 3}
        result = merge_dicts_with_priority(dict1, dict2)
        assert result["a"] == 1  # dict1's value wins
        assert result["b"] == 2
        assert result["c"] == 3

    def test_nested_dict_merge(self):
        """Test recursive merging of nested dicts."""
        dict1 = {"outer": {"a": 1}}
        dict2 = {"outer": {"b": 2}}
        result = merge_dicts_with_priority(dict1, dict2)
        assert result["outer"]["a"] == 1
        assert result["outer"]["b"] == 2

    def test_nested_dict_priority(self):
        """Test priority is maintained in nested dicts."""
        dict1 = {"outer": {"a": 1, "b": 2}}
        dict2 = {"outer": {"a": 100, "c": 3}}
        result = merge_dicts_with_priority(dict1, dict2)
        assert result["outer"]["a"] == 1  # dict1's nested value wins
        assert result["outer"]["b"] == 2
        assert result["outer"]["c"] == 3

    def test_deeply_nested_dicts(self):
        """Test deeply nested dict merging."""
        dict1 = {"l1": {"l2": {"l3": {"a": 1}}}}
        dict2 = {"l1": {"l2": {"l3": {"b": 2}, "extra": 3}}}
        result = merge_dicts_with_priority(dict1, dict2)
        assert result["l1"]["l2"]["l3"]["a"] == 1
        assert result["l1"]["l2"]["l3"]["b"] == 2
        assert result["l1"]["l2"]["extra"] == 3

    def test_dict2_is_none(self):
        """Test merging when dict2 is None."""
        dict1 = {"a": 1, "b": 2}
        result = merge_dicts_with_priority(dict1, None)
        assert result == {"a": 1, "b": 2}

    def test_empty_dict1(self):
        """Test merging when dict1 is empty."""
        dict1 = {}
        dict2 = {"a": 1, "b": 2}
        result = merge_dicts_with_priority(dict1, dict2)
        assert result == {"a": 1, "b": 2}

    def test_empty_dict2(self):
        """Test merging when dict2 is empty."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {}
        result = merge_dicts_with_priority(dict1, dict2)
        assert result == {"a": 1, "b": 2}

    def test_both_empty(self):
        """Test merging two empty dicts."""
        result = merge_dicts_with_priority({}, {})
        assert result == {}

    def test_original_dict_unchanged(self):
        """Test that original dicts are not modified."""
        dict1 = {"a": 1}
        dict2 = {"b": 2}
        dict1_copy = dict1.copy()
        dict2_copy = dict2.copy()

        merge_dicts_with_priority(dict1, dict2)

        assert dict1 == dict1_copy
        assert dict2 == dict2_copy

    def test_non_dict_values_not_merged(self):
        """Test that non-dict values in dict2 don't override dict1."""
        dict1 = {"a": {"nested": 1}}
        dict2 = {"a": "string_value"}
        result = merge_dicts_with_priority(dict1, dict2)
        # dict1's nested dict wins over dict2's string
        assert result["a"] == {"nested": 1}

    def test_dict1_has_non_dict_dict2_has_dict(self):
        """Test when dict1 has non-dict but dict2 has dict with same key."""
        dict1 = {"a": "string_value"}
        dict2 = {"a": {"nested": 1}}
        result = merge_dicts_with_priority(dict1, dict2)
        # dict1's value wins even if dict2 has a dict
        assert result["a"] == "string_value"

    def test_various_value_types(self):
        """Test merging with various value types."""
        dict1 = {
            "string": "hello",
            "number": 42,
            "list": [1, 2, 3],
            "bool": True,
            "none": None,
        }
        dict2 = {
            "string": "world",
            "new_number": 100,
            "list": [4, 5, 6],
            "extra": "value",
        }
        result = merge_dicts_with_priority(dict1, dict2)

        assert result["string"] == "hello"  # dict1 wins
        assert result["number"] == 42
        assert result["list"] == [1, 2, 3]  # dict1 wins, lists not merged
        assert result["bool"] is True
        assert result["none"] is None
        assert result["new_number"] == 100  # from dict2
        assert result["extra"] == "value"  # from dict2

    def test_mixed_nested_and_flat(self):
        """Test mixing nested and flat structures."""
        dict1 = {
            "flat": "value1",
            "nested": {"a": 1},
        }
        dict2 = {
            "flat": "value2",
            "nested": {"b": 2},
            "new_flat": "new_value",
        }
        result = merge_dicts_with_priority(dict1, dict2)

        assert result["flat"] == "value1"
        assert result["nested"]["a"] == 1
        assert result["nested"]["b"] == 2
        assert result["new_flat"] == "new_value"
