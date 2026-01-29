import click
from pathlib import Path
from deepx_dock._cli.registry import register


@register(
    cli_name="single-atom-to-deeph",
    cli_help="Translate the FHI-aims output data of single atom calculation to DeepH DFT data training set format.",
    cli_args=[
        click.argument(
            'aims_dir', type=click.Path(file_okay=False),
        ),
        click.argument(
            'deeph_dir', type=click.Path(file_okay=False),
        ),
        click.option(
            '--tier-num', '-t', type=int, default=0,
            help='The tier number of the aims source data, -1 for [aims_dir], 0 for <aims_dir>/<aims_dir>, 1 for <aims_dir>/<tier1>/<data_dirs>, etc.'
        ),
    ],
)
def translate_vasp_to_deeph(aims_dir: Path, deeph_dir: Path, tier_num: int):
    aims_dir = Path(aims_dir)
    deeph_dir = Path(deeph_dir)
    #
    from deepx_dock.convert.fhi_aims.single_atom_aims_to_deeph import SingleAtomDataTranslatorToDeepH
    translator = SingleAtomDataTranslatorToDeepH(
        aims_dir, deeph_dir, tier_num
    )
    translator.transfer_all_aims_to_deeph()
    click.echo("[done] Translation completed successfully!")

