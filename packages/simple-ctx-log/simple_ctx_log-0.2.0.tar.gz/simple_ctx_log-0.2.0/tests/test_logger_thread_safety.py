import threading
from simple_ctx_log import Logger


def test_thread_safe_logging(tmp_path):
    log_file = tmp_path / "thread.log"
    logger = Logger(log_file=str(log_file), stdout=False)

    def worker(idx):
        logger.log(f"Message {idx}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    content = log_file.read_text(encoding="utf-8")

    for i in range(10):
        assert f"Message {i}" in content
