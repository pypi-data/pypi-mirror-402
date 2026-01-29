import numpy as np
from scipy import sparse
import h5py
import json
from pathlib import Path
from tqdm import tqdm

from deepx_dock.CONSTANT import DEEPX_INFO_FILENAME
from deepx_dock.CONSTANT import DEEPX_HAMILTONIAN_FILENAME, DEEPX_OVERLAP_FILENAME
from deepx_dock.misc import get_data_dir_lister

HARTREE_TO_EV = 27.2113845 # 27.211386
spd_to_012 = {'s': 0, 'p': 1, 'd': 2, 'f': 3, 'g': 4, 'h': 5, 'i': 6}

AIMS_CONTROL_FILENAME = "control.in"
AIMS_STRUCT_FILENAME = "geometry.in"
AIMS_BASIS_FILENAME = "basis-indices.out"
FILES_NECESSARY = set([AIMS_CONTROL_FILENAME, AIMS_STRUCT_FILENAME, AIMS_BASIS_FILENAME])
FILES_IN = ["hamiltonian.out", "overlap-matrix.out"]
FILES_OUT = [DEEPX_HAMILTONIAN_FILENAME, DEEPX_OVERLAP_FILENAME]
UNITS = [HARTREE_TO_EV, 1.0]


def validation_check_aims(root_dir: Path, prev_dirname: Path):
    if root_dir.is_dir():
        all_files = [str(v.name) for v in root_dir.iterdir()]
        if FILES_NECESSARY.issubset(set(all_files)):
            yield prev_dirname


