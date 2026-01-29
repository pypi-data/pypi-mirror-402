# pyeio

- Description: Drop-in replacement for standard `io` module with some extra utilities.
- Purpose: Solves having to constantly `with open` stuff.
- Notes: Full docs may be added at some later point, along with some other file formats perhaps.

## Install

```sh
pip install pyeio
```

or

```sh
uv add pyeio
```

## Usage

```python
import pyeio as io
```

Everything should work the same as `io`, but with the following additions:

### Extra IO Functions

#### `io.read`

Read file content as string (utf-8) or bytes.

```python
# Read as string (default)
content = io.read("file.txt")

# Read as bytes
data = io.read("file.bin", bytes)
```

#### `io.write`

Write string or bytes to a file. Raises an error if the file already exists unless `overwrite=True`.

```python
# Write string
io.write("file.txt", "Hello, world!")

# Write bytes
io.write("file.bin", b"\x00\x01\x02")

# Overwrite existing file
io.write("file.txt", "New content", overwrite=True)
```

#### `io.append`

Append string or bytes to the end of a file.

```python
# Append string
io.append("file.txt", "\nAnother line")

# Append bytes
io.append("file.bin", b"\x03\x04")
```

### Formats

Additionally, `json`, `toml`, and `yaml` are included, with overloads/generics for handling pydantic models. Each of these exposes a `read`, and `write` function which more or less works the exact same way, along with a `parse` and `serialize` function.

Here are some examples:

```python
# Read JSON file
data = io.json.read("config.json")

# Read JSON file into a Pydantic model
user = io.json.read("user.json", UserModel)

# Write JSON to file
io.json.write("output.json", {"key": "value"})

# Write with pretty printing
io.json.write("output.json", data, overwrite=True, indent=True)

# Parse JSON string/bytes
data = io.json.parse('{"key": "value"}')
user = io.json.parse(json_bytes, UserModel)

# Serialize to string/bytes
json_bytes = io.json.serialize(data)  # returns bytes by default
json_str = io.json.serialize(data, str)
```