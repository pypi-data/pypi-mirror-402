
import numpy as np
from astropy import units as u
import copy

from .fal import Falc82
from .atomic_set import RadiativeSet
from .rh_method import Context
from .background import Background
from .rh_atoms_model import rh_atoms


class atomicspectrum:

    def __init__( self ):

        self.rh_atoms_setup = rh_atoms()


    def spectrum( self, atomIDs=['CaII'], tp={'space_index':0,'TempPerturbation':0}, setpop={'atomIDs':[],'densities':[]} ):

        active_atoms = [ self.rh_atoms_setup.atomID_name(ID)  for ID in atomIDs ]
        all_atomIDs = copy.copy( atomIDs )

        if 'H_6' not in all_atomIDs:
            all_atomIDs += ['H_6']

        atmosConst = Falc82()
        atmosConst.quadrature(5)
        if tp is not None:
            if hasattr( tp['TempPerturbation'], 'unit') is False:
                tp['TempPerturbation'] = tp['TempPerturbation'] << u.K 
            else:
                if tp['TempPerturbation'].unit != u.K:
                    print("\nThe given \"tp['TempPerturbation']\" should have astropy units of 'u.K'") #UnitConversionError
                    #
            atmosConst.temperature[ tp['space_index'] ] += tp['TempPerturbation']
            #
        atmos = atmosConst.convert_scales()


        aSet = RadiativeSet([  self.rh_atoms_setup.modelatom(ID)  for ID in all_atomIDs ])

        for atomIDname in active_atoms: 
            aSet.set_active(atomIDname)

        spect = aSet.compute_wavelength_grid()
        eqPops = aSet.compute_eq_pops(atmos)
        if setpop is not None:
            for ID, n in zip( setpop['atomIDs'] , setpop['densities'] ):
                eqPops[ self.rh_atoms_setup.atomfilecontent[ID]['name'] ].pops = np.copy(n)

        background = Background(atmos, spect)
        ctx = Context(atmos, spect, eqPops, background)

        dJ = 1.0
        dPops = 1.0
        i = 0
        while dJ > 2e-3 or dPops > 1e-3:
            i += 1
            dJ = ctx.formal_sol_gamma_matrices()

            if i > 3:
                dPops = ctx.stat_equil()
            print('Iteration %.3d: dJ: %.2e, dPops: %s' % (i, dJ, 'Just iterating Jbar' if i < 3 else '%.2e' % dPops))


        self.rt_atmos = atmos
        #self.aSet = aSet
        self.rt_spect = spect
        self.rt_eqPops = eqPops
        #self.background = background
        self.rt_ctx = ctx
        self.rt_dPops = dPops
        self.rt_dJ = dJ

        return  spect.wavelength , ctx.I#[:, -1]


