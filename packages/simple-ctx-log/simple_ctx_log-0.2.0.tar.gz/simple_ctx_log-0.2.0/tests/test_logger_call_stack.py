from simple_ctx_log import Logger


def factory(name, logger):
    class Outer:
        def __init__(self, value):
            self.value = value

        class Inner:
            def __init__(self, parent):
                self.parent = parent

            def recurse(self, depth):
                if depth > 0:
                    self.recurse(depth - 1)
                else:
                    logger.log("Deep message")

        def build(self):
            return self.Inner(self)

    return Outer(name)


def test_call_stack_order(capsys):
    logger = Logger(max_depth=5)

    root = factory("ROOT", logger)
    proc = root.build()
    proc.recurse(3)

    output = capsys.readouterr().out

    assert "test_call_stack_order" in output
    assert "factory" not in output  # because factory is no longer in the call stack
    assert "recurse(depth=1" in output or "recurse(depth=0" in output
    assert "Deep message" in output
