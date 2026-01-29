import click
from pathlib import Path
from deepx_dock._cli.registry import register


@register(
    cli_name="to-deeph",
    cli_help="Translate VASP output data to DeepH DFT data training set format. (Not yet implemented)",
    cli_args=[
        click.argument('vasp_dir', type=click.Path()),
        click.argument('deeph_dir', type=click.Path()),
    ],
)
def translate_vasp_to_deeph(vasp_dir: Path, deeph_dir: Path):
    click.echo("Not implemented")

