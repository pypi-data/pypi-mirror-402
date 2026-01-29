import json
from pathlib import Path

import pytest

from singlejson.fileutils import (
    DefaultNotJSONSerializableError,
    JSONDeserializationError,
    JSONFile,
)


def test_default_data_is_deepcopied(tmp_path: Path):
    path = tmp_path / "test.json"

    # Original mutable data
    default_data = {"nested": {"key": "value"}, "list": [1, 2, 3]}

    # Initialize JSONFile. Since file doesn't exist, it will use default_data
    jf = JSONFile(path, default_data=default_data)

    # Verify initial state
    assert jf.json == default_data
    assert jf.json is not default_data
    assert jf.json["nested"] is not default_data["nested"]
    assert jf.json["list"] is not default_data["list"]

    # Mutate original default_data
    default_data["nested"]["key"] = "changed"
    default_data["list"].append(4)

    # JSONFile's data should remain unchanged
    assert jf.json["nested"]["key"] == "value"
    assert jf.json["list"] == [1, 2, 3]

    # Even if we reload (it should still be the same on disk)
    jf.reload()
    assert jf.json["nested"]["key"] == "value"
    assert jf.json["list"] == [1, 2, 3]


def test_default_data_reinstantiation_is_consistent(tmp_path: Path):
    path = tmp_path / "test_reinstantiate.json"

    default_data = {"a": [1]}
    jf = JSONFile(path, default_data=default_data)

    # Delete file and reload to force reinstantiation from stored __default_data
    path.unlink()
    jf.reload()

    assert jf.json == {"a": [1]}

    # Mutate jf.json and then reload after unlinking again
    jf.json["a"].append(2)
    path.unlink()
    jf.reload()

    # Should still be the original default, not the mutated one
    assert jf.json == {"a": [1]}


def test_default_file_is_copied(tmp_path: Path):
    template = tmp_path / "template.json"
    content = {"hello": "world", "num": 5}
    with template.open("w", encoding="utf-8") as f:
        json.dump(content, f)

    dest = tmp_path / "dest.json"
    jf = JSONFile(dest, default_path=str(template))

    assert dest.exists()
    with dest.open("r", encoding="utf-8") as f:
        d = json.load(f)
    assert d == content
    assert jf.json == content


def test_strict_init(tmp_path: Path):
    valid = tmp_path / "valid.json"
    malformed = tmp_path / "malformed.json"
    valid.write_text('{"key": "value"}', encoding="utf-8")  # Valid JSON
    malformed.write_text('{"key": "value",}', encoding="utf-8")  # Malformed JSON

    # Should load fine
    jf_valid = JSONFile(valid, strict=True)
    assert jf_valid.json == {"key": "value"}

    # Should raise error on malformed with strict=True
    with pytest.raises(JSONDeserializationError):
        JSONFile(malformed, strict=True)

    # Should load fine with strict=False, reverting to default {}
    jf_malformed = JSONFile(malformed, strict=False)
    assert jf_malformed.json == {}

    # Test defaults
    default_data = "{'default_key': 'default_value',}"  # Malformed
    with pytest.raises(DefaultNotJSONSerializableError):
        JSONFile(valid, default_data=default_data, strict=True)

    malformed.write_text('{"key": "value",}', encoding="utf-8")  # Malformed JSON
    jf_with_data = JSONFile(malformed, default_data=default_data, strict=False)
    # Should not throw an error, fallback to empty since default is invalid JSON text
    assert jf_with_data.json == {}

    with pytest.raises(DefaultNotJSONSerializableError):
        JSONFile(valid, default_path="nonexistent.json", strict=True)

    malformed.write_text('{"key": "value",}', encoding="utf-8")  # Malformed JSON
    assert JSONFile(malformed, default_path="nonexistent.json", strict=False).json == {}

    malformed.write_text('{"key": "value",}', encoding="utf-8")  # Malformed JSON
    with pytest.raises(DefaultNotJSONSerializableError):
        JSONFile(valid, default_path=malformed, strict=True)

    malformed.write_text('{"key": "value",}', encoding="utf-8")  # Malformed JSON
    assert JSONFile(malformed, default_path=malformed, strict=False).json == {}
    # Since the file is malformed and strict mode is off, it should revert to default


def test_string_default_writes_json(tmp_path: Path):
    path = tmp_path / "string_default.json"
    default_data = '{"hello": "world", "num": 5}'

    jf = JSONFile(path, default_data=default_data)

    assert jf.json == {"hello": "world", "num": 5}
    # Ensure the file content is JSON object, not a quoted string
    with path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {"hello": "world", "num": 5}


def test_invalid_string_default_falls_back(tmp_path: Path):
    path = tmp_path / "invalid_string_default.json"
    default_data = '{"hello": "world",}'  # Invalid JSON text

    jf = JSONFile(path, default_data=default_data, strict=False)

    assert jf.json == {}
    with path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {}


def test_restore_default_strict_mode(tmp_path: Path):
    load = tmp_path / "load.json"
    malformed = tmp_path / "malformed.json"
    load.write_text('{"key": "value"}', encoding="utf-8")  # Valid JSON
    malformed.write_text('{"key": "value",}', encoding="utf-8")  # Malformed JSON

    malformed_default = "{'default_key': 'default_value',}"  # Malformed
    jf_with_data = JSONFile(load, default_data=malformed_default)  # Loading non strict

    with pytest.raises(DefaultNotJSONSerializableError):
        jf_with_data.restore_default(strict=True)

    jf_with_data.restore_default(strict=False)  # Should not throw an error
    assert jf_with_data.json == {}

    load.write_text('{"key": "value"}', encoding="utf-8")  # Valid JSON
    jf_with_no_path = JSONFile(load, default_path="nonexistent.json")
    with pytest.raises(DefaultNotJSONSerializableError):
        jf_with_no_path.restore_default(strict=True)

    jf_with_no_path.restore_default(strict=False)
    # Should not throw an error and revert to {}
    assert jf_with_no_path.json == {}

    load.write_text('{"key": "value"}', encoding="utf-8")  # Valid JSON
    jf_with_path = JSONFile(load, default_path=malformed)
    with pytest.raises(DefaultNotJSONSerializableError):
        jf_with_path.restore_default(strict=True)

    jf_with_path.restore_default(strict=False)
    # Should not throw an error and revert to {} since cannot set json to malformed
    assert jf_with_path.json == {}
