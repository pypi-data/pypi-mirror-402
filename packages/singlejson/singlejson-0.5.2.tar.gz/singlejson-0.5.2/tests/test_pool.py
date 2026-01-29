import json

from singlejson.fileutils import JSONFile
from singlejson.pool import load, reset, sync


def test_pool(tmp_path):
    path = tmp_path.joinpath("test.json").__str__()
    jsonfile = load(
        path, default_data={"test": "successful", "other_types": [True, 1, {}]}
    )
    assert jsonfile.json["test"] == "successful", "should be successful"
    jsonfile.json["test"] = "unsuccessful"
    assert load(path).json["test"] == "unsuccessful", (
        "should be unsuccessful since it should access the local copy."
    )
    assert (
        JSONFile(path, default_data={"test": "unsuccessful"}).json["test"]
        == "successful"
    ), "should be successful since changes to pool should not have been saved."
    sync()
    assert (
        JSONFile(path, default_data={"test": "successful"}).json["test"]
        == "unsuccessful"
    ), "should be unsuccessful since changes to pool should have been saved."


def test_pool_load_preserve(tmp_path):
    path = tmp_path / "pool.json"
    path.write_text("{ invalid json", encoding="utf-8")
    reset()

    jf = load(path, default_data={"ok": True}, preserve=True, strict=False)

    assert jf.json == {"ok": True}
    assert json.loads(path.read_text(encoding="utf-8")) == {"ok": True}
    preserved = tmp_path / "pool.old.1.json"
    assert preserved.exists()
    assert preserved.read_text(encoding="utf-8") == "{ invalid json"
    reset()
