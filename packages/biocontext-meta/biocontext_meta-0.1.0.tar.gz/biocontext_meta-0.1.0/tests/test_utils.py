from meta_mcp.utils import fix_schema


class TestFixSchema:
    """Tests for the fix_schema function."""

    def test_array_with_single_prefix_item(self):
        """Test fixing array with single prefixItem."""
        schema = {
            "type": "array",
            "prefixItems": [{"type": "string"}],
        }
        result = fix_schema(schema)
        assert "items" in result
        assert result["items"] == {"type": "string"}
        assert "prefixItems" in result  # prefixItems should still be present

    def test_array_with_multiple_prefix_items(self):
        """Test fixing array with multiple prefixItems."""
        schema = {
            "type": "array",
            "prefixItems": [
                {"type": "string"},
                {"type": "number"},
                {"type": "boolean"},
            ],
        }
        result = fix_schema(schema)
        assert "items" in result
        assert result["items"] == {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "boolean"}]}
        assert "prefixItems" in result

    def test_array_with_empty_prefix_items(self):
        """Test fixing array with empty prefixItems."""
        schema = {
            "type": "array",
            "prefixItems": [],
        }
        result = fix_schema(schema)
        assert "items" in result
        assert result["items"] == {}
        assert "prefixItems" in result

    def test_array_with_prefix_items_and_existing_items(self):
        """Test that arrays with both prefixItems and items are not modified."""
        schema = {
            "type": "array",
            "prefixItems": [{"type": "string"}],
            "items": {"type": "number"},
        }
        result = fix_schema(schema)
        assert result["items"] == {"type": "number"}  # Should remain unchanged

    def test_non_array_schema_unchanged(self):
        """Test that non-array schemas pass through unchanged."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
            },
        }
        result = fix_schema(schema)
        assert result == schema

    def test_nested_array_in_properties(self):
        """Test fixing nested arrays within object properties."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "prefixItems": [{"type": "string"}],
                },
            },
        }
        result = fix_schema(schema)
        assert "items" in result["properties"]["tags"]
        assert result["properties"]["tags"]["items"] == {"type": "string"}

    def test_deeply_nested_arrays(self):
        """Test fixing deeply nested arrays."""
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "prefixItems": [{"type": "integer"}],
                        },
                    },
                },
            },
        }
        result = fix_schema(schema)
        assert "items" in result["properties"]["nested"]["properties"]["items"]
        assert result["properties"]["nested"]["properties"]["items"]["items"] == {"type": "integer"}

    def test_array_in_list(self):
        """Test fixing arrays that appear in lists."""
        schema = {
            "allOf": [
                {
                    "type": "array",
                    "prefixItems": [{"type": "string"}],
                },
                {
                    "type": "object",
                    "properties": {
                        "values": {
                            "type": "array",
                            "prefixItems": [{"type": "number"}],
                        },
                    },
                },
            ],
        }
        result = fix_schema(schema)
        assert "items" in result["allOf"][0]
        assert result["allOf"][0]["items"] == {"type": "string"}
        assert "items" in result["allOf"][1]["properties"]["values"]
        assert result["allOf"][1]["properties"]["values"]["items"] == {"type": "number"}

    def test_non_dict_input(self):
        """Test that non-dict input returns unchanged."""
        assert fix_schema("not a dict") == "not a dict"
        assert fix_schema(123) == 123
        assert fix_schema(None) is None
        assert fix_schema([1, 2, 3]) == [1, 2, 3]

    def test_empty_dict(self):
        """Test that empty dict returns unchanged."""
        schema = {}
        result = fix_schema(schema)
        assert result == {}

    def test_array_type_without_prefix_items(self):
        """Test that array type without prefixItems is unchanged."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        result = fix_schema(schema)
        assert result == schema

    def test_complex_nested_structure(self):
        """Test fixing a complex nested structure with multiple arrays."""
        schema = {
            "type": "object",
            "properties": {
                "coordinates": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "number"},
                        {"type": "number"},
                    ],
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "prefixItems": [{"type": "string"}],
                        },
                    },
                },
            },
        }
        result = fix_schema(schema)
        assert "items" in result["properties"]["coordinates"]
        assert result["properties"]["coordinates"]["items"] == {"anyOf": [{"type": "number"}, {"type": "number"}]}
        assert "items" in result["properties"]["metadata"]["properties"]["tags"]
        assert result["properties"]["metadata"]["properties"]["tags"]["items"] == {"type": "string"}

    def test_schema_is_not_mutated(self):
        """Test that the original schema dict is not mutated."""
        import copy

        schema = {
            "type": "array",
            "prefixItems": [{"type": "string"}],
        }
        original_schema = copy.deepcopy(schema)
        result = fix_schema(schema)
        assert "items" in result
        assert "items" not in schema  # Original should not have items added
        assert schema == original_schema  # Original should remain unchanged
