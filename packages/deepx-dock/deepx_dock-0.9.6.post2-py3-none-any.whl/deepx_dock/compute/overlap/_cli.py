import click
from pathlib import Path
from deepx_dock._cli.registry import register


# ------------------------------------------------------------------------------
@register(
    cli_name="calc",
    cli_help="Calculate the overlap matrix with the given basis and atomic structure.",
    cli_args=[
        click.argument('data_dir', type=click.Path()),
        click.argument('basis_dir', type=click.Path()),
        click.argument('code', type=str),
        click.option(
            '--spinful', '-s', is_flag=True,
            help='Consider spin degree of freedom.',
        ),
    ],
)
def calc_overlap(poscar_dir: Path, basis_dir: Path, code: str, spinful: bool = False):
    from HPRO.io.struio import from_poscar
    from HPRO.io.aodata import AOData
    from HPRO.io.hrloader import read_vnloc
    from HPRO.v2h.vkb import calc_vkb, get_nloc_pairs
    from HPRO.matao.matao import MatAO
    from HPRO.io.deephio import save_mat_deeph
    from deepx_dock.compute.overlap.overlap import calc_overlap as calc_olp
    
    assert code in ['siesta'], f'Unsupported code: {code}'
    with open(f'{poscar_dir}/POSCAR', 'r') as f:
        structure = from_poscar(f)
    aodata = AOData(structure, basis_path_root=basis_dir, aocode=code)
    olp_basis = calc_olp(aodata)
    Dij, Qij, projR = read_vnloc(structure, basis_dir, interface='code')
    if Qij is not None:
        olp_proj_ao = calc_overlap(projR, aodata2=aodata, Ecut=100, kind=1)
        dOkb = calc_vkb(olp_proj_ao, Qij)
        overlaps = olp_basis + dOkb
    else:
        nloc_pairs = get_nloc_pairs(structure, projR.cutoffs, aodata.cutoffs)
        dOkb = MatAO.init_mats(nloc_pairs, aodata, filling_value=0., dtype='f8')
        overlaps = olp_basis + dOkb
    if spinful:
        overlaps.spinless_to_spinful()
        
    save_mat_deeph(poscar_dir, overlaps, 'o')
