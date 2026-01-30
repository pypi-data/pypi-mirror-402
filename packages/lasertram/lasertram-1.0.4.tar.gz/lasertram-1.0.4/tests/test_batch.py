"""
Tests for the lasertram.helpers.batch module.

This module tests functionality for:
- Batch processing of laser ablation spots
- Helper functions for automated data processing workflows
"""

import pandas as pd
import pytest

from lasertram import LaserTRAM, batch


class TestProcessSpot:
    """Tests for the process_spot batch helper function."""

    def test_process_spot_matches_manual_processing(self, load_data):
        """
        Check that process_spot helper function produces same output
        as doing calculations one by one in LaserTRAM.
        """
        # Manual processing
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
        spot.make_output_report()

        # Batch processing
        spot2 = LaserTRAM(name="test")
        batch.process_spot(
            spot2,
            raw_data=load_data.loc[samples[0], :],
            bkgd=pytest.bkgd_interval,
            keep=pytest.keep_interval,
            omit=pytest.omit_interval,
            int_std=pytest.int_std,
            despike=False,
            output_report=True,
        )

        pd.testing.assert_frame_equal(spot.output_report, spot2.output_report)

    def test_process_spot_with_despiking(self, load_data):
        """Test process_spot with despiking enabled."""
        samples = load_data.index.unique().dropna().tolist()

        spot = LaserTRAM(name="test")
        batch.process_spot(
            spot,
            raw_data=load_data.loc[samples[0], :],
            bkgd=pytest.bkgd_interval,
            keep=pytest.keep_interval,
            omit=pytest.omit_interval,
            int_std=pytest.int_std,
            despike=True,
            output_report=True,
        )

        assert spot.despiked is True
        assert spot.output_report is not None

    def test_process_spot_without_omit(self, load_data):
        """Test process_spot without region omission."""
        samples = load_data.index.unique().dropna().tolist()

        spot = LaserTRAM(name="test")
        batch.process_spot(
            spot,
            raw_data=load_data.loc[samples[0], :],
            bkgd=pytest.bkgd_interval,
            keep=pytest.keep_interval,
            omit=None,
            int_std=pytest.int_std,
            despike=False,
            output_report=True,
        )

        assert spot.omitted_region is False
        assert spot.output_report is not None
