from pathlib import Path

import pytest

from pyeio.io import (
    append,
    append_binary,
    append_string,
    insert,
    insert_binary,
    insert_string,
    read,
    read_binary,
    read_string,
    write,
    write_binary,
    write_string,
)


@pytest.fixture
def text_file(tmp_path: Path) -> Path:
    """Create a temporary text file with sample content."""
    file = tmp_path / "sample.txt"
    file.write_text("Hello, World!", encoding="utf-8")
    return file


@pytest.fixture
def binary_file(tmp_path: Path) -> Path:
    """Create a temporary binary file with sample content."""
    file = tmp_path / "sample.bin"
    file.write_bytes(b"\x00\x01\x02\x03\x04\x05")
    return file


@pytest.fixture
def empty_file(tmp_path: Path) -> Path:
    """Create an empty temporary file."""
    file = tmp_path / "empty.txt"
    file.write_text("")
    return file


@pytest.fixture
def utf16_file(tmp_path: Path) -> Path:
    """Create a temporary file with UTF-16 encoding."""
    file = tmp_path / "utf16.txt"
    file.write_text("Héllo Wörld", encoding="utf-16")
    return file


class TestReadString:
    def test_read_entire_file(self, text_file: Path):
        result = read_string(text_file)
        assert result == "Hello, World!"

    def test_read_with_size_limit(self, text_file: Path):
        result = read_string(text_file, size=5)
        assert result == "Hello"

    def test_read_size_larger_than_file(self, text_file: Path):
        result = read_string(text_file, size=1000)
        assert result == "Hello, World!"

    def test_read_size_zero(self, text_file: Path):
        result = read_string(text_file, size=0)
        assert result == ""

    def test_read_size_negative(self, text_file: Path):
        result = read_string(text_file, size=-1)
        assert result == "Hello, World!"

    def test_read_empty_file(self, empty_file: Path):
        result = read_string(empty_file)
        assert result == ""

    def test_read_with_encoding(self, utf16_file: Path):
        result = read_string(utf16_file, encoding="utf-16")
        assert result == "Héllo Wörld"

    def test_read_nonexistent_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            read_string(tmp_path / "nonexistent.txt")

    def test_read_with_str_path(self, text_file: Path):
        result = read_string(str(text_file))
        assert result == "Hello, World!"

    def test_read_multiline(self, tmp_path: Path):
        file = tmp_path / "multiline.txt"
        content = "Line 1\nLine 2\nLine 3"
        file.write_text(content, encoding="utf-8")
        result = read_string(file)
        assert result == content


class TestReadBinary:
    def test_read_entire_file(self, binary_file: Path):
        result = read_binary(binary_file)
        assert result == b"\x00\x01\x02\x03\x04\x05"

    def test_read_with_size_limit(self, binary_file: Path):
        result = read_binary(binary_file, size=3)
        assert result == b"\x00\x01\x02"

    def test_read_size_larger_than_file(self, binary_file: Path):
        result = read_binary(binary_file, size=1000)
        assert result == b"\x00\x01\x02\x03\x04\x05"

    def test_read_size_zero(self, binary_file: Path):
        result = read_binary(binary_file, size=0)
        assert result == b""

    def test_read_size_negative(self, binary_file: Path):
        result = read_binary(binary_file, size=-1)
        assert result == b"\x00\x01\x02\x03\x04\x05"

    def test_read_empty_file(self, tmp_path: Path):
        file = tmp_path / "empty.bin"
        file.write_bytes(b"")
        result = read_binary(file)
        assert result == b""

    def test_read_nonexistent_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            read_binary(tmp_path / "nonexistent.bin")

    def test_read_with_str_path(self, binary_file: Path):
        result = read_binary(str(binary_file))
        assert result == b"\x00\x01\x02\x03\x04\x05"


class TestRead:
    def test_read_as_string_default(self, text_file: Path):
        result = read(text_file)
        assert result == "Hello, World!"
        assert isinstance(result, str)

    def test_read_as_string_explicit(self, text_file: Path):
        result = read(text_file, str)
        assert result == "Hello, World!"
        assert isinstance(result, str)

    def test_read_as_bytes(self, binary_file: Path):
        result = read(binary_file, bytes)
        assert result == b"\x00\x01\x02\x03\x04\x05"
        assert isinstance(result, bytes)

    def test_read_text_as_bytes(self, text_file: Path):
        result = read(text_file, bytes)
        assert result == b"Hello, World!"
        assert isinstance(result, bytes)


