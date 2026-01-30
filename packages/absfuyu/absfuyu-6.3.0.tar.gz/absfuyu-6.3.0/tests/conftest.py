"""
Global fixture

Version: 6.3.0
Date updated: 17/01/2026 (dd/mm/yyyy)
"""

import pytest


@pytest.fixture(scope="session")
def test_fixture_session():
    """This cache the fixture for current test session"""
    return None
