"""
Tests for matplotlib style registration in lasertram
"""

import pytest
import matplotlib.pyplot as plt
from pathlib import Path


class TestMplStyleRegistration:
    """Tests for the lasertram matplotlib style"""

    def test_style_path_exists(self):
        """Test that the style_path attribute exists and points to a valid file"""
        import lasertram
        
        assert hasattr(lasertram, 'style_path'), "lasertram should have a style_path attribute"
        assert Path(lasertram.style_path).exists(), f"Style file should exist at {lasertram.style_path}"
        assert lasertram.style_path.endswith('.mplstyle'), "style_path should point to an .mplstyle file"

    def test_style_registered_in_matplotlib(self):
        """Test that the lasertram style is registered with matplotlib after import"""
        import lasertram
        
        available_styles = plt.style.available
        assert 'lasertram' in available_styles, "lasertram style should be in plt.style.available"

    def test_style_can_be_used(self):
        """Test that the style can be applied without errors"""
        import lasertram
        
        # This should not raise any exceptions
        plt.style.use('lasertram')
        
        # Create a simple plot to verify the style is applied
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        plt.close(fig)

    def test_style_use_with_context(self):
        """Test that the style works with plt.style.context()"""
        import lasertram
        
        with plt.style.context('lasertram'):
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 2, 3])
            plt.close(fig)

    def test_style_file_is_valid(self):
        """Test that the style file contains valid matplotlib style parameters"""
        import lasertram
        
        style_path = Path(lasertram.style_path)
        content = style_path.read_text()
        
        # Check that the file is not empty
        assert len(content) > 0, "Style file should not be empty"
        
        # Check that it contains some common matplotlib style parameters
        # (at least one of these should be present in a typical style file)
        common_params = ['axes', 'figure', 'lines', 'font', 'legend', 'xtick', 'ytick']
        has_valid_params = any(param in content.lower() for param in common_params)
        assert has_valid_params, "Style file should contain valid matplotlib style parameters"

    def test_style_path_matches_package_location(self):
        """Test that style_path is correctly relative to the package location"""
        import lasertram
        
        package_dir = Path(lasertram.__file__).parent
        expected_style_path = package_dir / "lasertram.mplstyle"
        
        assert Path(lasertram.style_path) == expected_style_path, \
            f"style_path should be {expected_style_path}, got {lasertram.style_path}"
