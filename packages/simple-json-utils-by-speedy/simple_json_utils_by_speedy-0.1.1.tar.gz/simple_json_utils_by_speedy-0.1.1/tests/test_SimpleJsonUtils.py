import pytest
from SimpleJsonUtils.SimpleJsonUtils import *
from pathlib import Path

# ---------------- create_json_file ----------------
def test_create_json_file_creates_list(tmp_path):
    path = tmp_path / "test.json"
    create_json_file(path, list)

    assert path.exists()
    assert path.read_text() == "[]"

def test_create_json_file_creates_dict(tmp_path):
    path = tmp_path / "test.json"
    create_json_file(path, dict)

    assert path.exists()
    assert path.read_text() == "{}"

def test_create_json_file_wrong_type(tmp_path):
    path = tmp_path / "test.json"
    with pytest.raises(ValueError):
        create_json_file(path, int)

def test_create_json_file_wrong_extension(tmp_path):
    path = tmp_path / "test.txt"
    with pytest.raises(ValueError):
        create_json_file(path, list)

def test_create_json_file_creates_list(tmp_path):
    path = tmp_path / "test.json"
    create_json_file(path, list)

    assert path.exists()
    assert path.read_text() == "[]"


def test_create_json_file_wrong_extension(tmp_path):
    path = tmp_path / "test.txt"

    with pytest.raises(ValueError):
        create_json_file(path, list)



#-----------------Read json file ----------------------

def test_read_json_file_returns_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a": 1}', encoding="utf-8")

    data = read_json_file(path)

    assert isinstance(data, dict)
    assert data["a"] == 1

    
def test_read_json_file_returns_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a": 1}]', encoding="utf-8")

    data = read_json_file(path)

    assert isinstance(data, list)
    assert data[0].get("a") == 1

def test_read_json_file_empty_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[]',encoding="utf-8")

    data = read_json_file(path)

    assert isinstance(data, list)
    assert len(data) == 0

def test_read_json_file_wrong_extention(tmp_path):
    path = tmp_path / "test.jason"
    path.write_text('[]',encoding="utf-8")

    with pytest.raises(ValueError):
       read_json_file(path)

def test_read_json_file_not_exists(tmp_path):
    path = tmp_path / "test.json"
    with pytest.raises(FileNotFoundError):
       read_json_file(path)

