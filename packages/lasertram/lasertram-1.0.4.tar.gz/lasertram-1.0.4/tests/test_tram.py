"""
Tests for the lasertram.tram.tram module (LaserTRAM class).

This module tests functionality for:
- Loading and validating LA-ICP-MS time-series data
- Background signal determination and subtraction
- Signal interval selection and region omission
- Data normalization to internal standard
- Detection limit calculations
- Despiking (outlier removal)
- Output report generation
"""

import numpy as np
import pandas as pd
import pytest

from lasertram import LaserTRAM


class TestGetData:
    """Tests for LaserTRAM.get_data() method."""

    def test_get_data_loads_correctly(self, load_data):
        """Check whether or not data are loaded in properly."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()
        
        spot.get_data(load_data.loc[samples[0], :])
        df_to_check = spot.data.copy()
        df_to_check["Time"] = df_to_check["Time"] * 1000

        # Check that input data matches stored data
        pd.testing.assert_frame_equal(df_to_check, load_data.loc[samples[0], :])

    def test_get_data_missing_columns_raises_valueerror(self):
        """Test that missing required columns raises ValueError."""
        spot = LaserTRAM(name="test")
        
        bad_data = pd.DataFrame({
            "SampleLabel": ["test_sample"],
            "SomeOtherCol": [100],
        })
        
        with pytest.raises(ValueError, match="missing the following required columns"):
            spot.get_data(bad_data)

    def test_get_data_wrong_types_raises_typeerror(self, load_data):
        """Test that incorrect column types raises TypeError."""
        samples = load_data.index.unique().dropna().tolist()
        good_data = load_data.loc[samples[0], :].copy()
        
        # Corrupt the timestamp column to be a non-datetime type
        good_data["timestamp"] = 12345.0
        
        spot = LaserTRAM(name="test")
        
        with pytest.raises(TypeError, match="incorrect types"):
            spot.get_data(good_data)

    def test_get_data_time_units_seconds(self, load_data):
        """Test that time_units='s' does not modify Time column."""
        samples = load_data.index.unique().dropna().tolist()
        sample_data = load_data.loc[samples[0], :].copy()
        
        original_time = sample_data["Time"].values.copy()
        
        spot = LaserTRAM(name="test")
        spot.get_data(sample_data, time_units="s")
        
        np.testing.assert_array_equal(
            spot.data["Time"].values,
            original_time,
            err_msg="time_units='s' should not modify Time values"
        )

    def test_get_data_time_units_milliseconds(self, load_data):
        """Test that time_units='ms' divides Time by 1000."""
        samples = load_data.index.unique().dropna().tolist()
        sample_data = load_data.loc[samples[0], :].copy()
        
        original_time = sample_data["Time"].values.copy()
        
        spot = LaserTRAM(name="test")
        spot.get_data(sample_data, time_units="ms")
        
        np.testing.assert_allclose(
            spot.data["Time"].values,
            original_time / 1000,
            err_msg="time_units='ms' should divide Time by 1000"
        )


class TestAssignIntStd:
    """Tests for LaserTRAM.assign_int_std() method."""

    def test_assign_int_std(self, load_data):
        """Test that the internal standard is set correctly."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()

        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std(pytest.int_std)

        assert spot.int_std == pytest.int_std, \
            f"The internal standard should be {pytest.int_std}"


