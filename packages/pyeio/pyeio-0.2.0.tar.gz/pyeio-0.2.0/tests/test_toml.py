from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, Field
from toml import TomlDecodeError

from pyeio.toml._toml import (
    parse,
    read,
    serialize,
    serialize_native,
    serialize_pydantic,
    write,
    write_native,
    write_pydantic,
)


class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    id: int
    data: SimpleModel
    tags: list[str] = Field(default_factory=list)


class ModelWithAlias(BaseModel):
    field_name: str = Field(alias="fieldName")

    model_config = {"populate_by_name": True}


class ModelWithOptional(BaseModel):
    required: str
    optional: str | None = None
    with_default: str = "default_value"


class ModelWithDatetime(BaseModel):
    created_at: datetime
    date_only: date | None = None


@pytest.fixture
def simple_dict() -> dict[str, Any]:
    return {"name": "test", "value": 42, "nested": {"a": 1, "b": 2}}


@pytest.fixture
def simple_toml_str() -> str:
    return 'name = "test"\nvalue = 42\n\n[nested]\na = 1\nb = 2\n'


@pytest.fixture
def simple_model() -> SimpleModel:
    return SimpleModel(name="test", value=42)


@pytest.fixture
def nested_model() -> NestedModel:
    return NestedModel(
        id=1,
        data=SimpleModel(name="nested", value=100),
        tags=["tag1", "tag2"],
    )


@pytest.fixture
def model_with_optional() -> ModelWithOptional:
    return ModelWithOptional(required="required_value")


@pytest.fixture
def temp_toml_file(tmp_path: Path) -> Path:
    return tmp_path / "test.toml"


@pytest.fixture
def existing_toml_file(tmp_path: Path) -> Path:
    file = tmp_path / "existing.toml"
    file.write_text("existing = true\n")
    return file


