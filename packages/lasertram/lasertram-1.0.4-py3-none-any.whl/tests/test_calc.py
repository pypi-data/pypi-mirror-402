"""
Tests for the lasertram.calc.calc module (LaserCalc class).

This module tests functionality for:
- Loading and validating standard reference material (SRM) compositions
- Loading and validating LaserTRAM-complete data
- Setting calibration standards and calculating concentration ratios
- Drift checking and correction
- Setting internal standard concentrations
- Calculating element concentrations
- Calculating secondary standard accuracies
"""

import numpy as np
import pandas as pd
import pytest

from lasertram import LaserCalc, conversions, formatting


class TestGetSRMComps:
    """Tests for LaserCalc.get_SRM_comps() method."""

    def test_get_srm_comps(self, load_SRM_data):
        """Test that SRM compositions are loaded correctly."""
        concentrations = LaserCalc(name="test")
        concentrations.get_SRM_comps(load_SRM_data)

        expected_elements = [
            "Ag", "Al", "As", "Au", "B", "Ba", "Be", "Bi", "Br", "Ca", "Cd",
            "Ce", "Cl", "Co", "Cr", "Cs", "Cu", "Dy", "Er", "Eu", "F", "Fe",
            "Ga", "Gd", "Ge", "Hf", "Ho", "In", "K", "La", "Li", "Lu", "Mg",
            "Mn", "Mo", "Na", "Nb", "Nd", "Ni", "P", "Pb", "Pr", "Rb", "Re",
            "S", "Sb", "Sc", "Se", "Si", "Sm", "Sn", "Sr", "Ta", "Tb", "Th",
            "Ti", "Tl", "Tm", "U", "V", "W", "Y", "Yb", "Zn", "Zr", "SiO2",
            "TiO2", "Sl2O3", "FeO", "MgO", "MnO", "CaO", "Na2O", "K2O", "P2O5",
        ]
        
        assert concentrations.standard_elements == expected_elements, \
            "Standard elements not being accessed properly"

        expected_standards = [
            "BCR-2G", "BHVO-2G", "BIR-1G", "GSA-1G", "GSC-1G", "GSD-1G",
            "GSE-1G", "NIST-610", "NIST-612", "BM9021-G", "GOR128-G",
            "GOR132-G", "ATHO-G", "KL2-G", "ML3B-G", "T1-G", "StHs680-G",
        ]
        
        assert concentrations.database_standards == expected_standards, \
            "Standard names not being read in properly"

    def test_get_srm_comps_missing_columns_raises_valueerror(self, load_SRM_data):
        """Test that missing required columns raises ValueError."""
        calc = LaserCalc(name="test")
        
        # Keep all columns but rename 'Ag' to something else
        bad_data = load_SRM_data.copy()
        bad_data = bad_data.rename(columns={"Ag": "NotAg"})
        
        with pytest.raises(ValueError, match="missing the following required columns"):
            calc.get_SRM_comps(bad_data)

    def test_get_srm_comps_wrong_types_raises_typeerror(self, load_SRM_data):
        """Test that incorrect column types raises TypeError."""
        good_data = load_SRM_data.copy()
        good_data["Standard"] = 12345.0
        
        calc = LaserCalc(name="test")
        
        with pytest.raises(TypeError, match="incorrect types"):
            calc.get_SRM_comps(good_data)


