import click
from deepx_dock._cli.registry import register


@register(
    cli_name="create",
    cli_help="Establish the searching template for the structure generator.",
    cli_args=[
        click.argument(
            'target_dir', type=click.Path(exists=True, writable=True),
        ),
    ],
)
def establish_search_template(target_dir):
    from deepx_dock.design.mattergen_chgnet.establish_template import copy_templates_folder
    copy_templates_folder(target_path=target_dir)

