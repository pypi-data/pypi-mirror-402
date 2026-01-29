import pytest
import alias_agent


def test_version():
    assert alias_agent.__version__ == "0.1.0"


def test_import():
    # Basic import test
    assert alias_agent is not None