class TestGetData:
    """Tests for LaserCalc.get_data() method."""

    def test_get_lc_data(self, load_SRM_data, load_LTcomplete_data):
        """Test that LaserCalc data is loaded correctly."""
        concentrations = LaserCalc(name="test")
        concentrations.get_SRM_comps(load_SRM_data)
        concentrations.get_data(load_LTcomplete_data)
        
        # Check spots are found
        assert len(concentrations.spots) > 0
        assert concentrations.spots[0] == "GSD-1G_-_1"
        
        # Check potential calibration standards
        expected_cal_stds = ["ATHO-G", "BCR-2G", "GSD-1G", "GSE-1G", "NIST-612"]
        assert concentrations.potential_calibration_standards == expected_cal_stds, \
            "Potential calibration standards not found correctly"
        
        # Check unknown samples detected
        assert concentrations.samples_nostandards == ["unknown"], \
            "Unknown analyses not found correctly"
        
        # Check element extraction from analytes
        expected_elements = [
            "Li", "Si", "P", "Ca", "Sc", "Ti", "V", "Mn", "Cu", "Zn", "Rb",
            "Sr", "Y", "Zr", "Nb", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Sm",
            "Eu", "Gd", "Dy", "Er", "Yb", "Hf", "Ta", "Pb", "Th", "U",
        ]
        assert concentrations.elements == expected_elements, \
            "Analyte to element conversion not correct"

    def test_get_data_missing_columns_raises_valueerror(
        self, load_SRM_data, load_LTcomplete_data
    ):
        """Test that missing required columns raises ValueError."""
        calc = LaserCalc(name="test")
        calc.get_SRM_comps(load_SRM_data)
        
        bad_data = load_LTcomplete_data.copy()
        bad_data = bad_data.rename(columns={"timestamp": "not_timestamp"})
        
        with pytest.raises(ValueError, match="missing the following required columns"):
            calc.get_data(bad_data)

    def test_get_data_wrong_types_raises_typeerror(
        self, load_SRM_data, load_LTcomplete_data
    ):
        """Test that incorrect column types raises TypeError."""
        calc = LaserCalc(name="test")
        calc.get_SRM_comps(load_SRM_data)
        
        good_data = load_LTcomplete_data.copy()
        good_data["timestamp"] = "not_a_datetime"
        
        with pytest.raises(TypeError, match="incorrect types"):
            calc.get_data(good_data)

    def test_get_data_verbose_false(
        self, load_SRM_data, load_LTcomplete_data, capsys
    ):
        """Test that verbose=False suppresses print messages."""
        calc = LaserCalc(name="test")
        calc.get_SRM_comps(load_SRM_data)
        calc.get_data(load_LTcomplete_data, verbose=False)
        
        captured = capsys.readouterr()
        assert "checking LaserCalc input data format" not in captured.out

    def test_element_not_in_standards_raises_valueerror(
        self, load_SRM_data, load_LTcomplete_data
    ):
        """Test that an element not in standards database raises ValueError."""
        calc = LaserCalc(name="test")
        calc.get_SRM_comps(load_SRM_data)
        
        bad_lt_data = load_LTcomplete_data.copy()
        bad_lt_data["999Xx"] = 0.5
        bad_lt_data["999Xx_se"] = 0.1
        
        with pytest.raises(ValueError, match="is not in the standards database"):
            calc.get_data(bad_lt_data)

    def test_no_calibration_standards_raises_valueerror(
        self, load_SRM_data, load_LTcomplete_data
    ):
        """Test ValueError when no calibration standards have all analyte values."""
        calc = LaserCalc(name="test")
        calc.get_SRM_comps(load_SRM_data)
        
        bad_lt_data = load_LTcomplete_data.copy()
        bad_lt_data["79Br"] = 0.5
        bad_lt_data["79Br_se"] = 0.1
        bad_lt_data = bad_lt_data[~bad_lt_data["Spot"].str.contains("ATHO-G")]
        
        with pytest.raises(ValueError, match="cannot process data"):
            calc.get_data(bad_lt_data)


