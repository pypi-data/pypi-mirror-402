from simple_ctx_log import Logger


def test_logger_called_from_function(capsys):
    logger = Logger()

    def my_function():
        logger.log("from function")

    my_function()

    captured = capsys.readouterr()
    output = captured.out

    assert "from function" in output
    assert "my_function" in output
    assert "test_logger_function" in output
