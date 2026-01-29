from simple_ctx_log import Logger


def test_logger_called_from_class_method(capsys):
    logger = Logger()

    class MyClass:
        def my_method(self):
            logger.log("from class method")

    MyClass().my_method()

    captured = capsys.readouterr()
    output = captured.out

    assert "from class method" in output
    assert "MyClass" in output
    assert "my_method" in output