class TestDuplicateSamples:
    """Tests for handling duplicate sample names."""

    def test_duplicate_samples(self, load_LTcomplete_data):
        """Test check for finding duplicate sample names."""
        lt_complete = load_LTcomplete_data.copy()
        lt_complete.loc[1, "Spot"] = "GSD-1G_-_1"
        lt_complete.loc[164, "Spot"] = "ATHO-G_-_4"

        duplicates = formatting.check_duplicate_values(
            lt_complete, "Spot", print_output=True
        )

        expected = pd.Series(
            {0: "GSD-1G_-_1", 1: "GSD-1G_-_1", 164: "ATHO-G_-_4", 165: "ATHO-G_-_4"},
            name="Spot",
        )

        pd.testing.assert_series_equal(duplicates, expected)

    def test_replace_duplicate_samples(self, load_LTcomplete_data):
        """Test replacing duplicate sample names."""
        lt_complete = load_LTcomplete_data.copy()
        lt_complete.loc[1, "Spot"] = "GSD-1G_-_1"
        lt_complete.loc[164, "Spot"] = "ATHO-G_-_4"
        
        result = formatting.rename_duplicate_values(
            lt_complete, "Spot", print_output=True
        )
        expected = pd.Series(
            {
                0: "GSD-1G_-_1-a",
                1: "GSD-1G_-_1-b",
                164: "ATHO-G_-_4-a",
                165: "ATHO-G_-_4-b",
            },
            name="Spot",
        )

        pd.testing.assert_series_equal(result.loc[[0, 1, 164, 165], "Spot"], expected)


class TestSetCalibrationStandard:
    """Tests for LaserCalc.set_calibration_standard() method."""

    def test_set_calibration_standard(self, load_SRM_data, load_LTcomplete_data):
        """Test that calibration standard data is properly assigned."""
        concentrations = LaserCalc(name="test")
        concentrations.get_SRM_comps(load_SRM_data)
        concentrations.get_data(load_LTcomplete_data)
        concentrations.set_calibration_standard("GSD-1G")
        
        assert concentrations.calibration_std == "GSD-1G"
        
        # Check means
        test_means = pd.Series({
            "7Li": 0.010514340000220277,
            "29Si": 1.0,
            "31P": 0.025310021780240298,
            "43Ca": 0.0370916922740531,
            "45Sc": 0.020889371447489306,
            "47Ti": 0.21808824754316664,
            "51V": 0.01680311011458345,
            "55Mn": 0.11086931664495428,
            "65Cu": 0.0033192819392361688,
            "66Zn": 0.00538551006241637,
            "85Rb": 0.023780278610644006,
            "88Sr": 0.0458124521713978,
            "89Y": 0.022219077036608106,
            "90Zr": 0.010176602015108708,
            "93Nb": 0.018954572715224556,
            "133Cs": 0.029569786588847926,
            "137Ba": 0.006920249495778854,
            "139La": 0.025776100916924973,
            "140Ce": 0.03170470023214307,
            "141Pr": 0.042701015762156756,
            "146Nd": 0.006765706468540337,
            "147Sm": 0.006111752387191597,
            "153Eu": 0.021745128675798656,
            "157Gd": 0.005784290157112075,
            "163Dy": 0.010391424206551071,
            "166Er": 0.010458064791942844,
            "172Yb": 0.009639013782208355,
            "178Hf": 0.008836468906653999,
            "181Ta": 0.027866368422299996,
            "208Pb": 0.0221058848225871,
            "232Th": 0.026274269275601274,
            "238U": 0.03797459547232614,
        })
        pd.testing.assert_series_equal(
            concentrations.calibration_std_means, test_means
        )