class TestAssignIntervals:
    """Tests for LaserTRAM.assign_intervals() method."""

    def test_assign_intervals_with_omit(self, load_data):
        """Test that intervals are assigned correctly with omission region."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()

        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std(pytest.int_std)
        spot.assign_intervals(
            bkgd=pytest.bkgd_interval, 
            keep=pytest.keep_interval, 
            omit=pytest.omit_interval
        )

        assert spot.bkgd_start == pytest.bkgd_interval[0], "bkgd_start should be 5"
        assert spot.bkgd_stop == pytest.bkgd_interval[1], "bkgd_stop should be 10"
        assert spot.int_start == pytest.keep_interval[0], "int_start should be 25"
        assert spot.int_stop == pytest.keep_interval[1], "int_stop should be 40"
        assert spot.omit_start == pytest.omit_interval[0], "omit_start should be 30"
        assert spot.omit_stop == pytest.omit_interval[1], "omit_stop should be 33"
        assert spot.omitted_region is True, "omitted_region should be True"


class TestGetBkgdData:
    """Tests for LaserTRAM.get_bkgd_data() method."""

    def test_get_bkgd_data(self, load_data):
        """Test that background signal is being assigned properly."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()

        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std(pytest.int_std)
        spot.assign_intervals(
            bkgd=pytest.bkgd_interval, 
            keep=pytest.keep_interval, 
            omit=pytest.omit_interval
        )
        spot.get_bkgd_data()
        
        expected_bkgd = np.array([
            0.00000000e00, 1.82979534e05, 4.85094118e03, 1.50001000e02,
            9.00032401e02, 0.00000000e00, 0.00000000e00, 1.40007840e03,
            1.00000400e02, 0.00000000e00, 5.00002000e01, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
        ])
        
        assert np.allclose(spot.bkgd_data_median, expected_bkgd), \
            "Background values are not correctly assigned"


class TestSubtractBkgd:
    """Tests for LaserTRAM.subtract_bkgd() method."""

    def test_subtract_bkgd(self, load_data):
        """Test that background signal is correctly subtracted from interval data."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()

        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std(pytest.int_std)
        spot.assign_intervals(
            bkgd=pytest.bkgd_interval, 
            keep=pytest.keep_interval, 
            omit=pytest.omit_interval
        )
        spot.get_bkgd_data()
        spot.subtract_bkgd()

        expected = (
            spot.data_matrix[spot.int_start_idx : spot.int_stop_idx, 1:]
            - spot.bkgd_data_median
        )
        
        assert np.allclose(spot.bkgd_subtract_data, expected), \
            "Background not subtracted properly"


class TestGetDetectionLimits:
    """Tests for LaserTRAM.get_detection_limits() method."""

    def test_get_detection_limits(self, load_data):
        """Test that detection limits are generated correctly."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()

        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std(pytest.int_std)
        spot.assign_intervals(
            bkgd=pytest.bkgd_interval, 
            keep=pytest.keep_interval, 
            omit=pytest.omit_interval
        )
        spot.get_bkgd_data()
        spot.get_detection_limits()

        expected_limits = np.array([
            2.18530954e02, 1.95562571e05, 6.43972601e03, 6.44267522e02,
            1.80721449e03, 1.83086988e02, 3.09052197e02, 2.48611545e03,
            3.11049711e02, 2.19579097e02, 3.98836656e02, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 7.72621221e01, 1.23098263e02,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
            0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00,
        ])
        
        assert np.allclose(spot.detection_limits, expected_limits), \
            "Detection limits not calculated correctly"


