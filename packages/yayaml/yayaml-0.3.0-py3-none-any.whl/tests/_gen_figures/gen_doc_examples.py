"""Tests that dynamically generate output for use in the documentation.

NOTE While the files and functions are named differently, they are essentially
     still regular test functions.
     See pyproject.toml for the pytest-related settings that allow this.
"""

import pytest

from .._fixtures import *

# -----------------------------------------------------------------------------


def gen_figures(out_dir):
    """Generates figures to use in the documentation.

    The ``out_dir`` fixture provides the directory to which the files should be
    written. These are then available during the documentation build (if the
    corresponding environment variables are set accordingly).
    """
    # TODO Can dynamically generate output here, storing it in `out_dir`
    pass
