"""
MUSICA: A Python library for atmospheric chemistry simulations.
"""


# start delvewheel patch
def _delvewheel_patch_1_12_0():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'musica.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_12_0()
del _delvewheel_patch_1_12_0
# end delvewheel patch

from ._version import version as __version__
from .micm import MICM, SolverType, State, Conditions
from .tuvx import TUVX, GridMap, Grid, ProfileMap, Profile, RadiatorMap, Radiator
from . import mechanism_configuration
from . import carma
from . import cuda
from .examples import Examples