class TestNormalizeInterval:
    """Tests for LaserTRAM.normalize_interval() method."""

    def test_normalize_interval_with_omit(self, load_data):
        """Check that data are being normalized correctly with omission."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()

        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std(pytest.int_std)
        spot.assign_intervals(
            bkgd=pytest.bkgd_interval, 
            keep=pytest.keep_interval, 
            omit=pytest.omit_interval
        )
        spot.get_bkgd_data()
        spot.subtract_bkgd()
        spot.get_detection_limits()
        spot.normalize_interval()
        
        expected_shape = (spot.int_stop_idx - spot.int_start_idx) - \
                        (spot.omit_stop_idx - spot.omit_start_idx)
        
        assert spot.bkgd_subtract_normal_data.shape[0] == expected_shape, \
            "Background subtracted and normalized data wrong shape"
        
        expected_med = np.array([
            0.01043726, 1.0, 0.02550994, 0.03587271, 0.02063795, 0.21390534,
            0.01682313, 0.11149184, 0.0035571, 0.00530333, 0.02326246,
            0.04378744, 0.02122209, 0.00968445, 0.0187391, 0.02857566,
            0.00648418, 0.02463792, 0.03045385, 0.04082149, 0.00650887,
            0.00582857, 0.02133758, 0.00538868, 0.00981792, 0.01022141,
            0.0093663, 0.0086698, 0.02729486, 0.02080482, 0.02554539,
            0.03572571,
        ])
        
        assert np.allclose(spot.bkgd_subtract_med, expected_med), \
            "Median background and normalized values are incorrect"
        
        expected_std_err_rel = np.array([
            0.97426461, 0.0, 0.95142357, 0.93041269, 1.08044579, 0.93726462,
            1.1810172, 0.88558184, 1.89780192, 2.06505148, 1.33154415,
            1.25263845, 1.59623616, 1.44137923, 1.30504805, 1.7108269,
            2.07942066, 1.49831573, 1.43300245, 1.65521111, 1.70766679,
            1.70396693, 1.864858, 2.19004078, 1.74097691, 1.96200159,
            1.98419571, 2.30303923, 1.77776672, 2.13811969, 1.87573994,
            1.84468289,
        ])
        
        assert np.allclose(spot.bkgd_subtract_std_err_rel, expected_std_err_rel), \
            "Standard error values are incorrect"

    def test_normalize_interval_without_omit(self, load_data):
        """Test normalize_interval when no region is omitted."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()
        
        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std("29Si")
        spot.assign_intervals(bkgd=(5, 10), keep=(25, 40), omit=None)
        
        assert spot.omitted_region is False, "omitted_region should be False"
        
        spot.get_bkgd_data()
        spot.subtract_bkgd()
        spot.get_detection_limits()
        spot.normalize_interval()
        
        expected_rows = spot.int_stop_idx - spot.int_start_idx
        assert spot.bkgd_subtract_normal_data.shape[0] == expected_rows, \
            "Without omit, all rows in the interval should be included"
        
        assert spot.bkgd_subtract_med is not None
        assert spot.bkgd_subtract_std_err is not None
        assert spot.bkgd_subtract_std_err_rel is not None


class TestDespikeData:
    """Tests for LaserTRAM.despike_data() method."""

    def test_despike_data(self, load_data):
        """Test that data are despiked properly."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()

        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std(pytest.int_std)
        spot.assign_intervals(
            bkgd=pytest.bkgd_interval, 
            keep=pytest.keep_interval, 
            omit=pytest.omit_interval
        )
        spot.get_bkgd_data()
        spot.subtract_bkgd()
        spot.get_detection_limits()
        spot.normalize_interval()
        spot.despike_data()
        
        expected_row_100 = np.array([
            3.66069400e01, 2.44238377e04, 2.58263964e06, 6.82860111e04,
            8.11626423e04, 4.99997996e04, 4.88980604e05, 4.24720326e04,
            2.59873579e05, 8.50289098e03, 1.18055722e04, 5.99433846e04,
            1.08065112e05, 4.78915687e04, 2.41232548e04, 4.90962286e04,
            7.72378927e04, 1.81131139e04, 6.20536448e04, 8.48872585e04,
            1.12100416e05, 1.54094922e04, 1.55096160e04, 5.74316333e04,
            1.68112972e04, 2.69289756e04, 2.73298442e04, 2.57264468e04,
            2.20193771e04, 7.73385120e04, 6.10487147e04, 7.19062271e04,
            9.42540181e04,
        ])
        
        assert np.allclose(spot.data_matrix[100], expected_row_100), \
            "Data not despiked properly"

        assert spot.despiked, "spot.despiked should be True"
        assert spot.despiked_elements == spot.analytes, \
            "Despiked elements should match all analytes"

    def test_despike_data_single_analyte_string(self, load_data):
        """Test despike_data when analyte_list is a single string, not a list."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()
        
        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std("29Si")
        spot.assign_intervals(bkgd=(5, 10), keep=(25, 40), omit=(30, 33))
        spot.get_bkgd_data()
        spot.subtract_bkgd()
        spot.get_detection_limits()
        spot.normalize_interval()
        
        # Pass a SINGLE analyte as a STRING (not a list)
        spot.despike_data(analyte_list="7Li")
        
        assert spot.despiked is True
        assert spot.despiked_elements == ["7Li"], \
            "despiked_elements should be converted to list"

    def test_despike_data_multiple_analytes(self, load_data):
        """Test despike_data when analyte_list is a list of strings."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()
        
        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std("29Si")
        spot.assign_intervals(bkgd=(5, 10), keep=(25, 40), omit=(30, 33))
        spot.get_bkgd_data()
        spot.subtract_bkgd()
        spot.get_detection_limits()
        spot.normalize_interval()
        
        analytes_to_despike = ["7Li", "43Ca", "88Sr"]
        spot.despike_data(analyte_list=analytes_to_despike)
        
        assert spot.despiked is True
        assert spot.despiked_elements == analytes_to_despike

    def test_despike_data_all_analytes(self, load_data):
        """Test despike_data with analyte_list='all'."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()
        
        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std("29Si")
        spot.assign_intervals(bkgd=(5, 10), keep=(25, 40), omit=(30, 33))
        spot.get_bkgd_data()
        spot.subtract_bkgd()
        spot.get_detection_limits()
        spot.normalize_interval()
        
        spot.despike_data(analyte_list="all")
        
        assert spot.despiked is True
        assert spot.despiked_elements == spot.analytes