class TestParse:
    def test_parse_dict_from_string(self):
        """Test parsing a dictionary from TOML string."""
        data = 'name = "test"\nvalue = 42'
        result = parse(data)
        assert result == {"name": "test", "value": 42}

    def test_parse_dict_from_bytes(self):
        """Test parsing a dictionary from TOML bytes."""
        data = b'name = "test"\nvalue = 42'
        result = parse(data)
        assert result == {"name": "test", "value": 42}

    def test_parse_nested_table(self):
        """Test parsing nested TOML tables."""
        data = '[section]\nkey = "value"\n\n[section.subsection]\ninner = 1'
        result = parse(data)
        assert result == {
            "section": {
                "key": "value",
                "subsection": {"inner": 1},
            }
        }

    def test_parse_array(self):
        """Test parsing TOML arrays."""
        data = "items = [1, 2, 3, 4, 5]"
        result = parse(data)
        assert result == {"items": [1, 2, 3, 4, 5]}

    def test_parse_array_of_tables(self):
        """Test parsing array of tables."""
        data = '[[items]]\nname = "first"\n\n[[items]]\nname = "second"'
        result = parse(data)
        assert result == {"items": [{"name": "first"}, {"name": "second"}]}

    def test_parse_primitive_types(self):
        """Test parsing primitive TOML types."""
        data = """
string = "hello"
integer = 42
float_val = 3.14
boolean = true
"""
        result = parse(data)
        assert result["string"] == "hello"
        assert result["integer"] == 42
        assert result["float_val"] == 3.14
        assert result["boolean"] is True

    def test_parse_datetime(self):
        """Test parsing datetime values."""
        data = "timestamp = 2024-01-15T12:30:00Z"
        result = parse(data)
        assert "timestamp" in result
        assert isinstance(result["timestamp"], datetime)

    def test_parse_date(self):
        """Test parsing date values."""
        data = "date_val = 2024-01-15"
        result = parse(data)
        assert "date_val" in result

    def test_parse_time(self):
        """Test parsing time values."""
        data = "time_val = 12:30:00"
        result = parse(data)
        assert "time_val" in result

    def test_parse_with_pydantic_model(self):
        """Test parsing TOML into a Pydantic model."""
        data = 'name = "test"\nvalue = 42'
        result = parse(data, SimpleModel)
        assert isinstance(result, SimpleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_parse_nested_pydantic_model(self):
        """Test parsing TOML into a nested Pydantic model."""
        data = """
id = 1
tags = ["a", "b"]

[data]
name = "nested"
value = 100
"""
        result = parse(data, NestedModel)
        assert isinstance(result, NestedModel)
        assert result.id == 1
        assert result.data.name == "nested"
        assert result.tags == ["a", "b"]

    def test_parse_pydantic_with_strict_mode(self):
        """Test parsing with strict validation mode."""
        data = 'name = "test"\nvalue = 42'
        result = parse(data, SimpleModel, strict=True)
        assert isinstance(result, SimpleModel)

    def test_parse_pydantic_with_context(self):
        """Test parsing with validation context."""
        data = 'name = "test"\nvalue = 42'
        result = parse(data, SimpleModel, context={"extra": "data"})
        assert isinstance(result, SimpleModel)

    def test_parse_pydantic_by_alias(self):
        """Test parsing with by_alias option."""
        data = 'fieldName = "test"'
        result = parse(data, ModelWithAlias, by_alias=True)
        assert result.field_name == "test"

    def test_parse_pydantic_by_name(self):
        """Test parsing with by_name option."""
        data = 'field_name = "test"'
        result = parse(data, ModelWithAlias, by_name=True)
        assert result.field_name == "test"

    def test_parse_invalid_toml_raises_error(self):
        """Test that invalid TOML raises TomlDecodeError."""
        with pytest.raises(TomlDecodeError):
            parse("invalid = = toml")

    def test_parse_pydantic_validation_error(self):
        """Test that invalid data raises validation error."""
        from pydantic import ValidationError

        data = 'name = "test"'  # missing 'value'
        with pytest.raises(ValidationError):
            parse(data, SimpleModel)

    def test_parse_invalid_type_raises_error(self):
        """Test that invalid input type raises TypeError."""
        with pytest.raises(TypeError):
            parse(123)  # type: ignore


class TestRead:
    def test_read_dict(self, tmp_path: Path):
        """Test reading a dictionary from TOML file."""
        file = tmp_path / "test.toml"
        file.write_text('name = "test"\nvalue = 42')

        result = read(file)
        assert result == {"name": "test", "value": 42}

    def test_read_with_string_path(self, tmp_path: Path):
        """Test reading with string path."""
        file = tmp_path / "test.toml"
        file.write_text('key = "value"')

        result = read(str(file))
        assert result == {"key": "value"}

    def test_read_nested_tables(self, tmp_path: Path):
        """Test reading nested TOML tables."""
        file = tmp_path / "test.toml"
        file.write_text('[section]\nkey = "value"')

        result = read(file)
        assert result == {"section": {"key": "value"}}

    def test_read_with_pydantic_model(self, tmp_path: Path):
        """Test reading TOML into a Pydantic model."""
        file = tmp_path / "test.toml"
        file.write_text('name = "test"\nvalue = 42')

        result = read(file, SimpleModel)
        assert isinstance(result, SimpleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_read_nested_pydantic_model(self, tmp_path: Path):
        """Test reading TOML into a nested Pydantic model."""
        file = tmp_path / "test.toml"
        file.write_text('id = 1\ntags = []\n\n[data]\nname = "nested"\nvalue = 100')

        result = read(file, NestedModel)
        assert isinstance(result, NestedModel)
        assert result.id == 1

    def test_read_with_strict_mode(self, tmp_path: Path):
        """Test reading with strict validation mode."""
        file = tmp_path / "test.toml"
        file.write_text('name = "test"\nvalue = 42')

        result = read(file, SimpleModel, strict=True)
        assert isinstance(result, SimpleModel)

    def test_read_with_context(self, tmp_path: Path):
        """Test reading with validation context."""
        file = tmp_path / "test.toml"
        file.write_text('name = "test"\nvalue = 42')

        result = read(file, SimpleModel, context={"key": "value"})
        assert isinstance(result, SimpleModel)

    def test_read_nonexistent_file_raises_error(self, tmp_path: Path):
        """Test that reading non-existent file raises error."""
        file = tmp_path / "nonexistent.toml"
        with pytest.raises(FileNotFoundError):
            read(file)

    def test_read_invalid_toml_raises_error(self, tmp_path: Path):
        """Test that invalid TOML raises TomlDecodeError."""
        file = tmp_path / "test.toml"
        file.write_text("invalid = = syntax")

        with pytest.raises(TomlDecodeError):
            read(file)


# ============================================================================
# Tests for serialize_native
# ============================================================================


class TestSerializeNative:
    def test_serialize_dict_to_bytes(self, simple_dict: dict):
        """Test serializing dict to bytes (default)."""
        result = serialize_native(simple_dict)
        assert isinstance(result, bytes)
        assert b"name" in result
        assert b"test" in result

    def test_serialize_dict_to_str(self, simple_dict: dict):
        """Test serializing dict to string."""
        result = serialize_native(simple_dict, returns=str)
        assert isinstance(result, str)
        assert "name" in result
        assert "test" in result

    def test_serialize_nested_dict(self):
        """Test serializing nested dictionary."""
        data = {"section": {"key": "value", "number": 42}}
        result = serialize_native(data, returns=str)
        assert "[section]" in result
        assert 'key = "value"' in result

    def test_serialize_with_arrays(self):
        """Test serializing with arrays."""
        data = {"items": [1, 2, 3], "strings": ["a", "b", "c"]}
        result = serialize_native(data, returns=str)
        assert "items = [ 1, 2, 3,]\n" in result

    def test_serialize_primitive_types(self):
        """Test serializing primitive types."""
        data = {
            "string": "hello",
            "integer": 42,
            "float_val": 3.14,
            "boolean": True,
        }
        result = serialize_native(data, returns=str)
        assert 'string = "hello"' in result
        assert "integer = 42" in result
        assert "boolean = true" in result

    def test_serialize_with_custom_encoding(self, simple_dict: dict):
        """Test serializing with custom encoding."""
        result = serialize_native(simple_dict, returns=bytes, encoding="utf-8")
        assert isinstance(result, bytes)

    def test_serialize_invalid_returns_type_raises_error(self, simple_dict: dict):
        """Test that invalid returns type raises TypeError."""
        with pytest.raises(TypeError):
            serialize_native(simple_dict, returns=list)  # type: ignore

    def test_serialize_roundtrip(self, simple_dict: dict):
        """Test that serialized data can be parsed back."""
        serialized = serialize_native(simple_dict, returns=str)
        parsed = parse(serialized)
        assert parsed == simple_dict


# ============================================================================
# Tests for serialize_pydantic
# ============================================================================


class TestSerializePydantic:
    def test_serialize_to_bytes(self, simple_model: SimpleModel):
        """Test serializing Pydantic model to bytes (default)."""
        result = serialize_pydantic(simple_model)
        assert isinstance(result, bytes)
        assert b"name" in result
        assert b"test" in result

    def test_serialize_to_str(self, simple_model: SimpleModel):
        """Test serializing Pydantic model to string."""
        result = serialize_pydantic(simple_model, returns=str)
        assert isinstance(result, str)
        assert "name" in result
        assert "value = 42" in result

    def test_serialize_nested_model(self, nested_model: NestedModel):
        """Test serializing nested Pydantic model."""
        result = serialize_pydantic(nested_model, returns=str)
        assert "id = 1" in result
        assert "[data]" in result
        assert 'name = "nested"' in result

    def test_serialize_with_include(self, nested_model: NestedModel):
        """Test serializing with field inclusion."""
        result = serialize_pydantic(nested_model, returns=str, include={"id"})
        assert "id = 1" in result
        assert "[data]" not in result
        assert "tags" not in result

    def test_serialize_with_exclude(self, nested_model: NestedModel):
        """Test serializing with field exclusion."""
        result = serialize_pydantic(nested_model, returns=str, exclude={"tags"})
        assert "id = 1" in result
        assert "[data]" in result
        assert "tags" not in result

    def test_serialize_exclude_unset(self, model_with_optional: ModelWithOptional):
        """Test serializing with exclude_unset."""
        result = serialize_pydantic(
            model_with_optional, returns=str, exclude_unset=True
        )
        assert "required" in result
        # optional and with_default were not explicitly set
        assert "optional" not in result
        assert "with_default" not in result

    def test_serialize_exclude_defaults(self, model_with_optional: ModelWithOptional):
        """Test serializing with exclude_defaults."""
        result = serialize_pydantic(
            model_with_optional, returns=str, exclude_defaults=True
        )
        assert "required" in result
        assert "with_default" not in result

    def test_serialize_by_alias(self):
        """Test serializing with field aliases."""
        model = ModelWithAlias(fieldName="test")
        result = serialize_pydantic(model, returns=str, by_alias=True)
        assert "fieldName" in result
        assert "field_name" not in result

    def test_serialize_with_custom_encoding(self, simple_model: SimpleModel):
        """Test serializing with custom encoding."""
        result = serialize_pydantic(simple_model, returns=bytes, encoding="utf-8")
        assert isinstance(result, bytes)

    def test_serialize_invalid_returns_type_raises_error(
        self, simple_model: SimpleModel
    ):
        """Test that invalid returns type raises TypeError."""
        with pytest.raises(TypeError):
            serialize_pydantic(simple_model, returns=list)  # type: ignore

    def test_serialize_roundtrip(self, simple_model: SimpleModel):
        """Test that serialized model can be parsed back."""
        serialized = serialize_pydantic(simple_model, returns=str)
        parsed = parse(serialized, SimpleModel)
        assert parsed == simple_model


class TestSerialize:
    def test_serialize_dict_routes_to_native(self, simple_dict: dict):
        """Test that dict is serialized via native serializer."""
        result = serialize(simple_dict, bytes)
        assert isinstance(result, bytes)
        assert b"name" in result

    def test_serialize_pydantic_routes_to_pydantic(self, simple_model: SimpleModel):
        """Test that Pydantic model is serialized via pydantic serializer."""
        result = serialize(simple_model, bytes)
        assert isinstance(result, bytes)
        assert b"name" in result
        assert b"value" in result

    def test_serialize_with_returns_str(self, simple_dict: dict):
        """Test serializing to string."""
        result = serialize(simple_dict, returns=str)
        assert isinstance(result, str)

    def test_serialize_passes_kwargs_to_pydantic(self, nested_model: NestedModel):
        """Test that kwargs are passed to pydantic serializer."""
        result = serialize(nested_model, returns=str, exclude={"tags"})
        assert "tags" not in result


class TestWriteNative:
    def test_write_dict(self, temp_toml_file: Path, simple_dict: dict):
        """Test writing dict to file."""
        write_native(temp_toml_file, simple_dict)
        assert temp_toml_file.exists()
        content = temp_toml_file.read_text()
        assert "name" in content
        assert "test" in content

    def test_write_with_string_path(self, temp_toml_file: Path, simple_dict: dict):
        """Test writing with string path."""
        write_native(str(temp_toml_file), simple_dict)
        assert temp_toml_file.exists()

    def test_write_nested_dict(self, temp_toml_file: Path):
        """Test writing nested dictionary."""
        data = {"section": {"key": "value"}}
        write_native(temp_toml_file, data)
        content = temp_toml_file.read_text()
        assert "[section]" in content

    def test_write_overwrite_false_raises_on_existing(self, existing_toml_file: Path):
        """Test that overwrite=False raises error for existing file."""
        with pytest.raises(FileExistsError):
            write_native(existing_toml_file, {"new": "data"}, overwrite=False)

    def test_write_overwrite_true_replaces_existing(self, existing_toml_file: Path):
        """Test that overwrite=True replaces existing file."""
        write_native(existing_toml_file, {"new": "data"}, overwrite=True)
        content = existing_toml_file.read_text()
        assert "new" in content
        assert "existing" not in content

    def test_write_roundtrip(self, temp_toml_file: Path, simple_dict: dict):
        """Test that written file can be read back."""
        write_native(temp_toml_file, simple_dict)
        result = read(temp_toml_file)
        assert result == simple_dict


class TestWritePydantic:
    def test_write_simple_model(self, temp_toml_file: Path, simple_model: SimpleModel):
        """Test writing simple Pydantic model."""
        write_pydantic(temp_toml_file, simple_model, overwrite=False)
        assert temp_toml_file.exists()
        content = temp_toml_file.read_text()
        assert "name" in content
        assert "value = 42" in content

    def test_write_nested_model(self, temp_toml_file: Path, nested_model: NestedModel):
        """Test writing nested Pydantic model."""
        write_pydantic(temp_toml_file, nested_model, overwrite=False)
        content = temp_toml_file.read_text()
        assert "id = 1" in content
        assert "[data]" in content

    def test_write_with_include(self, temp_toml_file: Path, nested_model: NestedModel):
        """Test writing with field inclusion."""
        write_pydantic(temp_toml_file, nested_model, overwrite=False, include={"id"})
        content = temp_toml_file.read_text()
        assert "id = 1" in content
        assert "[data]" not in content

    def test_write_with_exclude(self, temp_toml_file: Path, nested_model: NestedModel):
        """Test writing with field exclusion."""
        write_pydantic(temp_toml_file, nested_model, overwrite=False, exclude={"tags"})
        content = temp_toml_file.read_text()
        assert "tags" not in content

    def test_write_exclude_unset(
        self, temp_toml_file: Path, model_with_optional: ModelWithOptional
    ):
        """Test writing with exclude_unset."""
        write_pydantic(
            temp_toml_file, model_with_optional, overwrite=False, exclude_unset=True
        )
        content = temp_toml_file.read_text()
        assert "required" in content
        assert "optional" not in content
        assert "with_default" not in content

    def test_write_exclude_defaults(
        self, temp_toml_file: Path, model_with_optional: ModelWithOptional
    ):
        """Test writing with exclude_defaults."""
        write_pydantic(
            temp_toml_file, model_with_optional, overwrite=False, exclude_defaults=True
        )
        content = temp_toml_file.read_text()
        assert "required" in content
        assert "with_default" not in content

    def test_write_by_alias(self, temp_toml_file: Path):
        """Test writing with field aliases."""
        model = ModelWithAlias(fieldName="test")
        write_pydantic(temp_toml_file, model, overwrite=False, by_alias=True)
        content = temp_toml_file.read_text()
        assert "fieldName" in content

    def test_write_overwrite_false_raises_on_existing(
        self, existing_toml_file: Path, simple_model: SimpleModel
    ):
        """Test that overwrite=False raises error for existing file."""
        with pytest.raises(FileExistsError):
            write_pydantic(existing_toml_file, simple_model, overwrite=False)

    def test_write_overwrite_true_replaces_existing(
        self, existing_toml_file: Path, simple_model: SimpleModel
    ):
        """Test that overwrite=True replaces existing file."""
        write_pydantic(existing_toml_file, simple_model, overwrite=True)
        content = existing_toml_file.read_text()
        assert "name" in content
        assert "existing" not in content

    def test_write_roundtrip(self, temp_toml_file: Path, simple_model: SimpleModel):
        """Test that written model can be read back."""
        write_pydantic(temp_toml_file, simple_model, overwrite=False)
        result = read(temp_toml_file, SimpleModel)
        assert result == simple_model


class TestWrite:
    def test_write_dict_routes_to_native(self, temp_toml_file: Path, simple_dict: dict):
        """Test that dict is written via native writer."""
        write(temp_toml_file, simple_dict)
        assert temp_toml_file.exists()
        content = temp_toml_file.read_text()
        assert "name" in content

    def test_write_pydantic_routes_to_pydantic(
        self, temp_toml_file: Path, simple_model: SimpleModel
    ):
        """Test that Pydantic model is written via pydantic writer."""
        write(temp_toml_file, simple_model)
        assert temp_toml_file.exists()
        content = temp_toml_file.read_text()
        assert "name" in content
        assert "value = 42" in content

    def test_write_with_overwrite(self, existing_toml_file: Path, simple_dict: dict):
        """Test writing with overwrite flag."""
        write(existing_toml_file, simple_dict, overwrite=True)
        content = existing_toml_file.read_text()
        assert "name" in content

    def test_write_passes_kwargs_to_pydantic(
        self, temp_toml_file: Path, nested_model: NestedModel
    ):
        """Test that kwargs are passed to pydantic writer."""
        write(temp_toml_file, nested_model, exclude={"tags"})
        content = temp_toml_file.read_text()
        assert "tags" not in content

    def test_write_roundtrip_dict(self, temp_toml_file: Path, simple_dict: dict):
        """Test dict write/read roundtrip."""
        write(temp_toml_file, simple_dict)
        result = read(temp_toml_file)
        assert result == simple_dict

    def test_write_roundtrip_pydantic(
        self, temp_toml_file: Path, simple_model: SimpleModel
    ):
        """Test Pydantic model write/read roundtrip."""
        write(temp_toml_file, simple_model)
        result = read(temp_toml_file, SimpleModel)
        assert result == simple_model


class TestEdgeCases:
    def test_empty_dict(self, temp_toml_file: Path):
        """Test handling of empty dictionary."""
        data: dict[str, Any] = {}
        write_native(temp_toml_file, data)
        result = read(temp_toml_file)
        assert result == {}

    def test_unicode_content(self, temp_toml_file: Path):
        """Test handling of unicode content."""
        data = {"message": "Hello, 世界! 🌍"}
        write_native(temp_toml_file, data)
        result = read(temp_toml_file)
        assert result["message"] == "Hello, 世界! 🌍"

    def test_multiline_strings(self, tmp_path: Path):
        """Test parsing multiline strings."""
        file = tmp_path / "test.toml"
        file.write_text('text = """\nLine 1\nLine 2\nLine 3"""')
        result = read(file)
        assert "Line 1" in result["text"]
        assert "Line 2" in result["text"]

    def test_literal_strings(self, tmp_path: Path):
        """Test parsing literal strings."""
        file = tmp_path / "test.toml"
        file.write_text("path = 'C:\\Users\\test'")
        result = read(file)
        assert result["path"] == "C:\\Users\\test"

    def test_inline_tables(self, tmp_path: Path):
        """Test parsing inline tables."""
        file = tmp_path / "test.toml"
        file.write_text("point = { x = 1, y = 2 }")
        result = read(file)
        assert result["point"] == {"x": 1, "y": 2}

    def test_deeply_nested_structure(self, temp_toml_file: Path):
        """Test deeply nested structure."""
        data = {"level1": {"level2": {"level3": {"value": "deep"}}}}
        write_native(temp_toml_file, data)
        result = read(temp_toml_file)
        assert result["level1"]["level2"]["level3"]["value"] == "deep"

    def test_mixed_array_types(self, tmp_path: Path):
        """Test arrays with consistent types."""
        file = tmp_path / "test.toml"
        file.write_text('integers = [1, 2, 3]\nstrings = ["a", "b", "c"]')
        result = read(file)
        assert result["integers"] == [1, 2, 3]
        assert result["strings"] == ["a", "b", "c"]

    def test_special_float_values(self, tmp_path: Path):
        """Test special float values."""
        file = tmp_path / "test.toml"
        file.write_text("pos_inf = inf\nneg_inf = -inf\nnan_val = nan")
        result = read(file)
        import math

        assert math.isinf(result["pos_inf"]) and result["pos_inf"] > 0
        assert math.isinf(result["neg_inf"]) and result["neg_inf"] < 0
        assert math.isnan(result["nan_val"])

    def test_hexadecimal_integers(self, tmp_path: Path):
        """Test hexadecimal integer parsing."""
        file = tmp_path / "test.toml"
        file.write_text("hex_val = 0xDEADBEEF")
        result = read(file)
        assert result["hex_val"] == 0xDEADBEEF
