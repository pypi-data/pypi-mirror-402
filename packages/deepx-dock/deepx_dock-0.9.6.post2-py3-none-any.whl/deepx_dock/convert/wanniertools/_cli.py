import click
from pathlib import Path
from deepx_dock._cli.registry import register


@register(
    cli_name="from-deeph",
    cli_help="Translate DeepH DFT data to WanneirTools format (Not yet implemented)",
    cli_args=[
        click.argument('deeph_dir', type=click.Path()),
        click.argument('wt_dir', type=click.Path()),
    ],
)
def translate_deeph_to_wt(deeph_dir: Path, wt_dir: Path):
    click.echo("Not implemented")

