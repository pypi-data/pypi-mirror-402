from .atomic_model import *
from .collisional_rates import *
import dipperpy

import pickle
import pathlib
import os


class rh_atoms:

    def __init__(self):

        #pfile_path = os.path.join( pathlib.Path( dipall().dipperpy_dbdir ).parent.resolve() , 'rh_atoms.pickle' )
        self.dbdir_path = pathlib.Path( dipperpy.dipall().dipperpy_dbdir )
        pfile_path = os.path.join( self.dbdir_path , 'rh_atoms.pickle' )
        #
        with open( pfile_path,'rb') as picklefile:
            self.atomfilecontent = pickle.load( picklefile )


        self.Lletterorbitals = {'S':0,'P':1,'D':2,'F':3,'G':4,'H':5,'I':6,'J':7,'K':8}


        self.collisiondictionfuncs = {'CE':CE, 'CI':CI, 'OMEGA':Omega}



    def checkID(func):
        def validateID(self, trialname):
            # before
            if trialname in list(self.atomfilecontent.keys()):
                IDname = func(self, trialname)
            else:
                print(f"\n\nPlease see the list of valid IDs here:\n{sorted(list(self.atomfilecontent.keys()))}\n\n")
                raise KeyError(f"The given ID '{trialname}' is not valid within the 'rh_atoms.pickle' atomic database.")
            # after
            return IDname
        return validateID


    @checkID
    def atomID_name(self, atom_identity='CaII'):
        return self.atomfilecontent[atom_identity]['name']

    @checkID
    def modelatom(self, atom_identity='CaII'):

        atomfilecontent = self.atomfilecontent
        Lletterorbitals = self.Lletterorbitals
        collisiondictionfuncs = self.collisiondictionfuncs
        checkScalar_JS = lambda val: Fraction( val[0] , val[1] )  if hasattr( val, '__len__' )  else val
        checkString_L = lambda val:  None  if val==None else Lletterorbitals[val]

        return AtomicModel( 
                           name=atomfilecontent[atom_identity]['name'],
                           levels=[
                               AtomicLevel( 
                                           E = atomfilecontent[atom_identity]['AtomLevel']['E'][ind], 
                                           g = atomfilecontent[atom_identity]['AtomLevel']['g'][ind], 
                                           label = atomfilecontent[atom_identity]['AtomLevel']['label'][ind], 
                                           stage = atomfilecontent[atom_identity]['AtomLevel']['stage'][ind], 
                                           J = checkScalar_JS( atomfilecontent[atom_identity]['AtomLevel']['J'][ind] ), 
                                           L = checkString_L( atomfilecontent[atom_identity]['AtomLevel']['L'][ind] ), 
                                           S = checkScalar_JS( atomfilecontent[atom_identity]['AtomLevel']['S'][ind] ), 
                                           )
                               for ind in range(len(atomfilecontent[atom_identity]['AtomLevel']['E']))
                               ],
                           lines=[
                               VoigtLine(
                                   j = atomfilecontent[atom_identity]['VoigtLine']['j'][ind], 
                                   i = atomfilecontent[atom_identity]['VoigtLine']['i'][ind], 
                                   f = atomfilecontent[atom_identity]['VoigtLine']['f'][ind],
                                   type = [ LineType.CRD , LineType.PRD ][int(atomfilecontent[atom_identity]['VoigtLine']['type'][ind]=='PRD')], 
                                   NlambdaGen = atomfilecontent[atom_identity]['VoigtLine']['NlambdaGen'][ind], 
                                   qCore = atomfilecontent[atom_identity]['VoigtLine']['qCore'][ind], 
                                   qWing = atomfilecontent[atom_identity]['VoigtLine']['qWing'][ind], 
                                   vdw = VdwUnsold(vals=[ atomfilecontent[atom_identity]['VoigtLine']['vdw_vals'][ind][0] , atomfilecontent[atom_identity]['VoigtLine']['vdw_vals'][ind][1] ]), 
                                   gRad = atomfilecontent[atom_identity]['VoigtLine']['gRad'][ind], 
                                   stark = atomfilecontent[atom_identity]['VoigtLine']['stark'][ind]
                                   )
                               for ind in range(len(atomfilecontent[atom_identity]['VoigtLine']['j']))
                               ],
                           continua=[],
                           collisions=[
                               collisiondictionfuncs[collisiontype]( j = atomfilecontent[atom_identity]['Collision'][collisiontype]['j'][ind] , i = atomfilecontent[atom_identity]['Collision'][collisiontype]['i'][ind], temperature = atomfilecontent[atom_identity]['Collision'][collisiontype]['temps_sets'][ind] , rates = atomfilecontent[atom_identity]['Collision'][collisiontype]['rates_sets'][ind] )   
                               for collisiontype in list(atomfilecontent[atom_identity]['Collision'].keys())  
                               for ind in range(len(atomfilecontent[atom_identity]['Collision'][collisiontype]['j']))    
                               if len( atomfilecontent[atom_identity]['Collision'][collisiontype]['j'] ) > 0   
                               ]
                           )