def test_read_json_file_wrong_structure(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[',encoding="utf-8")

    with pytest.raises(ValueError):
       read_json_file(path)


# ---------------- append_to_json_file ----------------
def test_append_to_json_file_adds_to_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[]', encoding="utf-8")
    obj = {"a": 1}

    append_to_json_file(obj, path)
    data = read_json_file(path)
    assert isinstance(data, list)
    assert obj in data

def test_append_to_json_file_creates_list_from_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":1}', encoding="utf-8")
    obj = {"b":2}

    append_to_json_file(obj, path)
    data = read_json_file(path)
    assert isinstance(data, list)
    assert any(d.get("a") == 1 for d in data)
    assert any(d.get("b") == 2 for d in data)

def test_append_to_json_file_wrong_object(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[]', encoding="utf-8")
    with pytest.raises(ValueError):
        append_to_json_file([1,2], path)

# ---------------- overwrite_json_file ----------------
def test_overwrite_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[]', encoding="utf-8")
    data_to_overwrite = [{"a":1}]
    overwrite_json_file(path, data_to_overwrite)

    data = read_json_file(path)
    assert data == data_to_overwrite

def test_overwrite_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{}', encoding="utf-8")
    data_to_overwrite = {"a":1}
    overwrite_json_file(path, data_to_overwrite)

    data = read_json_file(path)
    assert data == data_to_overwrite

def test_overwrite_json_file_wrong_type(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[]', encoding="utf-8")
    with pytest.raises(ValueError):
        overwrite_json_file(path, 123)

# ---------------- edit_json_file ----------------
def test_edit_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    edit_json_file(path, "a", 1, "b", 2)

    data = read_json_file(path)
    assert data[0]["b"] == 2

def test_edit_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":1}', encoding="utf-8")
    edit_json_file(path, "a", 1, "b", 2)

    data = read_json_file(path)
    assert data["b"] == 2

def test_edit_json_file_not_found(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    with pytest.raises(ValueError):
        edit_json_file(path, "a", 999, "b", 2)

# ---------------- add_key_value_to_json_file ----------------
def test_add_key_value_to_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    add_key_value_to_json_file(path, "a", 1, "b", 2)

    data = read_json_file(path)
    assert data[0]["b"] == 2

def test_add_key_value_to_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":1}', encoding="utf-8")
    add_key_value_to_json_file(path, "a", 1, "b", 2)

    data = read_json_file(path)
    assert data["b"] == 2

def test_add_key_value_to_json_file_key_exists(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1, "b":2}]', encoding="utf-8")
    with pytest.raises(ValueError):
        add_key_value_to_json_file(path, "a", 1, "b", 3)

# ---------------- get_max_from_json_file ----------------
def test_get_max_from_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}, {"a":5}, {"a":3}]', encoding="utf-8")
    assert get_max_from_json_file(path, "a") == 5

def test_get_max_from_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":7}', encoding="utf-8")
    assert get_max_from_json_file(path, "a") == 7

def test_get_max_from_json_file_nonparsable(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":"x"}]', encoding="utf-8")
    with pytest.raises(ValueError):
        get_max_from_json_file(path, "a")

# ---------------- get_min_from_json_file ----------------
def test_get_min_from_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}, {"a":5}, {"a":3}]', encoding="utf-8")
    assert get_min_from_json_file(path, "a") == 1

def test_get_min_from_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":7}', encoding="utf-8")
    assert get_min_from_json_file(path, "a") == 7

def test_get_min_from_json_file_nonparsable(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":"x"}]', encoding="utf-8")
    with pytest.raises(ValueError):
        get_min_from_json_file(path, "a")

# ---------------- normalize_json_file ----------------
def test_normalize_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":1}', encoding="utf-8")
    normalize_json_file(path)
    data = read_json_file(path)
    assert isinstance(data, list)
    assert data[0]["a"] == 1

def test_normalize_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    normalize_json_file(path)
    data = read_json_file(path)
    assert isinstance(data, list)
    assert data[0]["a"] == 1

# ---------------- remove_dict_from_json_file ----------------
def test_remove_dict_from_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}, {"a":2}]', encoding="utf-8")
    remove_dict_from_json_file(path, "a", 1)
    data = read_json_file(path)
    assert all(d["a"] != 1 for d in data)

def test_remove_dict_from_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":1}', encoding="utf-8")
    remove_dict_from_json_file(path, "a", 1)
    data = read_json_file(path)
    assert data == {}

def test_remove_dict_from_json_file_not_found(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    with pytest.raises(ValueError):
        remove_dict_from_json_file(path, "a", 999)

# ---------------- exists_in_json_file ----------------
def test_exists_in_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    assert exists_in_json_file(path, "a", 1) is True
    assert exists_in_json_file(path, "a", 999) is False

def test_exists_in_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":1}', encoding="utf-8")
    assert exists_in_json_file(path, "a", 1) is True
    assert exists_in_json_file(path, "a", 999) is False

# ---------------- get_value_from_json_file ----------------
def test_get_value_from_json_file_list(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1, "b":2}]', encoding="utf-8")
    val = get_value_from_json_file(path, "a", 1, "b")
    assert val == 2

def test_get_value_from_json_file_dict(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a":1, "b":2}', encoding="utf-8")
    val = get_value_from_json_file(path, "a", 1, "b")
    assert val == 2

def test_get_value_from_json_file_not_found(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    with pytest.raises(ValueError):
        get_value_from_json_file(path, "a", 1, "b")
