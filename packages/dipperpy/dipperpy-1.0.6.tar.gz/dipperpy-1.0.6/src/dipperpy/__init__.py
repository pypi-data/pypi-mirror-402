#
# import classes and functions from base.py (and others)
#
from .base import dipall, diprd, diprd_multi  # classes
from .missing import missing  # functions
#from .plasma import plasma
from . import lightspinner
from .version import __version__ , __version_usedate__ , version
#__version__ = version.__version__

print("Diagnostics Inferring the Physics of Plasma and Emitted Radiation in python (DIPPERpy)")
#if version.__version_usedate__:
if __version_usedate__:
    print(f"DIPPERpy last updated on {__version__}")
else:
    print(f"DIPPERpy version {__version__}")


dipall.confirmdirs(dipperpy_importing=True) # check path for XUVTOP


