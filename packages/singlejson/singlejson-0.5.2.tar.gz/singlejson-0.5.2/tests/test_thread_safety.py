import json
import threading

from singlejson.fileutils import JSONFile


def worker_save(jf: JSONFile, key: str, value, iterations: int = 50):
    for _ in range(iterations):
        # modify then save; internals are responsible for thread-safety
        jf.json[key] = value
        jf.save()


def worker_reload(jf: JSONFile, iterations: int = 50):
    for _ in range(iterations):
        jf.reload(strict=True)


def test_concurrent_save_and_reload(tmp_path):
    p = tmp_path / "concurrent.json"
    jf = JSONFile(p, default_data={})

    t1 = threading.Thread(target=worker_save, args=(jf, "a", 1))
    t2 = threading.Thread(target=worker_save, args=(jf, "b", 2))
    t3 = threading.Thread(target=worker_reload, args=(jf,))

    # start threads
    t1.start()
    t2.start()
    t3.start()

    # wait for finish
    t1.join()
    t2.join()
    t3.join()

    # final reload to ensure file is readable
    jf.reload(strict=True)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_pool_thread_safety(tmp_path):
    # Create a scenario where multiple threads call pool.load() for the same path
    from singlejson.pool import load as pool_load
    from singlejson.pool import reset as pool_reset

    p = tmp_path / "pool.json"
    results = []

    # ensure pool is empty to avoid returning old instances
    pool_reset()

    def loader():
        jf = pool_load(p, default_data={})
        results.append(jf)

    threads = [threading.Thread(target=loader) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # all returned objects should be the same instance
    assert all(r is results[0] for r in results)
