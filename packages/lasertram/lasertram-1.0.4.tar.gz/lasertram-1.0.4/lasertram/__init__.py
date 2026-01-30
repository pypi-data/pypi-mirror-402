from .calc import LaserCalc
from .helpers import batch, conversions, plotting, preprocessing, formatting
from .tram import LaserTRAM
from pathlib import Path
import matplotlib.pyplot as plt

__version__ = "1.0.4"

# Path to the lasertram matplotlib style file
style_path = str(Path(__file__).parent / "lasertram.mplstyle")

# Register the lasertram matplotlib style so it can be used as plt.style.use("lasertram")
_style_dir = str(Path(__file__).parent)
if _style_dir not in plt.style.core.USER_LIBRARY_PATHS:
    plt.style.core.USER_LIBRARY_PATHS.append(_style_dir)
    plt.style.core.reload_library()

# __all__ = ["tram", "calc", "helpers"]
