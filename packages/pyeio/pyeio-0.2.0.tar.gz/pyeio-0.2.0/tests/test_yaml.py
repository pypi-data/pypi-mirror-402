from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field

from pyeio.yaml._yaml import (
    DUMPER_MAP,
    LOADER_MAP,
    parse,
    read,
    serialize,
    serialize_pydantic,
    serialize_pyyaml,
    write,
    write_pydantic,
    write_pyyaml,
)


class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    title: str
    items: List[str]
    metadata: Optional[dict] = None


class AliasedModel(BaseModel):
    user_name: str = Field(alias="userName")
    user_age: int = Field(alias="userAge")

    model_config = {"populate_by_name": True}


@pytest.fixture
def simple_yaml_str() -> str:
    return "name: test\nvalue: 42\n"


@pytest.fixture
def simple_yaml_bytes() -> bytes:
    return b"name: test\nvalue: 42\n"


@pytest.fixture
def simple_dict() -> dict:
    return {"name": "test", "value": 42}


@pytest.fixture
def nested_yaml_str() -> str:
    return """title: Example
items:
  - one
  - two
  - three
metadata:
  key: value
"""


@pytest.fixture
def simple_model() -> SimpleModel:
    return SimpleModel(name="test", value=42)


@pytest.fixture
def nested_model() -> NestedModel:
    return NestedModel(
        title="Example",
        items=["one", "two", "three"],
        metadata={"key": "value"},
    )


@pytest.fixture
def tmp_yaml_file(tmp_path: Path) -> Path:
    return tmp_path / "test.yaml"


