from simple_ctx_log import Logger


def test_logger_basic_call(capsys):
    logger = Logger()

    logger.log("hello world")

    captured = capsys.readouterr()
    output = captured.out

    assert "hello world" in output
    assert "[INFO]" in output
