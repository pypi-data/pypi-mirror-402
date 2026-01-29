"""F3TS Hardware Utils Pytest Plugin Fixtures.

Various utility fixtures for accessing hardware APIs
"""
import logging

import pytest

from f3ts_hardware_utils.ffc import FixturCNTL

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def fixtur_cntl() -> FixturCNTL:
    """FixturCNTL Serial Interface Pytest Fixture

    Object for creating and sending requests to the FixturCNTL Serial
    Interface for interacting with the FixtureCNTL Board features
    """
    try:
        fixtur_cntl = FixturCNTL()
        fixtur_cntl.open()

        yield fixtur_cntl

        fixtur_cntl.close()

    except Exception as e:
        print("WARNING: Unable to connect to FixtureCNTL Board:", e)
