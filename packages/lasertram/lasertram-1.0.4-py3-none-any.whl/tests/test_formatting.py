"""
Tests for lasertram.helpers.formatting module

Tests the format validation functions used to check input data formats
for LaserTRAM, LaserCalc, and SRM database uploads.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from lasertram.helpers import formatting, preprocessing


# Use the same test data paths as the main test file
SRM_path = Path(__file__).parent / "laicpms_stds_tidy.xlsx"
LT_complete_path = Path(__file__).parent / "example_lt_complete.xlsx"


class TestCheckCols:
    """Tests for _check_cols helper function"""

    def test_all_columns_present_returns_none(self):
        """When all required columns are present, should return None"""
        in_cols = ['A', 'B', 'C', 'D']
        correct_cols = ['A', 'B', 'C']
        result = formatting._check_cols(in_cols, correct_cols)
        assert result is None

    def test_missing_columns_returns_list(self):
        """When columns are missing, should return list of missing columns"""
        in_cols = ['A', 'B']
        correct_cols = ['A', 'B', 'C', 'D']
        result = formatting._check_cols(in_cols, correct_cols)
        assert result == ['C', 'D']

    def test_empty_input_returns_all_required(self):
        """When input is empty, should return all required columns"""
        in_cols = []
        correct_cols = ['A', 'B', 'C']
        result = formatting._check_cols(in_cols, correct_cols)
        assert result == ['A', 'B', 'C']

    def test_extra_columns_ignored(self):
        """Extra columns in input should be ignored"""
        in_cols = ['A', 'B', 'C', 'Extra1', 'Extra2']
        correct_cols = ['A', 'B', 'C']
        result = formatting._check_cols(in_cols, correct_cols)
        assert result is None


class TestCheckColTypes:
    """Tests for _check_col_types helper function"""

    def test_datetime_type_valid(self):
        """Valid datetime column should pass"""
        df = pd.DataFrame({
            'date_col': pd.to_datetime(['2024-01-01', '2024-01-02'])
        })
        result = formatting._check_col_types(df, ['datetime'])
        assert result is None

    def test_datetime_type_invalid(self):
        """Invalid datetime column should fail"""
        df = pd.DataFrame({
            'date_col': ['not_a_date', 'also_not_a_date']
        })
        result = formatting._check_col_types(df, ['datetime'])
        assert result == [0]

    def test_string_type_valid(self):
        """Valid string column should pass"""
        df = pd.DataFrame({
            'str_col': ['hello', 'world']
        })
        result = formatting._check_col_types(df, ['str'])
        assert result is None

    def test_string_type_invalid(self):
        """Numeric column should fail string check"""
        df = pd.DataFrame({
            'num_col': [1, 2, 3]
        })
        result = formatting._check_col_types(df, ['str'])
        assert result == [0]

    def test_float_type_valid(self):
        """Valid numeric column should pass float check"""
        df = pd.DataFrame({
            'float_col': [1.5, 2.5, 3.5]
        })
        result = formatting._check_col_types(df, ['float'])
        assert result is None

    def test_float_type_valid_with_integers(self):
        """Integer column should also pass float check (is_numeric_dtype)"""
        df = pd.DataFrame({
            'int_col': [1, 2, 3]
        })
        result = formatting._check_col_types(df, ['float'])
        assert result is None

    def test_float_type_invalid(self):
        """String column should fail float check"""
        df = pd.DataFrame({
            'str_col': ['a', 'b', 'c']
        })
        result = formatting._check_col_types(df, ['float'])
        assert result == [0]

    def test_bool_type_valid(self):
        """Valid boolean column should pass"""
        df = pd.DataFrame({
            'bool_col': [True, False, True]
        })
        result = formatting._check_col_types(df, ['bool'])
        assert result is None

    def test_bool_type_invalid(self):
        """String column should fail bool check"""
        df = pd.DataFrame({
            'str_col': ['true', 'false']
        })
        result = formatting._check_col_types(df, ['bool'])
        assert result == [0]

    def test_multiple_columns_all_valid(self):
        """Multiple columns all valid should return None"""
        df = pd.DataFrame({
            'date_col': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'str_col': ['hello', 'world'],
            'float_col': [1.5, 2.5],
            'bool_col': [True, False]
        })
        result = formatting._check_col_types(df, ['datetime', 'str', 'float', 'bool'])
        assert result is None

    def test_multiple_columns_some_invalid(self):
        """Should return indices of invalid columns"""
        df = pd.DataFrame({
            'col1': pd.to_datetime(['2024-01-01', '2024-01-02']),  # valid datetime
            'col2': [1, 2],  # invalid for str (numeric)
            'col3': [1.5, 2.5],  # valid float
        })
        result = formatting._check_col_types(df, ['datetime', 'str', 'float'])
        # col2 (index 1) should fail string check
        assert result is not None
        assert 1 in result

    def test_unknown_type_fails(self):
        """Unknown type should be added to incorrect types"""
        df = pd.DataFrame({
            'col1': [1, 2, 3]
        })
        result = formatting._check_col_types(df, ['unknown_type'])
        assert result == [0]


class TestCheckLtInputFormat:
    """Tests for check_lt_input_format function using real test data"""

    def test_valid_lt_ready_data(self):
        """Valid LT ready data should pass all checks"""
        raw_data = preprocessing.load_test_rawdata()
        # Reset index to get SampleLabel as a column
        df = raw_data.reset_index()
        
        col_check, type_check = formatting.check_lt_input_format(df)
        
        assert col_check is None, f"Column check failed: {col_check}"
        assert type_check is None, f"Type check failed: {type_check}"

    def test_missing_timestamp_column(self):
        """Data missing timestamp column should fail"""
        df = pd.DataFrame({
            'SampleLabel': ['test1', 'test2'],
            'Time': [1.0, 2.0],
            '29Si': [100.0, 200.0]
        })
        col_check, type_check = formatting.check_lt_input_format(df)
        
        assert col_check is not None
        assert 'timestamp' in col_check

    def test_missing_time_column(self):
        """Data missing Time column should fail"""
        df = pd.DataFrame({
            'SampleLabel': ['test1', 'test2'],
            'timestamp': pd.to_datetime(['2024-01-01', '2024-01-02']),
            '29Si': [100.0, 200.0]
        })
        col_check, type_check = formatting.check_lt_input_format(df)
        
        assert col_check is not None
        assert 'Time' in col_check

    def test_wrong_timestamp_type(self):
        """Data with wrong timestamp type should fail type check"""
        df = pd.DataFrame({
            'SampleLabel': ['test1', 'test2'],
            'timestamp': ['not_a_date', 'also_not_a_date'],  # Should be datetime
            'Time': [1.0, 2.0],
            '29Si': [100.0, 200.0]
        })
        col_check, type_check = formatting.check_lt_input_format(df)
        
        # Column names are correct
        assert col_check is None
        # But types are wrong
        assert type_check is not None


class TestCheckLtCompleteFormat:
    """Tests for check_lt_complete_format function using real test data"""

    def test_valid_lt_complete_data(self):
        """Valid LT complete data should pass all checks"""
        data = pd.read_excel(LT_complete_path)
        
        col_check, type_check = formatting.check_lt_complete_format(data)
        
        assert col_check is None, f"Column check failed: {col_check}"
        assert type_check is None, f"Type check failed: {type_check}"

    def test_missing_spot_column(self):
        """Data missing Spot column should fail"""
        # Need all 11 columns that check_lt_complete_format expects to index
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(['2024-01-01']),
            'NOT_Spot': ['test'],  # Wrong column name
            'despiked': ['None'],
            'omitted_region': ['None'],
            'bkgd_start': [0.0],
            'bkgd_stop': [1.0],
            'int_start': [2.0],
            'int_stop': [3.0],
            'norm': ['29Si'],
            'norm_cps': [1000.0],
            '29Si': [100.0],  # Analyte column
        })
        col_check, type_check = formatting.check_lt_complete_format(df)
        
        assert col_check is not None
        assert 'Spot' in col_check


class TestCheckSrmFormat:
    """Tests for check_srm_format function using real test data"""

    def test_valid_srm_data(self):
        """Valid SRM data should pass all checks"""
        data = pd.read_excel(SRM_path)
        
        col_check, type_check = formatting.check_srm_format(data)
        
        assert col_check is None, f"Column check failed: {col_check}"
        assert type_check is None, f"Type check failed: {type_check}"


class TestCheckDuplicateValues:
    """Tests for check_duplicate_values function"""

    def test_no_duplicates_returns_none(self):
        """When no duplicates exist, should return None"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample2', 'sample3'],
            'value': [1, 2, 3]
        })
        result = formatting.check_duplicate_values(df, 'name', print_output=False)
        assert result is None

    def test_duplicates_returns_series(self):
        """When duplicates exist, should return Series with duplicates"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample2', 'sample1', 'sample3'],
            'value': [1, 2, 3, 4]
        })
        result = formatting.check_duplicate_values(df, 'name', print_output=False)
        
        assert result is not None
        assert len(result) == 2  # Two rows have 'sample1'
        assert all(val == 'sample1' for val in result.values)

    def test_multiple_duplicate_groups(self):
        """Should find all duplicate groups"""
        df = pd.DataFrame({
            'name': ['A', 'B', 'A', 'B', 'C'],
            'value': [1, 2, 3, 4, 5]
        })
        result = formatting.check_duplicate_values(df, 'name', print_output=False)
        
        assert result is not None
        assert len(result) == 4  # A appears twice, B appears twice

    def test_invalid_column_raises(self):
        """Should raise AssertionError for non-existent column"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample2'],
            'value': [1, 2]
        })
        with pytest.raises(AssertionError, match="is not in the input dataframe columns"):
            formatting.check_duplicate_values(df, 'nonexistent', print_output=False)

    def test_invalid_df_type_raises(self):
        """Should raise AssertionError for non-DataFrame input"""
        with pytest.raises(AssertionError, match="df must be a pandas dataframe"):
            formatting.check_duplicate_values("not a dataframe", 'col', print_output=False)

    def test_invalid_print_output_type_raises(self):
        """Should raise AssertionError for non-boolean print_output"""
        df = pd.DataFrame({'name': ['a', 'b']})
        with pytest.raises(AssertionError, match="print_output must be boolean"):
            formatting.check_duplicate_values(df, 'name', print_output="yes")

    def test_with_print_output_true(self, capsys):
        """Should print output when print_output=True and duplicates found"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample1'],
            'value': [1, 2]
        })
        formatting.check_duplicate_values(df, 'name', print_output=True)
        captured = capsys.readouterr()
        assert "duplicate sample names found" in captured.out

    def test_with_print_output_true_no_duplicates(self, capsys):
        """Should print 'no duplicates' message when print_output=True"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample2'],
            'value': [1, 2]
        })
        formatting.check_duplicate_values(df, 'name', print_output=True)
        captured = capsys.readouterr()
        assert "No duplicate values" in captured.out


