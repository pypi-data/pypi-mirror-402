import click
from typing import Tuple
from deepx_dock._cli.registry import register


# ------------------------------------------------------------------------------
@register(
    cli_name="gen",
    cli_help="Generate transformed structures for equivariance testing",
    cli_args=[
        click.argument(
            'poscar_dir',
            type=click.Path(exists=True, file_okay=False, readable=True),
        ),
        click.option(
            '--generate-num', '-n',
            type=click.IntRange(1, 1024),
            default=64,
            show_default=True,
            help='The number of translated and rotated structures.'
        ),
        click.option(
            '--rot-mode', '-r',
            type=click.Choice(['0', '1', '2', '3']),
            default='1',
            show_default=True,
            help='Rotation mode: 0 - no rotation, 1 - rotate coordinates only, 2 - rotate lattice only, 3 - both rotate coordinates and lattice.'
        ),
        click.option(
            '--translate', is_flag=True,
            help='Translate the structure.'
        ),
        click.option(
            '--move-to-origin', is_flag=True,
            help='Move the mass center to origin.'
        ),
        click.option(
            '--dump-decimals', type=int, default=-1,
            help='The decimals of coordinates and lattice when dumping, -1 for no rounding.'
        ),
    ],
)
def generate_structure(
    poscar_dir: str, generate_num: int, rot_mode: str,
    translate: bool, move_to_origin: bool, dump_decimals: int,
):
    from deepx_dock.analyze.dft_equiv.gen_struct import gen_struct
    if_rot_coord = (rot_mode == "1") or (rot_mode == "3")
    if_rot_lat = (rot_mode == "2") or (rot_mode == "3")
    gen_struct(
        poscar_dir=poscar_dir,
        generate_num=generate_num,
        if_rot_coord=if_rot_coord,
        if_rot_lat=if_rot_lat,
        if_translate=translate,
        if_move_to_origin=move_to_origin,
        dump_decimals=dump_decimals
    )


# ------------------------------------------------------------------------------
@register(
    cli_name="test",
    cli_help="Test data equivariance with translated and rotated structures",
    cli_args=[
        click.argument(
            'poscar_dir',
            type=click.Path(exists=True, file_okay=False, readable=True),
        ),
        click.option(
            '--target', '-t', type=str, default='hamiltonian',
            help='The file name for test, <target>.h5.'
        ),
        click.option(
            '--cell-index', '-R', type=(int, int, int), default=(0, 0, 0),
            help='The selected cell index for test.'
        ),
        click.option(
            '--atom-pair', '-P', type=(int, int), default=(-1, -1),
            help='The selected atom pair for test, (-1, -1) for all atom pairs.'
        ),
    ],
)
def test_equivariance(
    poscar_dir: str, target: str, cell_index: Tuple[int, int, int],
    atom_pair: Tuple[int, int],
):
    from deepx_dock.analyze.dft_equiv.test_equiv import test_equiv
    test_equiv(
        dft_dir=poscar_dir,
        target=target,
        R=cell_index,
        pair=atom_pair
    )