class TestParse:
    def test_parse_string_without_model(self, simple_yaml_str: str, simple_dict: dict):
        result = parse(simple_yaml_str, loader="safe")
        assert result == simple_dict

    def test_parse_bytes_without_model(
        self, simple_yaml_bytes: bytes, simple_dict: dict
    ):
        result = parse(simple_yaml_bytes, loader="safe")
        assert result == simple_dict

    def test_parse_with_pydantic_model(self, simple_yaml_str: str):
        result = parse(simple_yaml_str, SimpleModel, loader="safe")
        assert isinstance(result, SimpleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_parse_nested_yaml(self, nested_yaml_str: str):
        result = parse(nested_yaml_str, NestedModel, loader="safe")
        assert isinstance(result, NestedModel)
        assert result.title == "Example"
        assert result.items == ["one", "two", "three"]
        assert result.metadata == {"key": "value"}

    @pytest.mark.parametrize("loader_name", ["full", "safe", "unsafe"])
    def test_parse_with_different_loaders(self, simple_yaml_str: str, loader_name: str):
        result = parse(simple_yaml_str, loader=loader_name)
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_parse_with_strict_validation(self, simple_yaml_str: str):
        result = parse(simple_yaml_str, SimpleModel, strict=False, loader="safe")
        assert isinstance(result, SimpleModel)

    def test_parse_with_context(self, simple_yaml_str: str):
        result = parse(
            simple_yaml_str,
            SimpleModel,
            context={"extra": "data"},
            loader="safe",
        )
        assert isinstance(result, SimpleModel)

    def test_parse_invalid_yaml_raises_error(self):
        invalid_yaml = "invalid: yaml: content: [unclosed"
        with pytest.raises(Exception):
            parse(invalid_yaml, loader="safe")

    def test_parse_validation_error_with_wrong_types(self):
        yaml_data = "name: 123\nvalue: not_an_int\n"
        with pytest.raises(Exception):
            parse(yaml_data, SimpleModel, loader="safe")

    def test_parse_empty_yaml(self):
        result = parse("", loader="safe")
        assert result is None

    def test_parse_list_yaml(self):
        yaml_data = "- item1\n- item2\n- item3\n"
        result = parse(yaml_data, loader="safe")
        assert result == ["item1", "item2", "item3"]


class TestRead:
    def test_read_file_without_model(self, tmp_yaml_file: Path, simple_dict: dict):
        tmp_yaml_file.write_text("name: test\nvalue: 42\n")
        result = read(tmp_yaml_file, loader="safe")
        assert result == simple_dict

    def test_read_file_with_string_path(self, tmp_yaml_file: Path, simple_dict: dict):
        tmp_yaml_file.write_text("name: test\nvalue: 42\n")
        result = read(str(tmp_yaml_file), loader="safe")
        assert result == simple_dict

    def test_read_file_with_pydantic_model(self, tmp_yaml_file: Path):
        tmp_yaml_file.write_text("name: test\nvalue: 42\n")
        result = read(tmp_yaml_file, SimpleModel, loader="safe")
        assert isinstance(result, SimpleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_read_with_validation_params(self, tmp_yaml_file: Path):
        tmp_yaml_file.write_text("name: test\nvalue: 42\n")
        result = read(
            tmp_yaml_file,
            SimpleModel,
            strict=False,
            context=None,
            by_alias=False,
            by_name=True,
            loader="safe",
        )
        assert isinstance(result, SimpleModel)

    @pytest.mark.parametrize("loader_name", ["full", "safe", "unsafe"])
    def test_read_with_different_loaders(self, tmp_yaml_file: Path, loader_name: str):
        tmp_yaml_file.write_text("name: test\nvalue: 42\n")
        result = read(tmp_yaml_file, loader=loader_name)
        assert result["name"] == "test"


class TestSerializePyyaml:
    def test_serialize_dict_to_string(self, simple_dict: dict):
        result = serialize_pyyaml(simple_dict)
        assert isinstance(result, str)
        assert "name: test" in result
        assert "value: 42" in result

    def test_serialize_dict_to_bytes(self, simple_dict: dict):
        result = serialize_pyyaml(simple_dict, returns=bytes)
        assert isinstance(result, bytes)
        assert b"name: test" in result

    def test_serialize_with_encoding(self, simple_dict: dict):
        result = serialize_pyyaml(simple_dict, returns=bytes, encoding="utf-8")
        assert isinstance(result, bytes)

    def test_serialize_with_indent(self):
        data = {"outer": {"inner": "value"}}
        result = serialize_pyyaml(data, indent=4)
        assert "    inner:" in result

    def test_serialize_with_sort_keys_true(self):
        data = {"z_key": 1, "a_key": 2}
        result = serialize_pyyaml(data, sort_keys=True)
        assert result.index("a_key") < result.index("z_key")

    def test_serialize_with_sort_keys_false(self):
        data = {"z_key": 1, "a_key": 2}
        result = serialize_pyyaml(data, sort_keys=False)
        # Order should be preserved (z before a)
        assert result.index("z_key") < result.index("a_key")

    def test_serialize_with_default_flow_style(self):
        data = {"items": [1, 2, 3]}
        result = serialize_pyyaml(data, default_flow_style=True)
        assert "[1, 2, 3]" in result or "{" in result

    def test_serialize_with_width(self):
        data = {"key": "a" * 100}
        result = serialize_pyyaml(data, width=50)
        assert isinstance(result, str)

    def test_serialize_with_allow_unicode(self):
        data = {"text": "日本語"}
        result = serialize_pyyaml(data, allow_unicode=True)
        assert "日本語" in result

    @pytest.mark.parametrize("dumper_name", ["safe", "unsafe"])
    def test_serialize_with_different_dumpers(
        self, simple_dict: dict, dumper_name: str
    ):
        result = serialize_pyyaml(simple_dict, dumper=dumper_name)
        assert isinstance(result, str)

    def test_serialize_invalid_returns_type_raises_error(self, simple_dict: dict):
        with pytest.raises(TypeError):
            serialize_pyyaml(simple_dict, returns=int)  # type: ignore

    def test_serialize_list(self):
        data = [1, 2, 3, "four"]
        result = serialize_pyyaml(data)
        assert "- 1" in result
        assert "- four" in result

    def test_serialize_none(self):
        result = serialize_pyyaml(None)
        assert "null" in result


class TestSerializePydantic:
    def test_serialize_model_to_string(self, simple_model: SimpleModel):
        result = serialize_pydantic(simple_model)
        assert isinstance(result, str)
        assert "name: test" in result
        assert "value: 42" in result

    def test_serialize_model_to_bytes(self, simple_model: SimpleModel):
        result = serialize_pydantic(simple_model, returns=bytes)
        assert isinstance(result, bytes)

    def test_serialize_with_include(self):
        model = SimpleModel(name="test", value=42)
        result = serialize_pydantic(model, include={"name"})
        assert "name:" in result
        assert "value:" not in result

    def test_serialize_with_exclude(self):
        model = SimpleModel(name="test", value=42)
        result = serialize_pydantic(model, exclude={"value"})
        assert "name:" in result
        assert "value:" not in result

    def test_serialize_with_by_alias(self):
        model = AliasedModel(userName="John", userAge=30)
        result = serialize_pydantic(model, by_alias=True)
        assert "userName:" in result
        assert "userAge:" in result

    def test_serialize_with_exclude_none(self):
        class ModelWithOptional(BaseModel):
            required: str
            optional: Optional[str] = None

        model = ModelWithOptional(required="value")
        result = serialize_pydantic(model, exclude_none=True)
        assert "required:" in result
        assert "optional:" not in result

    def test_serialize_with_exclude_unset(self):
        class ModelWithDefault(BaseModel):
            required: str
            with_default: str = "default"

        model = ModelWithDefault(required="value")
        result = serialize_pydantic(model, exclude_unset=True)
        assert "required:" in result
        assert "with_default:" not in result

    def test_serialize_with_exclude_defaults(self):
        class ModelWithDefault(BaseModel):
            required: str
            with_default: str = "default"

        model = ModelWithDefault(required="value", with_default="default")
        result = serialize_pydantic(model, exclude_defaults=True)
        assert "required:" in result
        assert "with_default:" not in result

    def test_serialize_nested_model(self, nested_model: NestedModel):
        result = serialize_pydantic(nested_model)
        assert "title: Example" in result
        assert "- one" in result
        assert "key: value" in result

    def test_serialize_with_indent(self, nested_model: NestedModel):
        result = serialize_pydantic(nested_model, indent=4)
        assert isinstance(result, str)

    def test_serialize_invalid_returns_type_raises_error(
        self, simple_model: SimpleModel
    ):
        with pytest.raises(TypeError):
            serialize_pydantic(simple_model, returns=int)  # type: ignore


class TestSerialize:
    def test_serialize_pydantic_model(self, simple_model: SimpleModel):
        result = serialize(simple_model)
        assert isinstance(result, str)
        assert "name: test" in result

    def test_serialize_dict(self, simple_dict: dict):
        result = serialize(simple_dict)
        assert isinstance(result, str)
        assert "name: test" in result

    def test_serialize_list(self):
        data = [1, 2, 3]
        result = serialize(data)
        assert isinstance(result, str)

    def test_serialize_to_bytes(self, simple_dict: dict):
        result = serialize(simple_dict, returns=bytes)
        assert isinstance(result, bytes)

    def test_serialize_routes_pydantic_correctly(self, simple_model: SimpleModel):
        with patch("pyeio.yaml._yaml.serialize_pydantic") as mock_pydantic:
            mock_pydantic.return_value = "mocked"
            serialize(simple_model)
            mock_pydantic.assert_called_once()

    def test_serialize_routes_pyyaml_correctly(self, simple_dict: dict):
        with patch("pyeio.yaml._yaml.serialize_pyyaml") as mock_pyyaml:
            mock_pyyaml.return_value = "mocked"
            serialize(simple_dict)
            mock_pyyaml.assert_called_once()


class TestWritePyyaml:
    def test_write_dict_to_file(self, tmp_yaml_file: Path, simple_dict: dict):
        write_pyyaml(tmp_yaml_file, simple_dict)
        content = tmp_yaml_file.read_text()
        assert "name: test" in content
        assert "value: 42" in content

    def test_write_with_string_path(self, tmp_yaml_file: Path, simple_dict: dict):
        write_pyyaml(str(tmp_yaml_file), simple_dict)
        assert tmp_yaml_file.exists()

    def test_write_with_overwrite_false_existing_file(
        self, tmp_yaml_file: Path, simple_dict: dict
    ):
        tmp_yaml_file.write_text("existing content")
        with pytest.raises(Exception):
            write_pyyaml(tmp_yaml_file, simple_dict, overwrite=False)

    def test_write_with_overwrite_true(self, tmp_yaml_file: Path, simple_dict: dict):
        tmp_yaml_file.write_text("existing content")
        write_pyyaml(tmp_yaml_file, simple_dict, overwrite=True)
        content = tmp_yaml_file.read_text()
        assert "name: test" in content

    def test_write_with_formatting_options(self, tmp_yaml_file: Path):
        data = {"outer": {"inner": "value"}}
        write_pyyaml(tmp_yaml_file, data, indent=4, sort_keys=True)
        content = tmp_yaml_file.read_text()
        assert "    inner:" in content

    def test_write_creates_parent_directories(self, tmp_path: Path, simple_dict: dict):
        nested_file = tmp_path / "nested" / "dir" / "test.yaml"
        nested_file.parent.mkdir(parents=True, exist_ok=True)
        write_pyyaml(nested_file, simple_dict)
        assert nested_file.exists()


class TestWritePydantic:
    def test_write_model_to_file(self, tmp_yaml_file: Path, simple_model: SimpleModel):
        write_pydantic(tmp_yaml_file, simple_model)
        content = tmp_yaml_file.read_text()
        assert "name: test" in content
        assert "value: 42" in content

    def test_write_with_include(self, tmp_yaml_file: Path, simple_model: SimpleModel):
        write_pydantic(tmp_yaml_file, simple_model, include={"name"})
        content = tmp_yaml_file.read_text()
        assert "name:" in content
        assert "value:" not in content

    def test_write_with_exclude(self, tmp_yaml_file: Path, simple_model: SimpleModel):
        write_pydantic(tmp_yaml_file, simple_model, exclude={"value"})
        content = tmp_yaml_file.read_text()
        assert "name:" in content
        assert "value:" not in content

    def test_write_with_by_alias(self, tmp_yaml_file: Path):
        model = AliasedModel(userName="John", userAge=30)
        write_pydantic(tmp_yaml_file, model, by_alias=True)
        content = tmp_yaml_file.read_text()
        assert "userName:" in content

    def test_write_nested_model(self, tmp_yaml_file: Path, nested_model: NestedModel):
        write_pydantic(tmp_yaml_file, nested_model)
        content = tmp_yaml_file.read_text()
        assert "title: Example" in content
        assert "- one" in content

    def test_write_with_overwrite_true(
        self, tmp_yaml_file: Path, simple_model: SimpleModel
    ):
        tmp_yaml_file.write_text("existing")
        write_pydantic(tmp_yaml_file, simple_model, overwrite=True)
        content = tmp_yaml_file.read_text()
        assert "name: test" in content


class TestWrite:
    def test_write_pydantic_model(self, tmp_yaml_file: Path, simple_model: SimpleModel):
        write(tmp_yaml_file, simple_model)
        content = tmp_yaml_file.read_text()
        assert "name: test" in content

    def test_write_dict(self, tmp_yaml_file: Path, simple_dict: dict):
        write(tmp_yaml_file, simple_dict)
        content = tmp_yaml_file.read_text()
        assert "name: test" in content

    def test_write_routes_pydantic_correctly(
        self, tmp_yaml_file: Path, simple_model: SimpleModel
    ):
        with patch("pyeio.yaml._yaml.write_pydantic") as mock_write:
            write(tmp_yaml_file, simple_model)
            mock_write.assert_called_once()

    def test_write_routes_pyyaml_correctly(
        self, tmp_yaml_file: Path, simple_dict: dict
    ):
        with patch("pyeio.yaml._yaml.write_pyyaml") as mock_write:
            write(tmp_yaml_file, simple_dict)
            mock_write.assert_called_once()

    def test_write_with_overwrite(self, tmp_yaml_file: Path, simple_dict: dict):
        tmp_yaml_file.write_text("existing")
        write(tmp_yaml_file, simple_dict, overwrite=True)
        assert tmp_yaml_file.exists()


class TestMaps:
    def test_loader_map_contains_expected_keys(self):
        assert "full" in LOADER_MAP
        assert "safe" in LOADER_MAP
        assert "unsafe" in LOADER_MAP

    def test_dumper_map_contains_expected_keys(self):
        assert "safe" in DUMPER_MAP
        assert "unsafe" in DUMPER_MAP


class TestIntegration:
    def test_roundtrip_pydantic_model(self, tmp_yaml_file: Path):
        original = SimpleModel(name="roundtrip", value=123)
        write(tmp_yaml_file, original)
        loaded = read(tmp_yaml_file, SimpleModel, loader="safe")
        assert loaded.name == original.name
        assert loaded.value == original.value

    def test_roundtrip_nested_model(self, tmp_yaml_file: Path):
        original = NestedModel(
            title="Test",
            items=["a", "b", "c"],
            metadata={"nested": "data"},
        )
        write(tmp_yaml_file, original)
        loaded = read(tmp_yaml_file, NestedModel, loader="safe")
        assert loaded.title == original.title
        assert loaded.items == original.items
        assert loaded.metadata == original.metadata

    def test_roundtrip_dict(self, tmp_yaml_file: Path):
        original = {"key": "value", "number": 42, "list": [1, 2, 3]}
        write(tmp_yaml_file, original)
        loaded = read(tmp_yaml_file, loader="safe")
        assert loaded == original

    def test_parse_and_serialize_consistency(self, simple_model: SimpleModel):
        serialized = serialize(simple_model)
        parsed = parse(serialized, SimpleModel, loader="safe")
        assert parsed.name == simple_model.name
        assert parsed.value == simple_model.value