class SingleAtomDataTranslatorToDeepH:
    def __init__(self, aims_data_dir, deeph_data_dir, n_tier=0):
        self.aims_data_dir = Path(aims_data_dir)
        self.deeph_data_dir = Path(deeph_data_dir)
        self.n_tier = n_tier
        assert self.aims_data_dir.is_dir(), f"{aims_data_dir} is not a directory!"
        self.deeph_data_dir.mkdir(parents=True, exist_ok=True)

    def transfer_all_aims_to_deeph(self):
        data_dir_lister = get_data_dir_lister(
            self.aims_data_dir, self.n_tier, validation_check_aims
        )
        for dir_name in tqdm(data_dir_lister, desc="Data"):
            self.transfer_one_aims_to_deeph(
                dir_name, self.aims_data_dir, self.deeph_data_dir
            )

    @staticmethod
    def transfer_one_aims_to_deeph(
        dir_name: str, aims_path: Path, deeph_path: Path
    ):
        try:
            aims_dir_path = aims_path / dir_name
            deeph_dir_path = deeph_path / dir_name
            deeph_dir_path.mkdir(parents=True, exist_ok=True)
            return SingleAtomDataTranslatorToDeepH.transfer(
                aims_dir_path, deeph_dir_path
            )
        except Exception as e:
            print(f"Error in {dir_name}: {e}")

    @staticmethod
    def transfer(input_dir: Path, output_dir: Path):
        with open(input_dir / AIMS_STRUCT_FILENAME, "r") as f:
            lines = f.readlines()
            if len(lines) != 1:
                print(f"[Warn] {input_dir} is not a single atom structure!")
            elements = [line.split()[4] for line in lines]
        basis_types = np.loadtxt(
            input_dir / AIMS_BASIS_FILENAME, dtype=str, usecols=(1,), skiprows=2
        ) # 'atomic', 'ionic', 'hydro', ...
        basis_indices = np.loadtxt(
            input_dir / AIMS_BASIS_FILENAME, 
            dtype=int, usecols=(2,3,4,5), skiprows=2
        ) # shape: [N_orb, 4], 4: ia, n, l, m
        #
        N_orb = basis_indices.shape[0]
        N_atom = max(basis_indices[:, 0])
        phase_factor = (-1)**(
            np.logical_and(basis_indices[:,3] > 0, basis_indices[:,3] % 2 == 1)
        )
        #
        elements_info = SingleAtomDataTranslatorToDeepH.read_control_file(input_dir)
        #
        orbital_map = [[] for _ in range(N_atom)]
        core_orbital_index = [[] for _ in range(N_atom)]
        valence_orbital_index = [[] for _ in range(N_atom)]
        unoccupied_orbital_index = [[] for _ in range(N_atom)]
        orbital_index_now = [0 for _ in range(N_atom)]
        i = 0
        while i < N_orb:
            ia, n, ll = basis_indices[i, 0:3]
            orbital_map[ia-1].append(int(ll))
            ele = elements[ia-1]
            if ('atomic' == basis_types[i]) and (n < elements_info[ele]['valence'][ll]):
                core_orbital_index[ia-1].append(orbital_index_now[ia-1])
            elif ('atomic' == basis_types[i]) and (n == elements_info[ele]['valence'][ll]):
                valence_orbital_index[ia-1].append(orbital_index_now[ia-1])
            else:
                unoccupied_orbital_index[ia-1].append(orbital_index_now[ia-1])
            orbital_index_now[ia-1] += 1
            i += 2*ll + 1
        elements_orbital_map = {}
        elements_core_orbital_index = {}
        elements_valence_orbital_index = {}
        elements_unoccupied_orbital_index = {}
        for i in range(len(orbital_map)):
            ele = elements[i]
            if ele not in elements_orbital_map.keys():
                elements_orbital_map[ele] = orbital_map[i]
                elements_core_orbital_index[ele] = core_orbital_index[i]
                elements_valence_orbital_index[ele] = valence_orbital_index[i]
                elements_unoccupied_orbital_index[ele] = unoccupied_orbital_index[i]
        #
        info = {
            "atoms_quantity": int(N_atom),
            "orbits_quantity": int(N_orb),
            "orthogonal_basis": False,
            "spinful": False,
            "fermi_energy_eV": None,
            "elements_orbital_map": elements_orbital_map,
            "elements_core_orbital_index": elements_core_orbital_index,
            "elements_valence_orbital_index": elements_valence_orbital_index,
            "elements_unoccupied_orbital_index": elements_unoccupied_orbital_index,
        }
        with open(output_dir/DEEPX_INFO_FILENAME, 'w') as f:
            json.dump(info, f)
        #
        for file_in, file_out, unit in zip(FILES_IN, FILES_OUT, UNITS):
            if not (input_dir / file_in).exists():
                continue
            obs_raw_idx = np.loadtxt(
                input_dir / file_in, dtype=int, usecols=(0,1)
            )
            obs_raw_value = np.loadtxt(
                input_dir / file_in, dtype=float, usecols=(2)
            )
            assert max(obs_raw_idx[:,0]) == max(obs_raw_idx[:,1]) == N_orb, f"The size of {file_in} ({max(obs_raw_idx[:,0])}) is not consistent with the number of orbitals ({N_orb})! (NOTE: spinful case is not supported yet)"
            obs = sparse.coo_matrix((
                obs_raw_value, (obs_raw_idx[:,0]-1, obs_raw_idx[:,1]-1)
            ), shape=(N_orb, N_orb)).todense()
            obs = np.array(obs, dtype=np.float64) * unit
            obs = obs + obs.T
            obs[np.arange(N_orb), np.arange(N_orb)] /= 2.0
            obs = obs * phase_factor[:, None] * phase_factor[None, :]
            #
            R = [0,0,0]
            atom_pairs = []
            chunk_shapes = []
            chunk_boundaries = [0,]
            entries = []
            for i_atom in range(1, N_atom+1):
                slice_i = basis_indices[:, 0] == i_atom
                for j_atom in range(1, N_atom+1):
                    slice_j = basis_indices[:, 0] == j_atom
                    #
                    block = obs[slice_i, :][:, slice_j]
                    atom_pairs.append([R[0], R[1], R[2], i_atom-1, j_atom-1])
                    chunk_shapes.append(block.shape)
                    chunk_boundaries.append(
                        chunk_boundaries[-1] + block.shape[0]*block.shape[1]
                    )
                    entries.append(block.reshape(-1))
            entries = np.concatenate(entries, axis=0)

            with h5py.File(output_dir / file_out, 'w') as f:
                f.create_dataset("atom_pairs", data=np.array(atom_pairs, dtype=int))
                f.create_dataset("chunk_shapes", data=np.array(chunk_shapes, dtype=int))
                f.create_dataset("chunk_boundaries", data=np.array(chunk_boundaries, dtype=int))
                f.create_dataset("entries", data=entries, dtype=np.float64)
    
    @staticmethod
    def read_control_file(input_dir):
        elements_info = {}
        ele = ""
        with open(input_dir / AIMS_CONTROL_FILENAME, 'r') as f:
            for line in f.readlines():
                if len(line.split()) == 0:
                    continue
                sp = line.split()
                if 'species' == sp[0]:
                    ele = sp[1]
                    elements_info[ele] = {'valence': [0,]*10}
                if 'valence' == sp[0]:
                    n, ll = int(sp[1]), int(spd_to_012[sp[2]])
                    elements_info[ele]['valence'][ll] = n
        return elements_info
