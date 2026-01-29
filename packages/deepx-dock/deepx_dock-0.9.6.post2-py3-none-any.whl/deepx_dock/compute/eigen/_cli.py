import os
from pathlib import Path
import click
from deepx_dock._cli.registry import register

from deepx_dock.CONSTANT import DEEPX_BAND_FILENAME, DEEPX_K_PATH_FILENAME


def set_environ(thread_num):
    os.environ["OMP_NUM_THREADS"] = str(thread_num)
    os.environ["MKL_NUM_THREADS"] = str(thread_num)
    os.environ["OPENBLAS_NUM_THREADS"] = str(thread_num)
    os.environ["NUMEXPR_NUM_THREADS"] = str(thread_num)
    os.environ["VECLIB_MAXIMUM_THREADS"] = str(thread_num)


# ------------------------------------------------------------------------------
@register(
    cli_name="calc-band",
    cli_help="Calculate the energy band and save it into h5 file.",
    cli_args=[
        click.argument(
            'data_path',
            type=click.Path(exists=True, file_okay=False, readable=True),
        ),
        click.option(
            '--parallel-num', '-p', type=int, default=-1,
            help='The parallel processing number, -1 for using all of the cores.'
        ),
        click.option(
            "--thread-num", type=int, default=1,
            help='Number of threads for each k-point.'
        ),
        click.option(
            "--sparse-calc", is_flag=True,
            help="Use sparse diagonalization."
        ),
        click.option(
            "--num-band", type=int, default=50,
            help="Number of bands when using sparse diagonalization."
        ),
        click.option(
            "--E-min", "--min", type=float, default=-0.5,
            help="Lowest band energy (from the fermi level) when using sparse diagonalization."
        ),
        click.option(
            "--maxiter", type=int, default=300,
            help="Max number of iterations when using sparse diagonalization."
        ),
    ],
)
def calc_band(
    data_path, parallel_num, num_band, e_min, maxiter, sparse_calc, thread_num,
):
    data_path = Path(data_path).resolve()
    band_data_path = data_path / DEEPX_BAND_FILENAME
    k_path_path = data_path / DEEPX_K_PATH_FILENAME
    with open(k_path_path, 'r') as f:
        k_list_spell = f.read()
    band_conf = {
        "k_list_spell" : k_list_spell,
        "num_band": num_band,
        "lowest_band_energy": e_min,
        "maxiter": maxiter,
    }
    #
    set_environ(thread_num)
    from deepx_dock.compute.eigen.hamiltonian import HamiltonianObj
    from deepx_dock.compute.eigen.band import BandDataGenerator
    obj_H = HamiltonianObj(data_path)
    bd_gen = BandDataGenerator(obj_H, band_conf)
    bd_gen.calc_band_data(k_process_num=parallel_num, sparse_calc=sparse_calc)
    bd_gen.dump_band_data(band_data_path)


# ------------------------------------------------------------------------------
@register(
    cli_name="plot-band",
    cli_help="Plot energy band with the h5 file that is calculated already.",
    cli_args=[
        click.argument(
            'data_path',
            type=click.Path(exists=True, file_okay=False, readable=True),
        ),
        click.option(
            "--energy-window", "--E-win", type=(float, float), default=(-5, 5),
            help="Plot band energy window (respect to fermi energy)."
        ),
    ],
)
def plot_band_data(data_path, energy_window):
    data_path = Path(data_path).resolve()
    band_data_path = data_path / DEEPX_BAND_FILENAME
    #
    from deepx_dock.compute.eigen.band import BandPlotter
    bd_plotter = BandPlotter(band_data_path)
    bd_plotter.plot(Emin=energy_window[0], Emax=energy_window[1])


