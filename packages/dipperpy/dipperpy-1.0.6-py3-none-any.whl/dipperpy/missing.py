#
import numpy as np
#import dipperpy as dp
def missing(atom):   # v0
#
#   get  missing transitions from bb and store in bbm
#    
    bb=atom['bb']
    nb=len(bb)
    nb0=nb
    if(nb == 0): return 0
    xbb = []  # part of output array
    #
    #   get unique string for term for each atomic level 
    #
    lvl = atom['lvl']
    nl=len(lvl)
    uniqterm=[]
    uniqlvl =[]
    for l in range(nl):
        levstr,termstr= dp.uniqlev(lvl,l)
        uniqlvl.append(levstr)
        uniqterm.append(termstr)
    #
    #
    #
    uniqtrn=[]   # a unique identifier for all transitions between levels
    #
    count=0
    for k in range(1,nl):
        for l in range(k):
            str=uniqlvl[k]+uniqlvl[l]
            uniqtrn.append(str)
            count+=1
    #
    # get multiplet indices from bb array
    #
    m=   dp.dict2array(bb,'mindex',int)  # index of transition
    um=np.unique(m)
    print(len(um) , ' unique multiplets and ', len(bb), ' transitions')
    jrad=dp.dict2array(bb,'j',int)  # j of transition
    irad=dp.dict2array(bb,'i',int)  # i of transition
    #
    #  find all levels belonging to a multiplet, using term string
    #
    kr=np.arange(len(bb))
    for im in um:    # loop over all multiplets in bb 
        #
        ok = dp.numwhere(im, m)  # get all lines in bb for multiplet
        #
        #
        use = ok[0]  # use the first line to get the termu, terml
        #
        type = bb[use]['type']
        #
        # OK is index in bb of all transitions
        #
        # Next:
        # find the set of allowed transitions between
        # all levels in lvl for this multiplet
        #
        j= bb[use]['j']
        i= bb[use]['i']
        #  upper and lower are indices 
        upper=uniqterm[j]
        lower=uniqterm[i]
        count=0
        #
        #  here are the permitted lines of all multiplets
        #
        for iu in range(1,nl):
            upt=uniqterm[iu]
            if (upt == upper):           # possibly   belongs to the multiplet

                for il in range(nl):
                    lot=uniqterm[il]
                    #
                    if(lot == lower):    # definitely belongs to the multiplet
                        #
                        # is it in bb already?
                        #
                        absent = True
                        for kr in range(nb0):
                            if(absent & iu == jrad[kr] & il == irad[kr]): absent=False
                        if(absent):
                            sum = lvl[iu]['g']+lvl[il]['g']
                            dif = lvl[iu]['g']-lvl[il]['g']
                            dif=np.abs(dif) 
                            signal = False
                            if(type == 'E1'): signal =    (sum > 2) &  (dif <= 2)
                            if(type == 'IC'): signal =    (sum > 2) &  (dif <= 2)
                            if(type == 'M1'): signal =    (sum > 2) &  (dif <= 2)
                            if(type == 'E2'): signal =    (sum > 4) &  (dif <= 4)
                            if(type == 'M1E2'): signal =  (sum > 4) &  (dif <= 4)
                            if(signal):
                                new = bb[use]
                                nb+=1
                                new['type'] = type
                                new['i'] = il
                                new['j'] = iu
                                new['ref'] = 'Missing transition'
                                new['f'] = 0.
                                new['aji'] = 0.
                                new['entry'] = nb
                                de = abs( lvl[iu]['e'] - lvl[il]['e'] )*100.
                                if(de == 0.): de=1.e-10
                                wl= 1./de*1.e10
                                new['wl'] = wl
                                new['mindex'] = im
                                bb.append(new)
                                if((wl > 5240.) & (type == 'IC') & (wl < 5260.)):
                                    print(new)
    print('bb expanded from ',nb0,' to ',len(bb), ' in filling with missing transitions')
    return bb

                        
#!#######################################################################
#!# End of 'missing'
#!#######################################################################