class TestMakeOutputReport:
    """Tests for LaserTRAM.make_output_report() method."""

    def test_make_output_report_with_omit(self, load_data):
        """Check that output report is generated correctly with omission."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()
        
        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std(pytest.int_std)
        spot.assign_intervals(
            bkgd=pytest.bkgd_interval, 
            keep=pytest.keep_interval, 
            omit=pytest.omit_interval
        )
        spot.get_bkgd_data()
        spot.subtract_bkgd()
        spot.get_detection_limits()
        spot.normalize_interval()
        spot.despike_data()
        spot.make_output_report()
        
        expected = pd.DataFrame({
            "timestamp": {0: pd.Timestamp("2022-05-10 23:08:59")},
            "Spot": {0: "test"},
            "despiked": {
                0: [
                    "7Li", "29Si", "31P", "43Ca", "45Sc", "47Ti", "51V", "55Mn",
                    "65Cu", "66Zn", "85Rb", "88Sr", "89Y", "90Zr", "93Nb",
                    "133Cs", "137Ba", "139La", "140Ce", "141Pr", "146Nd",
                    "147Sm", "153Eu", "157Gd", "163Dy", "166Er", "172Yb",
                    "178Hf", "181Ta", "208Pb", "232Th", "238U",
                ]
            },
            "omitted_region": {
                0: (np.float64(30.019650000000002), np.float64(33.31339))
            },
            "bkgd_start": {0: 5.1363},
            "bkgd_stop": {0: 10.25943},
            "int_start": {0: 25.2623},
            "int_stop": {0: 40.26601},
            "norm": {0: "29Si"},
            "norm_cps": {0: 2819243.2722727386},
            "7Li": {0: 0.010437259034101},
            "29Si": {0: 1.0},
            "31P": {0: 0.02550993641024596},
            "43Ca": {0: 0.03587271241690164},
            "45Sc": {0: 0.020637954074539257},
            "47Ti": {0: 0.2139053355651085},
            "51V": {0: 0.016823127327213718},
            "55Mn": {0: 0.11149183525132685},
            "65Cu": {0: 0.003557100318428378},
            "66Zn": {0: 0.005303326725585216},
            "85Rb": {0: 0.02326245724103047},
            "88Sr": {0: 0.04378744384175842},
            "89Y": {0: 0.021222094964942637},
            "90Zr": {0: 0.00968444848099825},
            "93Nb": {0: 0.018739101968643035},
            "133Cs": {0: 0.028575660636982726},
            "137Ba": {0: 0.0064841776030295445},
            "139La": {0: 0.02463791668966695},
            "140Ce": {0: 0.030453845935454353},
            "141Pr": {0: 0.04082149351465142},
            "146Nd": {0: 0.006508870567873512},
            "147Sm": {0: 0.005828571501401572},
            "153Eu": {0: 0.021337580959465384},
            "157Gd": {0: 0.005388680603868104},
            "163Dy": {0: 0.009817921222589381},
            "166Er": {0: 0.010221411134162577},
            "172Yb": {0: 0.009366301785549105},
            "178Hf": {0: 0.008669797278608683},
            "181Ta": {0: 0.02729485532766075},
            "208Pb": {0: 0.020804823707881108},
            "232Th": {0: 0.025545385313949856},
            "238U": {0: 0.03572571386095365},
            "7Li_se": {0: 0.9742646111044662},
            "29Si_se": {0: 0.0},
            "31P_se": {0: 0.9514235658823135},
            "43Ca_se": {0: 0.930412694285101},
            "45Sc_se": {0: 1.080445788344373},
            "47Ti_se": {0: 0.9372646210445522},
            "51V_se": {0: 1.1810172014404927},
            "55Mn_se": {0: 0.8855818382733421},
            "65Cu_se": {0: 1.8978019212448682},
            "66Zn_se": {0: 2.0650514767520787},
            "85Rb_se": {0: 1.331544147368859},
            "88Sr_se": {0: 1.2526384454267696},
            "89Y_se": {0: 1.5962361610371518},
            "90Zr_se": {0: 1.4413792299360928},
            "93Nb_se": {0: 1.3050480549054508},
            "133Cs_se": {0: 1.710826904827876},
            "137Ba_se": {0: 2.079420660182808},
            "139La_se": {0: 1.4983157335779338},
            "140Ce_se": {0: 1.4330024474613523},
            "141Pr_se": {0: 1.6552111073601967},
            "146Nd_se": {0: 1.7076667903943026},
            "147Sm_se": {0: 1.7039669327734615},
            "153Eu_se": {0: 1.8648580005076827},
            "157Gd_se": {0: 2.190040781302208},
            "163Dy_se": {0: 1.740976911125997},
            "166Er_se": {0: 1.9620015928084438},
            "172Yb_se": {0: 1.9841957089474223},
            "178Hf_se": {0: 2.3030392323015816},
            "181Ta_se": {0: 1.777766722012861},
            "208Pb_se": {0: 2.1381196925657986},
            "232Th_se": {0: 1.875739939915299},
            "238U_se": {0: 1.844682892581869},
        })
        
        # ignore dtype check due to object vs string types in "Spot" column
        # this is related to pandas introducing string dtype
        pd.testing.assert_frame_equal(spot.output_report, expected, check_dtype=False)

    def test_make_output_report_without_omit(self, load_data):
        """Test make_output_report when no region is omitted."""
        spot = LaserTRAM(name="test")
        samples = load_data.index.unique().dropna().tolist()
        
        spot.get_data(load_data.loc[samples[0], :])
        spot.assign_int_std("29Si")
        spot.assign_intervals(bkgd=(5, 10), keep=(25, 40), omit=None)
        
        spot.get_bkgd_data()
        spot.subtract_bkgd()
        spot.get_detection_limits()
        spot.normalize_interval()
        spot.make_output_report()
        
        assert spot.output_report is not None
        assert spot.output_report["omitted_region"].iloc[0] == "None", \
            "omitted_region should be 'None' string when no omission"
        assert spot.output_report["despiked"].iloc[0] == "None", \
            "despiked should be 'None' string when no despiking"
