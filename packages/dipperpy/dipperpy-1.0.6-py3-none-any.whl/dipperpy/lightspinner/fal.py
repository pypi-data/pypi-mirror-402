import numpy as np
from .atmosphere import AtmosphereConstructor, ScaleType
from typing import Callable
from . import constants as Const
import astropy.units as u

import pickle
import dipperpy
import pathlib
import os

def Falc82():

    dbdir_path = pathlib.Path( dipperpy.dipall().dipperpy_dbdir )
    pfile_path = os.path.join( dbdir_path , 'fal.pickle' )
    with open( pfile_path ,'rb') as picklefile:
        faldiction = pickle.load( picklefile )

    _Falc82: Callable[[], AtmosphereConstructor] = lambda: AtmosphereConstructor(depthScale=faldiction['cmass'] << u.g / u.cm**2, temperature=np.copy(faldiction['temp']) << u.K, ne=faldiction['ne'] << u.cm**(-3), vlos=faldiction['vel_LoS'] << u.km / u.s, vturb=faldiction['vturb'] << u.km / u.s, hydrogenPops=faldiction['nh'] << u.cm**(-3))

    return _Falc82()


