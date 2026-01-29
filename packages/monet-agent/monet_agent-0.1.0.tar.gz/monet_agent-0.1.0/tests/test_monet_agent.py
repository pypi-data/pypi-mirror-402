import pytest
import monet_agent


def test_version():
    assert monet_agent.__version__ == "0.1.0"


def test_import():
    # Basic import test
    assert monet_agent is not None
