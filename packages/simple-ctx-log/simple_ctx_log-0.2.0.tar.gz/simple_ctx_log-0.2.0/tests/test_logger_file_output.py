import os
from simple_ctx_log import Logger


def test_log_written_to_file(tmp_path):
    log_file = tmp_path / "test.log"

    logger = Logger(log_file=str(log_file), stdout=False)
    logger.log("File output test")

    content = log_file.read_text(encoding="utf-8")

    assert "File output test" in content