class TestRenameDuplicateValues:
    """Tests for rename_duplicate_values function"""

    def test_renames_duplicates_correctly(self):
        """Should append -a, -b, etc. to duplicate values"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample2', 'sample1'],
            'value': [1, 2, 3]
        })
        result = formatting.rename_duplicate_values(df, 'name', print_output=False)
        
        assert 'sample1-a' in result['name'].values
        assert 'sample1-b' in result['name'].values
        assert 'sample2' in result['name'].values  # Non-duplicate unchanged

    def test_no_duplicates_returns_unmodified_copy(self):
        """When no duplicates, should return copy of original"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample2', 'sample3'],
            'value': [1, 2, 3]
        })
        result = formatting.rename_duplicate_values(df, 'name', print_output=False)
        
        assert result['name'].tolist() == ['sample1', 'sample2', 'sample3']

    def test_does_not_modify_original(self):
        """Should not modify the original DataFrame"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample1'],
            'value': [1, 2]
        })
        original_names = df['name'].tolist()
        formatting.rename_duplicate_values(df, 'name', print_output=False)
        
        assert df['name'].tolist() == original_names

    def test_multiple_duplicate_groups(self):
        """Should handle multiple groups of duplicates"""
        df = pd.DataFrame({
            'name': ['A', 'B', 'A', 'B', 'C'],
            'value': [1, 2, 3, 4, 5]
        })
        result = formatting.rename_duplicate_values(df, 'name', print_output=False)
        
        names = result['name'].tolist()
        assert 'A-a' in names
        assert 'A-b' in names
        assert 'B-a' in names
        assert 'B-b' in names
        assert 'C' in names

    def test_invalid_column_raises(self):
        """Should raise AssertionError for non-existent column"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample2'],
            'value': [1, 2]
        })
        with pytest.raises(AssertionError, match="is not in the input dataframe columns"):
            formatting.rename_duplicate_values(df, 'nonexistent', print_output=False)

    def test_invalid_df_type_raises(self):
        """Should raise AssertionError for non-DataFrame input"""
        with pytest.raises(AssertionError, match="df must be a pandas dataframe"):
            formatting.rename_duplicate_values("not a dataframe", 'col', print_output=False)

    def test_with_print_output_true(self, capsys):
        """Should print renaming info when print_output=True"""
        df = pd.DataFrame({
            'name': ['sample1', 'sample1'],
            'value': [1, 2]
        })
        formatting.rename_duplicate_values(df, 'name', print_output=True)
        captured = capsys.readouterr()
        assert "Rename" in captured.out
