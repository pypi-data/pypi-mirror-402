"""
Unit and regression test for the QCANT package.
"""

# Import package, test suite, and other packages as needed
import sys

import pytest

import QCANT


def test_QCANT_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "QCANT" in sys.modules
