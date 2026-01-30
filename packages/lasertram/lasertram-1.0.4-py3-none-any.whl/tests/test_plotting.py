"""
Tests for the lasertram.helpers.plotting module.

This module tests functionality for:
- Plotting raw time-series ICP-MS data
- Plotting LaserTRAM uncertainty/error bars
"""

import numpy as np
import pytest
from matplotlib import pyplot as plt

from lasertram import LaserTRAM, plotting, preprocessing


class TestPlotTimeseriesData:
    """Tests for plotting raw time-series data."""

    def test_plot_timeseries_data_all_analytes(self):
        """Test that plot_timeseries_data correctly plots all analyte data."""
        raw_data = preprocessing.load_test_rawdata()
        sample = "GSD-1G_-_1"
        
        ax = plotting.plot_timeseries_data(raw_data.loc[sample, :])

        lines = ax[0].get_lines()
        for line in lines:
            ydata = line.get_ydata()
            np.testing.assert_array_equal(
                ydata, raw_data.loc[sample, line.get_label()].values
            )
        
        plt.close('all')

    def test_plot_timeseries_data_specified_analytes(self):
        """Test that plot_timeseries_data works with specified analyte subset."""
        raw_data = preprocessing.load_test_rawdata()
        sample = "GSD-1G_-_1"
        
        ax = plotting.plot_timeseries_data(
            raw_data.loc[sample, :], analytes=["7Li", "29Si"]
        )
        
        lines = ax[0].get_lines()
        for line in lines:
            ydata = line.get_ydata()
            np.testing.assert_array_equal(
                ydata, raw_data.loc[sample, line.get_label()].values
            )
        
        plt.close('all')


class TestPlotLaserTRAMUncertainties:
    """Tests for plotting LaserTRAM uncertainty bars."""

    def test_plot_lasertram_uncertainties(self, load_data):
        """Test that error bars are being plotted correctly for LaserTRAM."""
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

        fig, ax = plt.subplots()
        plotting.plot_lasertram_uncertainties(spot, ax=ax)
        
        patches = ax.patches
        heights = []
        for patch in patches:
            heights.append(patch.get_height())
        heights = np.array(heights)

        np.testing.assert_array_equal(heights, spot.bkgd_subtract_std_err_rel)
        
        plt.close('all')
