import argparse
from pathlib import Path
import glob
import time
import datetime
import logging
import shutil
from pymatgen.core import Structure
from pymatgen.io.vasp import Poscar
from chgnet.model import StructOptimizer

# Setup the logging configuration
logging.basicConfig(
    format='[ %(asctime)s | %(levelname)s ] %(message)s',
    level=logging.INFO
)


class StructureMonitor:
    def __init__(self,
        buffer_dir, origin_dir, relaxed_dir, error_dir, F_max=0.1, N_max=500,
        save_trajectory_info=False,
    ):
        self.buffer_dir = Path(buffer_dir)
        self.origin_dir = Path(origin_dir)
        self.relaxed_dir = Path(relaxed_dir)
        self.error_dir = Path(error_dir)
        self.F_max = F_max
        self.N_max = N_max
        self.save_trajectory_info = save_trajectory_info
        #
        self.relaxer = StructOptimizer()
        #
        logging.info("[info] CHGNet model loaded.")

    def process_file(self, poscar_path):
        """Process one poscar file"""
        poscar_path = Path(poscar_path)
        buffer_sid_dir = poscar_path.parent
        buffer_subdir = buffer_sid_dir.parent
        sid = buffer_sid_dir.name
        #
        _rel_subdir = buffer_subdir.relative_to(self.buffer_dir)
        _origin_subdir = self.origin_dir / _rel_subdir
        _origin_sid_dir = _origin_subdir / sid
        _relaxed_subdir = self.relaxed_dir / _rel_subdir
        _relaxed_sid_dir = _relaxed_subdir / sid
        _error_subdir = self.error_dir / _rel_subdir
        _error_sid_dir = _error_subdir / sid
        #
        _relaxed_poscar_path = _relaxed_sid_dir / "POSCAR"
        _relaxed_info_path = _relaxed_sid_dir / "chgnet_info.pkl" \
            if self.save_trajectory_info else None
        #
        try:
            _relaxed_sid_dir.mkdir(parents=True, exist_ok=True)
            # Read in the structure
            logging.info(f"[do] Processing structure `{sid}` ...")
            structure = Structure.from_file(poscar_path)
            # Relaxation
            result = self.relaxer.relax(
                structure, fmax=self.F_max, steps=self.N_max,
                save_path=_relaxed_info_path
            )
            relaxed_structure = result["final_structure"]
            # Save the relaxed structure
            time_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            relaxed_poscar = Poscar(
                relaxed_structure, comment=f"Relaxed by CHGNet, {time_stamp}."
            )
            relaxed_poscar.write_file(_relaxed_poscar_path, direct=False)
            # Logging the final total energy
            logging.info(f"[done] Completed {sid} | Total-Energy {result['trajectory'].energies[-1]:.3f} eV")
            # Move the buffer poscar to origin
            _origin_subdir.mkdir(parents=True, exist_ok=True)
            assert not _origin_sid_dir.exists()
            shutil.move(buffer_sid_dir, _origin_sid_dir)
            return True
        except Exception as e:
            logging.error(f"Failed on relaxing `{poscar_path}`: {str(e)}")
            shutil.rmtree(_relaxed_sid_dir, ignore_errors=True)
            _error_subdir.mkdir(parents=True, exist_ok=True)
            assert not _error_sid_dir.exists()
            shutil.move(buffer_sid_dir, _error_sid_dir)
            return False

    def run(self):
        """Loop for monitoring relaxation"""
        logging.info(f"[do] Monitoring started on {self.buffer_dir}")
        try:
            while True:
                for poscar_path in self.buffer_dir.rglob('POSCAR'):
                    self.process_file(str(poscar_path))
                time.sleep(1)
                if (self.buffer_dir / "STOP").exists():
                    logging.info("[stop] Monitoring stopped by STOP file!")
                    return
        except KeyboardInterrupt:
            logging.info("[stop] Monitoring stopped by user!")


def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--buffer', required=True, help='')
    parser.add_argument('--origin', required=True, help='')
    parser.add_argument('--relaxed', required=True, help='')
    parser.add_argument('--error', required=True, help='')
    parser.add_argument('--F_max', default=0.1, type=float, help='')
    parser.add_argument('--N_max', default=500, type=int, help='')
    parser.add_argument('--save_trajectory_info', action='store_true', help='')
    args = parser.parse_args()

    monitor = StructureMonitor(
        buffer_dir=args.buffer,
        origin_dir=args.origin,
        relaxed_dir=args.relaxed,
        error_dir=args.error,
        F_max=args.F_max,
        N_max=args.N_max,
        save_trajectory_info=args.save_trajectory_info,
    )
    monitor.run()


if __name__ == "__main__":
    main()
