import copy
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u

from .radtransfer_spectrum import atomicspectrum



def iterate_temperature_perturbation( atomIDs=['CaII'] , tempPert = 50):

    if hasattr( tempPert, 'unit') is False:
        tempPert = tempPert << u.K
    
    AtomSpect = atomicspectrum()
    wvls, intensities = AtomSpect.spectrum( atomIDs )
    kwargs = dict(  
                  setpop = { 
                            'atomIDs': atomIDs, 
                            'densities': [  AtomSpect.rt_eqPops[ AtomSpect.rh_atoms_setup.atomfilecontent[thisID]['name'] ].n   for thisID in atomIDs  ] 
                            }  
                  )

    Iplus = np.zeros((AtomSpect.rt_spect.wavelength.shape[0], AtomSpect.rt_atmos.Nspace))
    Iminus = copy.copy( Iplus )
    I_pm_arrays = {'Iplus':Iplus, 'Iminus':Iminus}
    pm_factors = [1,-1]
    print( "Nspace:", AtomSpect.rt_atmos.Nspace )
    for k in range(AtomSpect.rt_atmos.Nspace):
        print( "k-th of Nspace:", k )

        for I_pm, sign_pm in zip( ['Iplus','Iminus'] , pm_factors ):
            kwargs['tp'] = { 'space_index':k , 'TempPerturbation': sign_pm * 0.5 * tempPert }
            I_pm_arrays[I_pm][:,k] = atomicspectrum().spectrum(  atomIDs , **kwargs  )[1][:,-1]

    rf = (I_pm_arrays['Iplus'] - I_pm_arrays['Iminus']) / AtomSpect.rt_ctx.I[:, -1][:, None]

    yEdges = np.arange(AtomSpect.rt_atmos.Nspace+1) - 0.5
    xEdges = 0.5 * (AtomSpect.rt_spect.wavelength[1:] + AtomSpect.rt_spect.wavelength[:-1])
    xEdges = np.insert(xEdges, 0, xEdges[0] - (xEdges[1] - xEdges[0]))
    xEdges = np.insert(xEdges, -1, xEdges[-1] + (xEdges[-1] - xEdges[-2]))
    plt.figure()
    plt.pcolormesh(xEdges, yEdges, rf.T)
    plt.xlim(853.944, 854.944)
    plt.show()
    #plt.close()

    return xEdges, yEdges, rf.T