# ------------------------------------------------------------------------------
@register(
    cli_name="find-fermi",
    cli_help="Find the Fermi energy using the number of occupied electrons.",
    cli_args=[
        click.argument(
            'data_path',
            type=click.Path(exists=True, file_okay=False, readable=True),
        ),
        click.option(
            "--parallel-num", "-p", type=int, default=1,
            help="Number of processes for k-points."
        ),
        click.option(
            "--thread-num", type=int, default=1,
            help="Number of threads for each k-point."
        ),
        click.option(
            "--method", type=click.Choice(['counting', 'tetrahedron']),
            default='counting',
            help="Calculating method that is used for obtaining DOS."
        ),
        click.option(
            "--kp-density", "-d", type=float, default=0.1,
            help="The density of the k points."
        ),
        click.option(
            '--cache-res', is_flag=True,
            help='Cache the eigenvalues so that you can save time in the subsequent DOS calculation.'
        ),
    ],
)
def find_fermi_energy(
    data_path, parallel_num, thread_num, method, kp_density, cache_res
):
    data_path = Path(data_path).resolve()
    #
    set_environ(thread_num)
    from deepx_dock.compute.eigen.hamiltonian import HamiltonianObj
    from deepx_dock.compute.eigen.fermi_dos import FermiEnergyAndDOSGenerator
    obj_H = HamiltonianObj(data_path)
    fd_fermi = FermiEnergyAndDOSGenerator(data_path, obj_H)
    fd_fermi.find_fermi_energy(
        dk=kp_density, k_process_num=parallel_num, method=method
    )
    fd_fermi.dump_fermi_energy()
    if cache_res and fd_fermi.eigvals is not None:
        fd_fermi.dump_eigval_data()


# ------------------------------------------------------------------------------
@register(
    cli_name="calc-dos",
    cli_help="Calc and plot the density of states.",
    cli_args=[
        click.argument(
            'data_path',
            type=click.Path(exists=True, file_okay=False, readable=True),
        ),
        click.option(
            "--parallel-num", "-p", type=int, default=1,
            help="Number of processes for k-points."
        ),
        click.option(
            "--thread-num", type=int, default=1,
            help="Number of threads for each k-point."
        ),
        click.option(
            "--method", type=click.Choice(['gaussian', 'tetrahedron']),
            default="gaussian",
            help="Calculating method that is used for obtaining DOS."
        ),
        click.option(
            "--kp-density", "-d", type=float, default=0.1,
            help="The density of the k points."
        ),
        click.option(
            "--energy-window", "--E-win", type=(float, float), default=(-5, 5),
            help="Plot band energy window (respect to fermi energy)."
        ),
        click.option(
            "--smearing", "-s", type=float, default=-1.0,
            help="The smearing width (eV) in gaussian method."
        ),
        click.option(
            "--energy-num", "--num", type=int, default=201,
            help="Number of energy points."
        ),
        click.option(
            '--cache-res', is_flag=True,
            help='Cache the eigenvalues so that you can save time in the next same task.'
        ),
    ],
)
def calc_dos_from_H(
    data_path, parallel_num, thread_num, method, kp_density, energy_window,
    energy_num, smearing, cache_res
):
    data_path = Path(data_path).resolve()
    #
    set_environ(thread_num)
    from deepx_dock.compute.eigen.hamiltonian import HamiltonianObj
    from deepx_dock.compute.eigen.fermi_dos import FermiEnergyAndDOSGenerator
    obj_H = HamiltonianObj(data_path)
    fd_fermi = FermiEnergyAndDOSGenerator(data_path, obj_H)
    fermi_method = "counting" if "gaussian" == method else method
    fd_fermi.find_fermi_energy(
        dk=kp_density, k_process_num=parallel_num, 
        method=fermi_method
    )
    fd_fermi.dump_fermi_energy()
    fd_fermi.calc_dos(
        dk=kp_density, k_process_num=parallel_num, 
        emin=energy_window[0], emax=energy_window[1], enum=energy_num,
        method=method, sigma=smearing
    )
    if cache_res:
        fd_fermi.dump_eigval_data()
    fd_fermi.dump_dos_data()
    fd_fermi.plot_dos_data(plot_format="png", dpi=300)