class TestWriteString:
    def test_write_new_file(self, tmp_path: Path):
        file = tmp_path / "new.txt"
        write_string(file, "Test content")
        assert file.read_text(encoding="utf-8") == "Test content"

    def test_write_overwrite_false_raises(self, text_file: Path):
        with pytest.raises(FileExistsError):
            write_string(text_file, "New content", overwrite=False)

    def test_write_overwrite_true(self, text_file: Path):
        write_string(text_file, "New content", overwrite=True)
        assert text_file.read_text(encoding="utf-8") == "New content"

    def test_write_with_encoding(self, tmp_path: Path):
        file = tmp_path / "utf16.txt"
        write_string(file, "Héllo Wörld", encoding="utf-16")
        assert file.read_text(encoding="utf-16") == "Héllo Wörld"

    def test_write_empty_string(self, tmp_path: Path):
        file = tmp_path / "empty.txt"
        write_string(file, "")
        assert file.read_text(encoding="utf-8") == ""

    def test_write_multiline(self, tmp_path: Path):
        file = tmp_path / "multiline.txt"
        content = "Line 1\nLine 2\nLine 3"
        write_string(file, content)
        assert file.read_text(encoding="utf-8") == content

    def test_write_with_str_path(self, tmp_path: Path):
        file = tmp_path / "str_path.txt"
        write_string(str(file), "Test content")
        assert file.read_text(encoding="utf-8") == "Test content"


class TestWriteBinary:
    def test_write_new_file(self, tmp_path: Path):
        file = tmp_path / "new.bin"
        write_binary(file, b"\x00\x01\x02")
        assert file.read_bytes() == b"\x00\x01\x02"

    def test_write_overwrite_false_raises(self, binary_file: Path):
        with pytest.raises(FileExistsError):
            write_binary(binary_file, b"\xff\xfe", overwrite=False)

    def test_write_overwrite_true(self, binary_file: Path):
        write_binary(binary_file, b"\xff\xfe", overwrite=True)
        assert binary_file.read_bytes() == b"\xff\xfe"

    def test_write_empty_bytes(self, tmp_path: Path):
        file = tmp_path / "empty.bin"
        write_binary(file, b"")
        assert file.read_bytes() == b""

    def test_write_with_str_path(self, tmp_path: Path):
        file = tmp_path / "str_path.bin"
        write_binary(str(file), b"\x00\x01\x02")
        assert file.read_bytes() == b"\x00\x01\x02"


class TestWrite:
    def test_write_string(self, tmp_path: Path):
        file = tmp_path / "test.txt"
        write(file, "Test content")
        assert file.read_text(encoding="utf-8") == "Test content"

    def test_write_bytes(self, tmp_path: Path):
        file = tmp_path / "test.bin"
        write(file, b"\x00\x01\x02")
        assert file.read_bytes() == b"\x00\x01\x02"

    def test_write_overwrite_false_raises(self, text_file: Path):
        with pytest.raises(FileExistsError):
            write(text_file, "New content", overwrite=False)

    def test_write_overwrite_true(self, text_file: Path):
        write(text_file, "New content", overwrite=True)
        assert text_file.read_text(encoding="utf-8") == "New content"


class TestAppendString:
    def test_append_to_existing(self, text_file: Path):
        append_string(text_file, " Goodbye!")
        assert text_file.read_text(encoding="utf-8") == "Hello, World! Goodbye!"

    def test_append_to_empty(self, empty_file: Path):
        append_string(empty_file, "First content")
        assert empty_file.read_text(encoding="utf-8") == "First content"

    def test_append_creates_file(self, tmp_path: Path):
        file = tmp_path / "new.txt"
        append_string(file, "New content")
        assert file.read_text(encoding="utf-8") == "New content"

    def test_append_with_encoding(self, tmp_path: Path):
        file = tmp_path / "utf16.txt"
        file.write_text("Hello", encoding="utf-16")
        append_string(file, " World", encoding="utf-16")
        assert file.read_text(encoding="utf-16") == "Hello World"

    def test_append_empty_string(self, text_file: Path):
        append_string(text_file, "")
        assert text_file.read_text(encoding="utf-8") == "Hello, World!"

    def test_append_newline(self, text_file: Path):
        append_string(text_file, "\nNew line")
        assert text_file.read_text(encoding="utf-8") == "Hello, World!\nNew line"


class TestAppendBinary:
    def test_append_to_existing(self, binary_file: Path):
        append_binary(binary_file, b"\x06\x07")
        assert binary_file.read_bytes() == b"\x00\x01\x02\x03\x04\x05\x06\x07"

    def test_append_to_empty(self, tmp_path: Path):
        file = tmp_path / "empty.bin"
        file.write_bytes(b"")
        append_binary(file, b"\x00\x01")
        assert file.read_bytes() == b"\x00\x01"

    def test_append_creates_file(self, tmp_path: Path):
        file = tmp_path / "new.bin"
        append_binary(file, b"\x00\x01")
        assert file.read_bytes() == b"\x00\x01"

    def test_append_empty_bytes(self, binary_file: Path):
        append_binary(binary_file, b"")
        assert binary_file.read_bytes() == b"\x00\x01\x02\x03\x04\x05"


class TestAppend:
    def test_append_string(self, text_file: Path):
        append(text_file, " Goodbye!")
        assert text_file.read_text(encoding="utf-8") == "Hello, World! Goodbye!"

    def test_append_bytes(self, binary_file: Path):
        append(binary_file, b"\x06\x07")
        assert binary_file.read_bytes() == b"\x00\x01\x02\x03\x04\x05\x06\x07"


