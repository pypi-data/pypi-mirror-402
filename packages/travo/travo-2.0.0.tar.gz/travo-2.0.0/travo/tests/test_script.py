import os
import pytest
from travo import script


def test_travo_version():
    exit_status = os.system("travo --version")
    assert exit_status == 0


def test_script_noargs():
    class A:
        name = "classA"
        version = "1.0"

        def f(self, x, y):
            return (x, y)

    a = A()
    with pytest.raises(SystemExit):
        script.CLI(a, args=[], usage="Print usage")
