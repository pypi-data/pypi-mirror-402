from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import orjson
import pytest
from pydantic import BaseModel, Field

from pyeio.json._json import (
    JSONDecodeError,
    JSONEncodeError,
    compute_orjson_opt_code,
    parse,
    read,
    serialize,
    serialize_orjson,
    serialize_pydantic,
    write_orjson,
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


@dataclasses.dataclass
class SimpleDataclass:
    name: str
    value: int


@pytest.fixture
def simple_dict() -> dict[str, Any]:
    return {"name": "test", "value": 42, "nested": {"a": 1, "b": 2}}


@pytest.fixture
def simple_list() -> list[Any]:
    return [1, 2, 3, "four", {"five": 5}]


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
def temp_json_file(tmp_path: Path) -> Path:
    return tmp_path / "test.json"


@pytest.fixture
def existing_json_file(tmp_path: Path) -> Path:
    file = tmp_path / "existing.json"
    file.write_bytes(b'{"existing": true}')
    return file


class TestComputeOrjsonOptCode:
    def test_default_options(self):
        """Test default option code computation."""
        opt_code = compute_orjson_opt_code()
        assert opt_code & orjson.OPT_NON_STR_KEYS  # coerce_keys_to_str=True
        assert opt_code & orjson.OPT_OMIT_MICROSECONDS  # always set
        assert opt_code & orjson.OPT_SERIALIZE_NUMPY  # coerce_numpy_arrays=True
        assert not (opt_code & orjson.OPT_APPEND_NEWLINE)
        assert not (opt_code & orjson.OPT_INDENT_2)
        assert not (opt_code & orjson.OPT_SORT_KEYS)

    def test_caching(self):
        """Test that function results are cached."""
        # Call with same args multiple times
        opt1 = compute_orjson_opt_code(indent_two_spaces=True, sort_keys=True)
        opt2 = compute_orjson_opt_code(indent_two_spaces=True, sort_keys=True)
        assert opt1 == opt2
        # Check cache info
        cache_info = compute_orjson_opt_code.cache_info()
        assert cache_info.hits >= 1


class TestParse:
    def test_parse_dict_from_string(self):
        """Test parsing a dictionary from JSON string."""
        data = '{"name": "test", "value": 42}'
        result = parse(data)
        assert result == {"name": "test", "value": 42}

    def test_parse_dict_from_bytes(self):
        """Test parsing a dictionary from JSON bytes."""
        data = b'{"name": "test", "value": 42}'
        result = parse(data)
        assert result == {"name": "test", "value": 42}

    def test_parse_list(self):
        """Test parsing a list from JSON."""
        data = '[1, 2, 3, "four"]'
        result = parse(data)
        assert result == [1, 2, 3, "four"]

    def test_parse_primitive_types(self):
        """Test parsing primitive JSON types."""
        assert parse("null") is None
        assert parse("true") is True
        assert parse("false") is False
        assert parse("42") == 42
        assert parse("3.14") == 3.14
        assert parse('"hello"') == "hello"

    def test_parse_with_pydantic_model(self):
        """Test parsing JSON into a Pydantic model."""
        data = '{"name": "test", "value": 42}'
        result = parse(data, SimpleModel)
        assert isinstance(result, SimpleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_parse_nested_pydantic_model(self):
        """Test parsing JSON into a nested Pydantic model."""
        data = '{"id": 1, "data": {"name": "nested", "value": 100}, "tags": ["a", "b"]}'
        result = parse(data, NestedModel)
        assert isinstance(result, NestedModel)
        assert result.id == 1
        assert result.data.name == "nested"
        assert result.tags == ["a", "b"]

    def test_parse_pydantic_with_strict_mode(self):
        """Test parsing with strict validation mode."""
        data = '{"name": "test", "value": 42}'
        result = parse(data, SimpleModel, strict=True)
        assert isinstance(result, SimpleModel)

    def test_parse_pydantic_with_context(self):
        """Test parsing with validation context."""
        data = '{"name": "test", "value": 42}'
        result = parse(data, SimpleModel, context={"extra": "data"})
        assert isinstance(result, SimpleModel)

    def test_parse_pydantic_by_alias(self):
        """Test parsing with by_alias option."""
        data = '{"fieldName": "test"}'
        result = parse(data, ModelWithAlias, by_alias=True)
        assert result.field_name == "test"

    def test_parse_pydantic_by_name(self):
        """Test parsing with by_name option."""
        data = '{"field_name": "test"}'
        result = parse(data, ModelWithAlias, by_name=True)
        assert result.field_name == "test"

    def test_parse_invalid_json_raises_error(self):
        """Test that invalid JSON raises JSONDecodeError."""
        with pytest.raises(JSONDecodeError):
            parse("{invalid json}")

    def test_parse_pydantic_validation_error(self):
        """Test that invalid data raises validation error."""
        from pydantic import ValidationError

        data = '{"name": "test"}'  # missing 'value'
        with pytest.raises(ValidationError):
            parse(data, SimpleModel)


class TestRead:
    def test_read_dict(self, tmp_path: Path):
        """Test reading a dictionary from JSON file."""
        file = tmp_path / "test.json"
        file.write_bytes(b'{"name": "test", "value": 42}')

        result = read(file)
        assert result == {"name": "test", "value": 42}

    def test_read_with_string_path(self, tmp_path: Path):
        """Test reading with string path."""
        file = tmp_path / "test.json"
        file.write_bytes(b'{"key": "value"}')

        result = read(str(file))
        assert result == {"key": "value"}

    def test_read_list(self, tmp_path: Path):
        """Test reading a list from JSON file."""
        file = tmp_path / "test.json"
        file.write_bytes(b"[1, 2, 3]")

        result = read(file)
        assert result == [1, 2, 3]

    def test_read_with_pydantic_model(self, tmp_path: Path):
        """Test reading JSON into a Pydantic model."""
        file = tmp_path / "test.json"
        file.write_bytes(b'{"name": "test", "value": 42}')

        result = read(file, SimpleModel)
        assert isinstance(result, SimpleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_read_nested_pydantic_model(self, tmp_path: Path):
        """Test reading JSON into a nested Pydantic model."""
        file = tmp_path / "test.json"
        file.write_bytes(
            b'{"id": 1, "data": {"name": "nested", "value": 100}, "tags": []}'
        )

        result = read(file, NestedModel)
        assert isinstance(result, NestedModel)
        assert result.id == 1

    def test_read_with_strict_mode(self, tmp_path: Path):
        """Test reading with strict validation mode."""
        file = tmp_path / "test.json"
        file.write_bytes(b'{"name": "test", "value": 42}')

        result = read(file, SimpleModel, strict=True)
        assert isinstance(result, SimpleModel)

    def test_read_with_context(self, tmp_path: Path):
        """Test reading with validation context."""
        file = tmp_path / "test.json"
        file.write_bytes(b'{"name": "test", "value": 42}')

        result = read(file, SimpleModel, context={"key": "value"})
        assert isinstance(result, SimpleModel)

    def test_read_nonexistent_file_raises_error(self, tmp_path: Path):
        """Test that reading non-existent file raises error."""
        file = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            read(file)

    def test_read_invalid_json_raises_error(self, tmp_path: Path):
        """Test that invalid JSON raises JSONDecodeError."""
        file = tmp_path / "test.json"
        file.write_bytes(b"{invalid}")

        with pytest.raises(JSONDecodeError):
            read(file)


class TestSerializeOrjson:
    def test_serialize_dict_to_bytes(self, simple_dict: dict):
        """Test serializing dict to bytes (default)."""
        result = serialize_orjson(simple_dict)
        assert isinstance(result, bytes)
        assert orjson.loads(result) == simple_dict

    def test_serialize_dict_to_str(self, simple_dict: dict):
        """Test serializing dict to string."""
        result = serialize_orjson(simple_dict, returns=str)
        assert isinstance(result, str)
        assert orjson.loads(result) == simple_dict

    def test_serialize_list(self, simple_list: list):
        """Test serializing list."""
        result = serialize_orjson(simple_list)
        assert orjson.loads(result) == simple_list

    def test_serialize_with_indent(self, simple_dict: dict):
        """Test serializing with indentation."""
        result = serialize_orjson(simple_dict, returns=str, indent=True)
        assert "\n" in result
        assert "  " in result  # 2-space indent

    def test_serialize_with_newline(self, simple_dict: dict):
        """Test serializing with trailing newline."""
        result = serialize_orjson(simple_dict, append_newline=True)
        assert result.endswith(b"\n")

    def test_serialize_with_sorted_keys(self):
        """Test serializing with sorted keys."""
        data = {"z": 1, "a": 2, "m": 3}
        result = serialize_orjson(data, returns=str, sort_keys=True)
        # Keys should appear in alphabetical order
        assert result.index('"a"') < result.index('"m"') < result.index('"z"')

    def test_serialize_non_string_keys(self):
        """Test serializing dict with non-string keys."""
        data = {1: "one", 2: "two"}
        result = serialize_orjson(data, coerce_keys_to_str=True)
        parsed = orjson.loads(result)
        assert parsed == {"1": "one", "2": "two"}

    def test_serialize_dataclass(self):
        """Test serializing dataclass."""
        dc = SimpleDataclass(name="test", value=42)
        result = serialize_orjson(dc, coerce_dataclasses=True)
        parsed = orjson.loads(result)
        assert parsed == {"name": "test", "value": 42}

    def test_serialize_datetime(self):
        """Test serializing datetime objects."""
        dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        data = {"timestamp": dt}
        result = serialize_orjson(data, coerce_datetimes=True)
        parsed = orjson.loads(result)
        assert "timestamp" in parsed
        assert "2024-01-15" in parsed["timestamp"]

    def test_serialize_numpy_array(self):
        """Test serializing numpy arrays."""
        arr = np.array([1, 2, 3, 4, 5])
        result = serialize_orjson(arr, coerce_numpy_arrays=True)
        parsed = orjson.loads(result)
        assert parsed == [1, 2, 3, 4, 5]

    def test_serialize_numpy_2d_array(self):
        """Test serializing 2D numpy arrays."""
        arr = np.array([[1, 2], [3, 4]])
        result = serialize_orjson(arr, coerce_numpy_arrays=True)
        parsed = orjson.loads(result)
        assert parsed == [[1, 2], [3, 4]]

    def test_serialize_with_custom_encoding(self, simple_dict: dict):
        """Test serializing with custom encoding."""
        result = serialize_orjson(simple_dict, returns=str, encoding="utf-8")
        assert isinstance(result, str)

    def test_serialize_with_fallback(self):
        """Test serializing with fallback function."""

        class CustomObject:
            def __init__(self, value):
                self.value = value

        def fallback(obj):
            if isinstance(obj, CustomObject):
                return {"custom": obj.value}
            raise TypeError

        data = {"obj": CustomObject(42)}
        result = serialize_orjson(data, fallback=fallback)
        parsed = orjson.loads(result)
        assert parsed == {"obj": {"custom": 42}}

    def test_serialize_invalid_returns_type_raises_error(self, simple_dict: dict):
        """Test that invalid returns type raises TypeError."""
        with pytest.raises(TypeError):
            serialize_orjson(simple_dict, returns=list)  # type: ignore

    def test_serialize_non_serializable_raises_error(self):
        """Test that non-serializable data raises error."""

        class NotSerializable:
            pass

        with pytest.raises((TypeError, JSONEncodeError)):
            serialize_orjson({"obj": NotSerializable()})


class TestSerializePydantic:
    def test_serialize_to_bytes(self, simple_model: SimpleModel):
        """Test serializing Pydantic model to bytes (default)."""
        result = serialize_pydantic(simple_model)
        assert isinstance(result, bytes)
        parsed = orjson.loads(result)
        assert parsed == {"name": "test", "value": 42}

    def test_serialize_to_str(self, simple_model: SimpleModel):
        """Test serializing Pydantic model to string."""
        result = serialize_pydantic(simple_model, returns=str)
        assert isinstance(result, str)
        parsed = orjson.loads(result)
        assert parsed == {"name": "test", "value": 42}

    def test_serialize_nested_model(self, nested_model: NestedModel):
        """Test serializing nested Pydantic model."""
        result = serialize_pydantic(nested_model)
        parsed = orjson.loads(result)
        assert parsed["id"] == 1
        assert parsed["data"]["name"] == "nested"
        assert parsed["tags"] == ["tag1", "tag2"]

    def test_serialize_with_indent(self, simple_model: SimpleModel):
        """Test serializing with indentation."""
        result = serialize_pydantic(simple_model, returns=str, indent=True)
        assert "\n" in result

    def test_serialize_with_include(self, nested_model: NestedModel):
        """Test serializing with field inclusion."""
        result = serialize_pydantic(nested_model, include={"id"})
        parsed = orjson.loads(result)
        assert "id" in parsed
        assert "data" not in parsed
        assert "tags" not in parsed

    def test_serialize_with_exclude(self, nested_model: NestedModel):
        """Test serializing with field exclusion."""
        result = serialize_pydantic(nested_model, exclude={"tags"})
        parsed = orjson.loads(result)
        assert "id" in parsed
        assert "data" in parsed
        assert "tags" not in parsed

    def test_serialize_exclude_unset(self, model_with_optional: ModelWithOptional):
        """Test serializing with exclude_unset."""
        result = serialize_pydantic(model_with_optional, exclude_unset=True)
        parsed = orjson.loads(result)
        assert "required" in parsed
        assert "optional" not in parsed
        assert "with_default" not in parsed

    def test_serialize_exclude_defaults(self, model_with_optional: ModelWithOptional):
        """Test serializing with exclude_defaults."""
        result = serialize_pydantic(model_with_optional, exclude_defaults=True)
        parsed = orjson.loads(result)
        assert "required" in parsed
        assert "with_default" not in parsed

    def test_serialize_exclude_none(self, model_with_optional: ModelWithOptional):
        """Test serializing with exclude_none."""
        result = serialize_pydantic(model_with_optional, exclude_none=True)
        parsed = orjson.loads(result)
        assert "required" in parsed
        assert "optional" not in parsed

    def test_serialize_by_alias(self):
        """Test serializing with field aliases."""
        model = ModelWithAlias(fieldName="test")
        result = serialize_pydantic(model, by_alias=True)
        parsed = orjson.loads(result)
        assert "fieldName" in parsed
        assert "field_name" not in parsed

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


class TestSerialize:
    def test_serialize_dict_routes_to_orjson(self, simple_dict: dict):
        """Test that dict is serialized via orjson."""
        result = serialize(simple_dict, bytes)
        assert isinstance(result, bytes)
        assert orjson.loads(result) == simple_dict

    def test_serialize_list_routes_to_orjson(self, simple_list: list):
        """Test that list is serialized via orjson."""
        result = serialize(simple_list)
        assert orjson.loads(result) == simple_list

    def test_serialize_pydantic_routes_to_pydantic(self, simple_model: SimpleModel):
        """Test that Pydantic model is serialized via pydantic serializer."""
        result = serialize(simple_model, bytes)
        assert isinstance(result, bytes)
        parsed = orjson.loads(result)
        assert parsed == {"name": "test", "value": 42}

    def test_serialize_with_returns_str(self, simple_dict: dict):
        """Test serializing to string."""
        result = serialize(simple_dict, returns=str)
        assert isinstance(result, str)

    def test_serialize_with_indent(self, simple_dict: dict):
        """Test serializing with indentation."""
        result = serialize(simple_dict, returns=str, indent=True)
        assert "\n" in result

    def test_serialize_passes_kwargs_to_orjson(self, simple_dict: dict):
        """Test that kwargs are passed to orjson serializer."""
        result = serialize(simple_dict, sort_keys=True, returns=str)
        # Verify sorted keys behavior
        data = {"z": 1, "a": 2}
        result = serialize(data, sort_keys=True, returns=str)
        assert result.index('"a"') < result.index('"z"')

    def test_serialize_passes_kwargs_to_pydantic(self, nested_model: NestedModel):
        """Test that kwargs are passed to pydantic serializer."""
        result = serialize(nested_model, exclude={"tags"})
        parsed = orjson.loads(result)
        assert "tags" not in parsed


class TestWriteOrjson:
    def test_write_dict(self, temp_json_file: Path, simple_dict: dict):
        """Test writing dict to file."""
        write_orjson(temp_json_file, simple_dict)
        assert temp_json_file.exists()
        content = orjson.loads(temp_json_file.read_bytes())
        assert content == simple_dict

    def test_write_with_string_path(self, temp_json_file: Path, simple_dict: dict):
        """Test writing with string path."""
        write_orjson(str(temp_json_file), simple_dict)
        assert temp_json_file.exists()

    def test_write_list(self, temp_json_file: Path, simple_list: list):
        """Test writing list to file."""
        write_orjson(temp_json_file, simple_list)
        content = orjson.loads(temp_json_file.read_bytes())
        assert content == simple_list

    def test_write_with_indent(self, temp_json_file: Path, simple_dict: dict):
        """Test writing with indentation."""
        write_orjson(temp_json_file, simple_dict, indent=True)
        content = temp_json_file.read_text()
        assert "\n" in content

    def test_write_with_newline(self, temp_json_file: Path, simple_dict: dict):
        """Test writing with trailing newline."""
        write_orjson(temp_json_file, simple_dict, append_newline=True)
        content = temp_json_file.read_bytes()
        assert content.endswith(b"\n")

    def test_write_with_sorted_keys(self, temp_json_file: Path):
        """Test writing with sorted keys."""
        data = {"z": 1, "a": 2, "m": 3}
        write_orjson(temp_json_file, data, sort_keys=True)
        content = temp_json_file.read_text()
        assert content.index('"a"') < content.index('"m"') < content.index('"z"')

    def test_write_numpy_array(self, temp_json_file: Path):
        """Test writing numpy array."""
        arr = np.array([1, 2, 3])
        write_orjson(temp_json_file, arr, coerce_numpy_arrays=True)
        content = orjson.loads(temp_json_file.read_bytes())
        assert content == [1, 2, 3]

    def test_write_dataclass(self, temp_json_file: Path):
        """Test writing dataclass."""
        dc = SimpleDataclass(name="test", value=42)
        write_orjson(temp_json_file, dc, coerce_dataclasses=True)
        content = orjson.loads(temp_json_file.read_bytes())
        assert content == {"name": "test", "value": 42}

    def test_write_overwrite_false_raises_on_existing(self, existing_json_file: Path):
        """Test that overwrite=False raises error for existing file."""
        with pytest.raises(FileExistsError):
            write_orjson(existing_json_file, {"new": "data"}, overwrite=False)

    def test_write_overwrite_true_replaces_existing(self, existing_json_file: Path):
        """Test that overwrite=True replaces existing file."""
        write_orjson(existing_json_file, {"new": "data"}, overwrite=True)
        content = orjson.loads(existing_json_file.read_bytes())
        assert content == {"new": "data"}

    def test_write_with_fallback(self, temp_json_file: Path):
        """Test writing with fallback function."""

        class Custom:
            def __init__(self, val):
                self.val = val

        def fallback(obj):
            if isinstance(obj, Custom):
                return {"custom_val": obj.val}
            raise TypeError

        write_orjson(temp_json_file, {"obj": Custom(99)}, fallback=fallback)
        content = orjson.loads(temp_json_file.read_bytes())
        assert content == {"obj": {"custom_val": 99}}


class TestWritePydantic:
    def test_write_simple_model(self, temp_json_file: Path, simple_model: SimpleModel):
        """Test writing simple Pydantic model."""
        write_pydantic(temp_json_file, simple_model)
        assert temp_json_file.exists()
        content = orjson.loads(temp_json_file.read_bytes())
        assert content == {"name": "test", "value": 42}

    def test_write_nested_model(self, temp_json_file: Path, nested_model: NestedModel):
        """Test writing nested Pydantic model."""
        write_pydantic(temp_json_file, nested_model)
        content = orjson.loads(temp_json_file.read_bytes())
        assert content["id"] == 1
        assert content["data"]["name"] == "nested"

    def test_write_with_indent(self, temp_json_file: Path, simple_model: SimpleModel):
        """Test writing with indentation."""
        write_pydantic(temp_json_file, simple_model, indent=True)
        content = temp_json_file.read_text()
        assert "\n" in content

    def test_write_with_include(self, temp_json_file: Path, nested_model: NestedModel):
        """Test writing with field inclusion."""
        write_pydantic(temp_json_file, nested_model, include={"id"})
        content = orjson.loads(temp_json_file.read_bytes())
        assert list(content.keys()) == ["id"]

    def test_write_with_exclude(self, temp_json_file: Path, nested_model: NestedModel):
        """Test writing with field exclusion."""
        write_pydantic(temp_json_file, nested_model, exclude={"tags"})
        content = orjson.loads(temp_json_file.read_bytes())
        assert "tags" not in content

    def test_write_exclude_unset(
        self, temp_json_file: Path, model_with_optional: ModelWithOptional
    ):
        """Test writing with exclude_unset."""
        write_pydantic(temp_json_file, model_with_optional, exclude_unset=True)
        _ = orjson.loads(temp_json_file.read_bytes())