class TestDriftCheck:
    """Tests for LaserCalc.drift_check() method."""

    def test_drift_check(self, load_SRM_data, load_LTcomplete_data):
        """Test that drift is accounted for properly."""
        concentrations = LaserCalc(name="test")
        concentrations.get_SRM_comps(load_SRM_data)
        concentrations.get_data(load_LTcomplete_data)
        concentrations.set_calibration_standard("GSD-1G")
        concentrations.drift_check()
        
        test_drift = pd.Series({
            "7Li": "False", "29Si": "False", "31P": "False", "43Ca": "False",
            "45Sc": "False", "47Ti": "False", "51V": "True", "55Mn": "False",
            "65Cu": "False", "66Zn": "False", "85Rb": "True", "88Sr": "False",
            "89Y": "False", "90Zr": "False", "93Nb": "True", "133Cs": "True",
            "137Ba": "False", "139La": "False", "140Ce": "True", "141Pr": "False",
            "146Nd": "True", "147Sm": "False", "153Eu": "True", "157Gd": "False",
            "163Dy": "False", "166Er": "False", "172Yb": "False", "178Hf": "False",
            "181Ta": "False", "208Pb": "False", "232Th": "True", "238U": "True",
        })
        test_drift.name = "drift_correct"
        
        pd.testing.assert_series_equal(
            test_drift, concentrations.calibration_std_stats["drift_correct"]
        )

    def test_drift_check_returns_results(self, load_SRM_data, load_LTcomplete_data):
        """Test that drift_check returns expected structure."""
        calc = LaserCalc(name="test")
        calc.get_SRM_comps(load_SRM_data)
        calc.get_data(load_LTcomplete_data)
        calc.set_calibration_standard("GSD-1G")
        calc.get_calibration_std_ratios()
        
        calc.drift_check()
        
        assert hasattr(calc, "calibration_std_stats")
        assert calc.calibration_std_stats is not None
        
        expected_cols = [
            "drift_correct", "f_pval", "f_value", "f_crit_value",
            "rmse", "slope", "intercept", "mean", "std_dev", "percent_std_err"
        ]
        for col in expected_cols:
            assert col in calc.calibration_std_stats.columns


class TestGetCalibrationStdRatios:
    """Tests for LaserCalc.get_calibration_std_ratios() method."""

    def test_get_calibration_std_ratios(self, load_SRM_data, load_LTcomplete_data):
        """Test that concentration ratios are calculated correctly."""
        concentrations = LaserCalc(name="test")
        concentrations.get_SRM_comps(load_SRM_data)
        concentrations.get_data(load_LTcomplete_data)
        concentrations.set_calibration_standard("GSD-1G")
        concentrations.drift_check()
        concentrations.get_calibration_std_ratios()
        
        test_ratios = np.array([
            1.72905263e-04, 1.00000000e00, 3.45810526e-03, 2.06915230e-01,
            2.09094737e-04, 2.98909254e-02, 1.76926316e-04, 8.84631579e-04,
            1.68884211e-04, 2.17136842e-04, 1.49985263e-04, 2.79061053e-04,
            1.68884211e-04, 1.68884211e-04, 1.68884211e-04, 1.28673684e-04,
            2.69410526e-04, 1.57223158e-04, 1.66471579e-04, 1.80947368e-04,
            1.79741053e-04, 1.92206316e-04, 1.64863158e-04, 2.03867368e-04,
            2.05877895e-04, 1.61244211e-04, 2.04671579e-04, 1.56821053e-04,
            1.60842105e-04, 2.01052632e-04, 1.64863158e-04, 1.64863158e-04,
        ])
        
        assert np.allclose(
            concentrations.calibration_std_conc_ratios, test_ratios, rtol=1e-3
        ), "Calibration standard concentration ratios are not correct"


