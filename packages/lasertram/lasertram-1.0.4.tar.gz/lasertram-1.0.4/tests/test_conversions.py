"""
Tests for the lasertram.helpers.conversions module.

This module tests functionality for:
- Converting between oxide weight percent and elemental ppm
- Converting weight percent to oxide form
- Listing supported oxide forms for internal standard calculations
"""

import numpy as np
import pytest

from lasertram import conversions


class TestOxideToPpm:
    """Tests for oxide to ppm conversion."""

    def test_oxide_to_ppm_single_elements(self):
        """Test oxide to ppm conversion for common rock-forming elements."""
        elements = ["Si", "Al", "Ca"]
        oxide_vals = np.array([65.0, 15.0, 8.0])

        result = []
        for element, val in zip(elements, oxide_vals):
            result.append(conversions.oxide_to_ppm(val, element))

        result = np.array(result)
        expected = np.array([303833.86315597, 79388.5390063, 57175.66916918])

        np.testing.assert_allclose(
            result,
            expected,
            err_msg="Conversions from wt percent oxide to ppm not correct",
        )


class TestWtPercentToOxide:
    """Tests for weight percent element to oxide conversion."""

    def test_wt_percent_to_oxide_single_elements(self):
        """Test weight percent to oxide conversion for common elements."""
        elements = ["Si", "Al", "Ca"]
        wt_percent_values = (
            np.array([303833.86315597, 79388.5390063, 57175.66916918]) / 1e4
        )

        result = []
        for element, val in zip(elements, wt_percent_values):
            result.append(conversions.wt_percent_to_oxide(val, element))

        result = np.array(result)
        expected = np.array([65.0, 15.0, 8.0])

        np.testing.assert_allclose(
            result,
            expected,
            err_msg="Conversions from wt percent element to oxide not correct",
        )


class TestSupportedOxides:
    """Tests for supported internal standard oxides list."""

    def test_supported_internal_standard_oxides(self):
        """Test that all expected oxides are supported."""
        result = conversions.supported_internal_standard_oxides

        expected = [
            "Al2O3",
            "As2O3",
            "Au2O",
            "B2O3",
            "BaO",
            "BeO",
            "CO2",
            "CaO",
            "Ce2O3",
            "CoO",
            "Cr2O3",
            "Cs2O",
            "CuO",
            "Dy2O3",
            "Er2O3",
            "Eu2O3",
            "FeOT",
            "Ga2O3",
            "Gd2O3",
            "GeO2",
            "H2O",
            "HfO2",
            "Ho2O3",
            "K2O",
            "La2O3",
            "Li2O",
            "Lu2O3",
            "MgO",
            "MnO",
            "MoO3",
            "Na2O",
            "Nb2O5",
            "Nd2O3",
            "NiO",
            "P2O5",
            "PbO",
            "Pr2O3",
            "Rb2O",
            "SO3",
            "Sb2O3",
            "Sc2O3",
            "SiO2",
            "Sm2O3",
            "SnO2",
            "SrO",
            "Ta2O5",
            "Tb2O3",
            "ThO2",
            "TiO2",
            "Tm2O3",
            "V2O5",
            "WO3",
            "Y2O3",
            "Yb2O3",
            "ZnO",
            "ZrO2",
        ]

        assert sorted(result) == sorted(expected), \
            "Supported internal standard oxides do not match expected"
