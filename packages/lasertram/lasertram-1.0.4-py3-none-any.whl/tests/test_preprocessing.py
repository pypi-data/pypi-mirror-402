"""
Tests for the lasertram.helpers.preprocessing module.

This module tests functionality for:
- Loading and preprocessing raw ICP-MS data from various instrument formats
- Creating LaserTRAM-ready data files from raw data
- Loading test/example data included with the package
"""

from pathlib import Path

import pytest

from lasertram import preprocessing


# Test data paths from conftest.py
RAW_THERMO_PATH = Path(__file__).parent / "raw" / "03152024_IODP_tephras4_1.csv"


class TestThermoDataProcessing:
    """Tests for processing Thermo Scientific ICP-MS raw data."""

    def test_extract_thermo_data_returns_expected_keys(self):
        """Test that extract_thermo_data returns dict with expected keys."""
        result = preprocessing.extract_thermo_data(RAW_THERMO_PATH)
        expected_keys = ["timestamp", "file", "sample", "data"]
        
        assert all(k in result.keys() for k in expected_keys), \
            f"Missing expected keys. Got: {result.keys()}"

    def test_make_lt_ready_file_shape(self):
        """Test that make_lt_ready_file creates correct DataFrame shape."""
        df = preprocessing.make_lt_ready_file(RAW_THERMO_PATH, quad_type="thermo")
        
        assert df.shape == (194, 35), "DataFrame not the right shape"

    def test_make_lt_ready_file_columns(self):
        """Test that make_lt_ready_file creates correct columns."""
        df = preprocessing.make_lt_ready_file(RAW_THERMO_PATH, quad_type="thermo")
        
        expected_columns = [
            "timestamp",
            "SampleLabel",
            "Time",
            "7Li",
            "29Si",
            "31P",
            "43Ca",
            "45Sc",
            "47Ti",
            "51V",
            "55Mn",
            "65Cu",
            "66Zn",
            "85Rb",
            "88Sr",
            "89Y",
            "90Zr",
            "93Nb",
            "133Cs",
            "137Ba",
            "139La",
            "140Ce",
            "141Pr",
            "146Nd",
            "147Sm",
            "153Eu",
            "157Gd",
            "163Dy",
            "166Er",
            "172Yb",
            "178Hf",
            "181Ta",
            "208Pb",
            "232Th",
            "238U",
        ]
        assert df.columns.to_list() == expected_columns, "Columns not correct"


class TestFolderProcessing:
    """Tests for processing folders of raw data files."""

    def test_make_lt_ready_folder_shape(self):
        """Test that make_lt_ready_folder creates correct DataFrame shape."""
        df = preprocessing.make_lt_ready_folder(
            RAW_THERMO_PATH.parent, quad_type="thermo"
        )
        
        assert df.shape == (973, 35), "DataFrame not the right shape"

    def test_make_lt_ready_folder_columns(self):
        """Test that make_lt_ready_folder creates correct columns."""
        df = preprocessing.make_lt_ready_folder(
            RAW_THERMO_PATH.parent, quad_type="thermo"
        )
        
        expected_columns = [
            "timestamp",
            "SampleLabel",
            "Time",
            "7Li",
            "29Si",
            "31P",
            "43Ca",
            "45Sc",
            "47Ti",
            "51V",
            "55Mn",
            "65Cu",
            "66Zn",
            "85Rb",
            "88Sr",
            "89Y",
            "90Zr",
            "93Nb",
            "133Cs",
            "137Ba",
            "139La",
            "140Ce",
            "141Pr",
            "146Nd",
            "147Sm",
            "153Eu",
            "157Gd",
            "163Dy",
            "166Er",
            "172Yb",
            "178Hf",
            "181Ta",
            "208Pb",
            "232Th",
            "238U",
        ]
        assert df.columns.to_list() == expected_columns, "Columns not correct"


class TestLoadTestData:
    """Tests for loading example/test data included with the package."""

    def test_load_test_rawdata_shape(self):
        """Test that load_test_rawdata returns correct DataFrame shape."""
        raw_data = preprocessing.load_test_rawdata()
        
        assert raw_data.shape == (27434, 34), "Raw data not the right shape"

    def test_load_test_rawdata_columns(self):
        """Test that load_test_rawdata returns correct columns."""
        raw_data = preprocessing.load_test_rawdata()
        
        expected_columns = [
            "timestamp",
            "Time",
            "7Li",
            "29Si",
            "31P",
            "43Ca",
            "45Sc",
            "47Ti",
            "51V",
            "55Mn",
            "65Cu",
            "66Zn",
            "85Rb",
            "88Sr",
            "89Y",
            "90Zr",
            "93Nb",
            "133Cs",
            "137Ba",
            "139La",
            "140Ce",
            "141Pr",
            "146Nd",
            "147Sm",
            "153Eu",
            "157Gd",
            "163Dy",
            "166Er",
            "172Yb",
            "178Hf",
            "181Ta",
            "208Pb",
            "232Th",
            "238U",
        ]
        assert raw_data.columns.to_list() == expected_columns

    def test_load_test_intervals_shape(self):
        """Test that load_test_intervals returns correct DataFrame shape."""
        intervals = preprocessing.load_test_intervals()
        
        assert intervals.shape == (168, 2), "Intervals DataFrame wrong shape"

    def test_load_test_intervals_columns(self):
        """Test that load_test_intervals returns correct columns."""
        intervals = preprocessing.load_test_intervals()
        
        assert intervals.columns.to_list() == ["int_start", "int_stop"]

    def test_load_test_int_std_comps_shape(self):
        """Test that load_test_int_std_comps returns correct DataFrame shape."""
        int_std_comps = preprocessing.load_test_int_std_comps()
        
        assert int_std_comps.shape == (131, 3), "Internal std comps wrong shape"

    def test_load_test_int_std_comps_columns(self):
        """Test that load_test_int_std_comps returns correct columns."""
        int_std_comps = preprocessing.load_test_int_std_comps()
        
        assert int_std_comps.columns.to_list() == ["Spot", "SiO2", "SiO2_std%"]