class TestInsertString:
    def test_insert_at_beginning(self, text_file: Path):
        insert_string(text_file, "Start: ", position=0)
        assert text_file.read_text(encoding="utf-8") == "Start: Hello, World!"

    def test_insert_at_middle(self, text_file: Path):
        insert_string(text_file, "INSERTED", position=7)
        assert text_file.read_text(encoding="utf-8") == "Hello, INSERTEDWorld!"

    def test_insert_at_end(self, text_file: Path):
        insert_string(text_file, " End", position=13)
        assert text_file.read_text(encoding="utf-8") == "Hello, World! End"

    def test_insert_beyond_end(self, text_file: Path):
        insert_string(text_file, " Extra", position=100)
        assert text_file.read_text(encoding="utf-8") == "Hello, World! Extra"

    def test_insert_empty_string(self, text_file: Path):
        insert_string(text_file, "", position=5)
        assert text_file.read_text(encoding="utf-8") == "Hello, World!"

    def test_insert_into_empty_file(self, empty_file: Path):
        insert_string(empty_file, "Content")
        assert empty_file.read_text(encoding="utf-8") == "Content"

    def test_insert_with_encoding(self, utf16_file: Path):
        insert_string(utf16_file, "-->", position=5, encoding="utf-16")
        assert utf16_file.read_text(encoding="utf-16") == "Héllo--> Wörld"

    def test_insert_default_position(self, text_file: Path):
        insert_string(text_file, "Start: ")
        assert text_file.read_text(encoding="utf-8") == "Start: Hello, World!"


class TestInsertBinary:
    def test_insert_at_beginning(self, binary_file: Path):
        insert_binary(binary_file, b"\xff\xfe", position=0)
        assert binary_file.read_bytes() == b"\xff\xfe\x00\x01\x02\x03\x04\x05"

    def test_insert_at_middle(self, binary_file: Path):
        insert_binary(binary_file, b"\xff\xfe", position=3)
        assert binary_file.read_bytes() == b"\x00\x01\x02\xff\xfe\x03\x04\x05"

    def test_insert_at_end(self, binary_file: Path):
        insert_binary(binary_file, b"\xff\xfe", position=6)
        assert binary_file.read_bytes() == b"\x00\x01\x02\x03\x04\x05\xff\xfe"

    def test_insert_beyond_end(self, binary_file: Path):
        insert_binary(binary_file, b"\xff", position=100)
        assert binary_file.read_bytes() == b"\x00\x01\x02\x03\x04\x05\xff"

    def test_insert_empty_bytes(self, binary_file: Path):
        insert_binary(binary_file, b"", position=3)
        assert binary_file.read_bytes() == b"\x00\x01\x02\x03\x04\x05"

    def test_insert_into_empty_file(self, tmp_path: Path):
        file = tmp_path / "empty.bin"
        file.write_bytes(b"")
        insert_binary(file, b"\x00\x01")
        assert file.read_bytes() == b"\x00\x01"

    def test_insert_default_position(self, binary_file: Path):
        insert_binary(binary_file, b"\xff\xfe")
        assert binary_file.read_bytes() == b"\xff\xfe\x00\x01\x02\x03\x04\x05"


class TestInsert:
    def test_insert_string(self, text_file: Path):
        insert(text_file, "Start: ", position=0)
        assert text_file.read_text(encoding="utf-8") == "Start: Hello, World!"

    def test_insert_bytes(self, binary_file: Path):
        insert(binary_file, b"\xff\xfe", position=3)
        assert binary_file.read_bytes() == b"\x00\x01\x02\xff\xfe\x03\x04\x05"

    def test_insert_default_position(self, text_file: Path):
        insert(text_file, "Prefix: ")
        assert text_file.read_text(encoding="utf-8") == "Prefix: Hello, World!"


class TestIntegration:
    def test_write_then_read_string(self, tmp_path: Path):
        file = tmp_path / "roundtrip.txt"
        original = "Test content with special chars: é ñ ü"
        write_string(file, original)
        result = read_string(file)
        assert result == original

    def test_write_then_read_binary(self, tmp_path: Path):
        file = tmp_path / "roundtrip.bin"
        original = bytes(range(256))
        write_binary(file, original)
        result = read_binary(file)
        assert result == original

    def test_multiple_appends(self, tmp_path: Path):
        file = tmp_path / "appends.txt"
        write_string(file, "A")
        append_string(file, "B")
        append_string(file, "C")
        append_string(file, "D")
        assert read_string(file) == "ABCD"

    def test_write_overwrite_append_cycle(self, tmp_path: Path):
        file = tmp_path / "cycle.txt"
        write_string(file, "Initial")
        append_string(file, " Added")
        write_string(file, "Overwritten", overwrite=True)
        append_string(file, " Again")
        assert read_string(file) == "Overwritten Again"

    def test_insert_multiple_positions(self, tmp_path: Path):
        file = tmp_path / "inserts.txt"
        write_string(file, "AC")
        insert_string(file, "B", position=1)
        assert read_string(file) == "ABC"
        insert_string(file, "0", position=0)
        assert read_string(file) == "0ABC"
        insert_string(file, "D", position=4)
        assert read_string(file) == "0ABCD"
