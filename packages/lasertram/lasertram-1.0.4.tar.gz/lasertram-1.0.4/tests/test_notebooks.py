"""
Tests for documentation notebooks to ensure they execute without errors
"""

import pytest
from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


# Get all notebook files in docs folder
DOCS_DIR = Path(__file__).parent.parent / "docs"
NOTEBOOK_FILES = list(DOCS_DIR.glob("*.ipynb"))


@pytest.mark.parametrize("notebook_path", NOTEBOOK_FILES, ids=lambda p: p.name)
def test_notebook_execution(notebook_path):
    """Test that each documentation notebook executes without errors"""
    
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    # Override the kernel spec to use the current Python interpreter
    # This ensures the notebook runs with the same Python that's running pytest
    nb.metadata.kernelspec = {
        "display_name": "Python",
        "language": "python",
        "name": "python"
    }
    
    # Execute the notebook
    ep = ExecutePreprocessor(timeout=600, kernel_name="python")
    
    try:
        ep.preprocess(nb, {"metadata": {"path": str(notebook_path.parent)}})
    except Exception as e:
        pytest.fail(f"Notebook {notebook_path.name} failed to execute: {e}")
