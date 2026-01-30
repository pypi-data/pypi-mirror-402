"""
Shared pytest fixtures for lasertram tests.

This module contains fixtures that are shared across multiple test modules.
"""

from pathlib import Path

import pandas as pd
import pytest


# ============================================================================
# Test data paths
# ============================================================================
TEST_DIR = Path(__file__).parent

# LaserTRAM test data
SPREADSHEET_PATH = TEST_DIR / "2022-05-10_LT_ready.xlsx"
RAW_THERMO_PATH = TEST_DIR / "raw" / "03152024_IODP_tephras4_1.csv"

# LaserCalc test data
SRM_PATH = TEST_DIR / "laicpms_stds_tidy.xlsx"
INTERVALS_PATH = TEST_DIR / "example_intervals.xlsx"
INTERNAL_STD_PATH = TEST_DIR / "example_internal_std.xlsx"
LT_COMPLETE_PATH = TEST_DIR / "example_lt_complete.xlsx"


# ============================================================================
# Common test parameters
# ============================================================================
pytest.bkgd_interval = (5, 10)
pytest.keep_interval = (25, 40)
pytest.omit_interval = (30, 33)
pytest.int_std = "29Si"


# ============================================================================
# LaserTRAM fixtures
# ============================================================================
@pytest.fixture
def load_data():
    """Load LaserTRAM-ready data for testing."""
    data = pd.read_excel(SPREADSHEET_PATH).set_index("SampleLabel")
    return data


# ============================================================================
# LaserCalc fixtures
# ============================================================================
@pytest.fixture
def load_SRM_data():
    """Load standard reference material compositions."""
    data = pd.read_excel(SRM_PATH)
    return data


@pytest.fixture
def load_intervals():
    """Load example intervals data."""
    intervals = pd.read_excel(INTERVALS_PATH).set_index("Spot")
    return intervals


@pytest.fixture
def load_internal_std_comps():
    """Load internal standard compositions."""
    internal_std_comps = pd.read_excel(INTERNAL_STD_PATH)
    return internal_std_comps


@pytest.fixture
def load_LTcomplete_data():
    """Load LaserTRAM-complete data for LaserCalc testing."""
    data = pd.read_excel(LT_COMPLETE_PATH)
    return data
