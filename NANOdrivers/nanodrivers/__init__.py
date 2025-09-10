from nanodrivers.visa_drivers import *
from nanodrivers.non_visa_drivers import *
from nanodrivers.LakeShore370 import *
from nanodrivers.scripts_for_matlab import *

import warnings
import packaging

min_version = (16, 8)
max_version = (24, 0)

ver = tuple(map(int, packaging.__version__.split('.')[:2]))

if not (min_version <= ver < max_version):
    warnings.warn(
        f"Detected packaging version {packaging.__version__}. "
        "Recommended version for full compatibility: >=16.8 and <24. "
        "The package may still work, but some features could be unstable.",
        UserWarning
    )