class TestSetIntStdConcentrations:
    """Tests for LaserCalc.set_int_std_concentrations() method."""

    def test_set_int_std_concentrations(
        self, load_SRM_data, load_LTcomplete_data, load_internal_std_comps
    ):
        """Test that internal standard concentration is set correctly."""
        concentrations = LaserCalc(name="test")
        concentrations.get_SRM_comps(load_SRM_data)
        concentrations.get_data(load_LTcomplete_data)
        concentrations.set_calibration_standard("GSD-1G")
        concentrations.drift_check()
        concentrations.get_calibration_std_ratios()
        concentrations.set_int_std_concentrations(
            spots=load_internal_std_comps["Spot"],
            concentrations=load_internal_std_comps["SiO2"],
            uncertainties=load_internal_std_comps["SiO2_std%"],
        )

        assert np.allclose(
            concentrations.data.loc["unknown", "int_std_comp"].values,
            load_internal_std_comps["SiO2"].values,
        ), "Internal standard concentrations for unknowns not set properly"
        
        assert np.allclose(
            concentrations.data.loc["unknown", "int_std_rel_unc"].values,
            load_internal_std_comps["SiO2_std%"].values,
        ), "Internal standard concentration uncertainties not set properly"

    def test_set_int_std_concentrations_with_none(
        self, load_SRM_data, load_LTcomplete_data
    ):
        """Test set_int_std_concentrations when spots=None uses defaults."""
        calc = LaserCalc(name="test")
        calc.get_SRM_comps(load_SRM_data)
        calc.get_data(load_LTcomplete_data)
        calc.set_calibration_standard("GSD-1G")
        calc.get_calibration_std_ratios()
        
        calc.set_int_std_concentrations(
            spots=None,
            concentrations=None,
            uncertainties=None,
            units="ppm_el",
        )
        
        assert (calc.data["int_std_comp"] == 10.0).all()
        assert (calc.data["int_std_rel_unc"] == 1.0).all()


class TestCalculateConcentrations:
    """Tests for LaserCalc.calculate_concentrations() method."""

    def test_calculate_concentrations_units(
        self, load_SRM_data, load_LTcomplete_data, load_internal_std_comps
    ):
        """Test that all internal standard units produce same output."""
        out = []

        for units in ["wt_per_ox", "wt_per_el", "ppm_el"]:
            concentrations = LaserCalc(name="test")
            concentrations.get_SRM_comps(load_SRM_data)
            concentrations.get_data(load_LTcomplete_data)
            concentrations.set_calibration_standard("GSD-1G")
            concentrations.drift_check()
            concentrations.get_calibration_std_ratios()

            int_std_data = load_internal_std_comps

            if units == "ppm_el":
                values = conversions.oxide_to_ppm(int_std_data["SiO2"], "Si")
            elif units == "wt_per_el":
                values = conversions.oxide_to_ppm(int_std_data["SiO2"], "Si") / 1e4
            else:
                values = int_std_data["SiO2"]

            concentrations.set_int_std_concentrations(
                spots=int_std_data["Spot"],
                concentrations=values,
                uncertainties=int_std_data["SiO2_std%"],
                units=units,
            )
            concentrations.calculate_concentrations()
            out.append(concentrations.unknown_concentrations)

        pd.testing.assert_frame_equal(out[0], out[1])
        pd.testing.assert_frame_equal(out[0], out[2])

    def test_calculate_concentrations(
        self, load_SRM_data, load_LTcomplete_data, load_internal_std_comps
    ):
        """Test that concentrations are calculated correctly."""
        concentrations = LaserCalc(name="test")
        concentrations.get_SRM_comps(load_SRM_data)
        concentrations.get_data(load_LTcomplete_data)
        concentrations.set_calibration_standard("GSD-1G")
        concentrations.drift_check()
        concentrations.get_calibration_std_ratios()
        concentrations.set_int_std_concentrations(
            spots=load_internal_std_comps["Spot"],
            concentrations=load_internal_std_comps["SiO2"],
            uncertainties=load_internal_std_comps["SiO2_std%"],
        )
        concentrations.calculate_concentrations()
        
        # Test unknown concentrations (sample of 3 rows)
        test_unknown = pd.DataFrame({
            "sample": {0: "unknown", 1: "unknown", 2: "unknown"},
            "timestamp": {
                0: pd.Timestamp("2022-05-10 23:20:00"),
                1: pd.Timestamp("2022-05-10 23:23:54"),
                2: pd.Timestamp("2022-05-10 23:28:38"),
            },
            "Spot": {
                0: "AT-3214-2_shard1_-_1",
                1: "AT-3214-2_shard2_-_2",
                2: "AT-3214-2_shard4_-_1",
            },
            "7Li": {0: 25.834667, 1: 23.918061, 2: 22.898911},
        })
        
        result = concentrations.unknown_concentrations.iloc[[0, 4, 8], :].reset_index()
        
        assert result.loc[0, "Spot"] == "AT-3214-2_shard1_-_1"
        assert np.isclose(result.loc[0, "7Li"], 25.834667, rtol=1e-4)
        
        # Check SRM concentrations exist
        assert concentrations.SRM_concentrations is not None
        assert concentrations.SRM_concentrations.shape[0] > 0

    def test_calculate_concentrations_with_drift_correction(
        self, load_SRM_data, load_LTcomplete_data, load_internal_std_comps
    ):
        """Test concentration calculation which includes drift check results."""
        calc = LaserCalc(name="test")
        calc.get_SRM_comps(load_SRM_data)
        calc.get_data(load_LTcomplete_data)
        calc.set_calibration_standard("GSD-1G")
        calc.get_calibration_std_ratios()
        
        calc.drift_check()
        
        calc.set_int_std_concentrations(
            spots=tuple(load_internal_std_comps["Spot"]),
            concentrations=tuple(load_internal_std_comps["SiO2"]),
            uncertainties=tuple(load_internal_std_comps["SiO2_std%"]),
            units="wt_per_ox",
        )
        
        calc.calculate_concentrations()
        
        assert calc.SRM_concentrations is not None
        assert calc.unknown_concentrations is not None
        assert calc.SRM_concentrations.shape[0] > 0
        assert calc.unknown_concentrations.shape[0] > 0


