from simple_ctx_log import Logger


def abyss_factory(name, logger):
    class ExternalArchitect:
        def __init__(self, creator):
            self.creator = creator
            self.data = "Data"
            self._data = "Secret data"

        class InternProcess:
            def __init__(self, parent):
                self.parent = parent

            def recursive_log_call(self, depth, msg):
                # We descend into recursion for the pleasure of nesting.
                if depth > 0:
                    self.recursive_log_call(depth - 1, msg)
                else:
                    logger.log(f"Retrieved message : {msg}")

        def init_process(self):
            processeur = self.InternProcess(self)
            return processeur

    return ExternalArchitect(name)


def test_logger_called_from_function(capsys):
    logger = Logger()

    systeme = abyss_factory("Hell", logger)
    processeur_final = systeme.init_process()
    processeur_final.recursive_log_call(depth=3, msg="Entropy is inevitable.")

    captured = capsys.readouterr()
    output = captured.out

    assert output != ""
    assert "[INFO]" in output
    assert "Retrieved message : Entropy is inevitable." in output
    assert "InternProcess" in output
    assert "ExternalArchitect" in output
    assert "recursive_log_call" in output
    assert "depth=0" in output
    assert "creator = 'Hell'" in output
    assert "parent = <ExternalArchitect>" in output

    print(output)
