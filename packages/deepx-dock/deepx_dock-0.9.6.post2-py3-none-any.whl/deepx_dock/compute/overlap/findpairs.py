from itertools import chain
import numpy as np
from scipy.spatial import KDTree

from HPRO.utils.misc import atom_number2name
from HPRO.utils.supercell import minimum_supercell
from HPRO.matao.matao import PairsInfo


def pairs_within_cutoff(structure1, cutoffs1, structure2=None, cutoffs2=None):
    '''
    find all atom pairs (i, j) satisfying |r_i-r_j| <= (cutoff_i+cutoff_j),
    where r_i and r_j are atomic positions in structure1 and structure2 respectively.
    (the two structures must have the same lattice vectors and atomic species)
    This is the new implementation with scipy.spatial.KDTree which can be 300x faster on MATBG

    Returns:
        PairsInfo: The PairsInfo object containing the atom pairs within cutoff.
    '''
    if structure2 is None:
        structure2 = structure1
    if cutoffs2 is None:
        cutoffs2 = cutoffs1

    maxr = max(cutoffs1.values()) + max(cutoffs2.values())
    supercell2 = minimum_supercell(structure2, 2*maxr)

    atom_names_1 = atom_number2name(structure1.atomic_species)
    atom_names_2 = atom_number2name(structure2.atomic_species)
    assert atom_names_1 == atom_names_2, "The two structures must have the same atomic species"
    atom_names = atom_names_1
    cutoffs1 = [cutoffs1[name] for name in atom_names]
    cutoffs2 = [cutoffs2[name] for name in atom_names]

    # 1 corresponds to first atoms in atom pairs, and 2 corresponds to second atoms.
    # 1 is always in unit cell, 2 is always in supercell.
    trees1_spc, trees2_spc = [], []
    # mapiat maps index of atom of specifc atomic number (i.e. atom index in the tree) 
    # to index of it in original cell
    mapiat1_spc, mapiat2_spc = [], []
    for ispc in range(structure1.nspc):
        spc = structure1.atomic_species[ispc]

        is_thisspc = (structure1.atomic_numbers == spc)
        trees1_spc.append(KDTree(structure1.atomic_positions_cart_uc[is_thisspc]))
        mapiat1_spc.append(np.where(is_thisspc)[0])

        is_thisspc = (supercell2.atomic_numbers == spc)
        trees2_spc.append(KDTree(supercell2.atomic_positions_cart[is_thisspc]))
        mapiat2_spc.append(np.where(is_thisspc)[0])

    allpairs = []
    for ispc1 in range(structure1.nspc):
        for ispc2 in range(structure2.nspc):
            tree1 = trees1_spc[ispc1]
            tree2 = trees2_spc[ispc2]
            map1 = mapiat1_spc[ispc1]
            map2 = mapiat2_spc[ispc2]

            res = tree1.query_ball_tree(tree2, r=cutoffs1[ispc1]+cutoffs2[ispc2])
            iatspc1 = []
            for i1 in range(len(res)):
                n = len(res[i1])
                if n > 0: iatspc1.append(np.full(n, i1, dtype=int))

            if len(iatspc1) > 0: 
                iatspc1 = np.concatenate(iatspc1)
                iatspc2 = np.fromiter(chain.from_iterable(res), dtype=int)
                allpairs.append(np.stack((map1[iatspc1], map2[iatspc2]), axis=1))

    allpairs = np.concatenate(allpairs)

    translations_cuc, iat2_uc = supercell2.iat_sc2uc(allpairs[:, 1], True)

    allpairs[:, 1] = iat2_uc

    translations = structure2.trans_cuc_to_original(translations_cuc, allpairs[:, 0], allpairs[:, 1])

    return PairsInfo(structure2, translations, allpairs)