class TestSRMAccuracies:
    """Tests for LaserCalc.get_secondary_standard_accuracies() method."""

    def test_srm_accuracies(
        self, load_SRM_data, load_LTcomplete_data, load_internal_std_comps
    ):
        """Test that SRM accuracies are calculated correctly."""
        concentrations = LaserCalc(name="test")
        concentrations.get_SRM_comps(load_SRM_data)
        concentrations.get_data(load_LTcomplete_data)
        concentrations.set_calibration_standard("GSD-1G")
        concentrations.drift_check()
        concentrations.get_calibration_std_ratios()
        concentrations.set_int_std_concentrations(
            spots=load_internal_std_comps["Spot"],
            concentrations=load_internal_std_comps["SiO2"],
            uncertainties=load_internal_std_comps["SiO2_std%"],
        )
        concentrations.calculate_concentrations()
        concentrations.get_secondary_standard_accuracies()
        
        # Test SRM accuracies (sample of 3 rows)
        result = concentrations.SRM_accuracies.iloc[[0, 4, 8], :]
        
        # ATHO-G should be ~100% for most elements
        assert np.isclose(result.loc["ATHO-G", "29Si"], 100.0)
        
        # Check that BCR-2G and GSE-1G are present
        assert "BCR-2G" in result.index
        assert "GSE-1G" in result.index


class TestDataWithoutTimestamp:
    """Tests for data without timestamp column.
    
    NOTE: These branches appear to be unreachable due to validation in get_data()
    which requires 'timestamp' to be present. These tests are skipped as they would
    require bypassing validation, which is not a supported use case.
    """

    @pytest.mark.skip(
        reason="timestamp is required by check_lt_complete_format - branch unreachable"
    )
    def test_calculate_concentrations_without_timestamp(
        self, load_SRM_data, load_LTcomplete_data, load_internal_std_comps
    ):
        """Test concentration calculation when data lacks timestamp column."""
        pass

    @pytest.mark.skip(
        reason="timestamp is required by check_lt_complete_format - branch unreachable"
    )
    def test_srm_accuracies_without_timestamp(
        self, load_SRM_data, load_LTcomplete_data, load_internal_std_comps
    ):
        """Test SRM accuracy calculation when data lacks timestamp column."""
        pass
