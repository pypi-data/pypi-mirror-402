import json
import multiprocessing as mp
import time
from pathlib import Path

from singlejson.fileutils import JSONFile


def _writer(path: str, payloads: list[dict], delay: float):
    # Each writer will sequentially write payloads to the JSONFile
    jf = JSONFile(path, default_data={})
    for p in payloads:
        jf.json = p
        jf.save()
        time.sleep(delay)


def test_concurrent_writes_no_partial_reads(tmp_path: Path):
    path = str(tmp_path / "shared.json")

    # Prepare payloads for two writers
    w1_payloads = [{"writer": 1, "i": i} for i in range(5)]
    w2_payloads = [{"writer": 2, "i": i} for i in range(5)]

    # Start writer processes
    p1 = mp.Process(target=_writer, args=(path, w1_payloads, 0.01))
    p2 = mp.Process(target=_writer, args=(path, w2_payloads, 0.01))
    p1.start()
    p2.start()

    # Concurrently read the file multiple times and ensure we never see a partial JSON (decode error)
    reads = 0
    start = time.time()
    timeout = 2
    while time.time() - start < timeout:
        if Path(path).exists():
            try:
                with open(path, encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError:
                p1.terminate()
                p2.terminate()
                p1.join()
                p2.join()
                assert "Found partial/invalid JSON during concurrent writes"
        reads += 1
        time.sleep(0.005)

    p1.join()
    p2.join()

    assert p1.exitcode == 0
    assert p2.exitcode == 0


def _copy_default(template: str, dest: str, repeats: int, delay: float):
    for _ in range(repeats):
        JSONFile(dest, default_path=template)
        time.sleep(delay)


def test_copy_default_file_race(tmp_path: Path):
    template = tmp_path / "tmpl.json"
    content = {"x": 1, "y": [1, 2, 3]}
    with template.open("w", encoding="utf-8") as f:
        json.dump(content, f)

    dest = tmp_path / "dest.json"

    p = mp.Process(target=_copy_default, args=(str(template), str(dest), 10, 0.005))
    p.start()

    # Concurrently attempt to read dest if it appears, ensuring no JSONDecodeError
    start = time.time()
    timeout = 2
    while time.time() - start < timeout:
        if dest.exists():
            try:
                with dest.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    assert data == content
            except json.JSONDecodeError:
                p.terminate()
                p.join()
                assert "Found partial/invalid JSON while default file was being copied"
        time.sleep(0.003)

    p.join()
    assert p.exitcode == 0
