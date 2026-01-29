import click
from pathlib import Path
from deepx_dock._cli.registry import register


@register(
    cli_name="stack",
    cli_help="Generate twisted 2D heterostructures with custom parameters.",
    cli_args=[
        click.argument('prim_poscar1', type=click.Path(exists=True)),
        click.argument('super1_a1_a2', type=str),
        click.argument('prim_poscar2', type=click.Path(exists=True)),
        click.argument('super2_a1_a2', type=str),
        click.option(
            '--next-layer-dis', '-d', type=float, default=2.0,
            help='Distance between twisted layers (in Angstrom).'
        ),
        click.option(
            '--start-z', '-z', type=float, default=0.1,
            help='Starting z-coordinate for the first layer.'
        ),
    ],
)
def create_twisted_2d_heterostructure(
    prim_poscar1: str, super1_a1_a2: str,
    prim_poscar2: str, super2_a1_a2: str,
    next_layer_dis: float = 2.0,
    start_z: float = 0.1,
):
    from deepx_dock.design.twist_2d.twist import Twist2D
    from deepx_dock.design.twist_2d.twist import DEFAULT_OUT_POSCAR
    # Create an object for t2d
    twist_2d = Twist2D()
    
    # Add first layer
    super1_a1_a2 = [int(v) for v in super1_a1_a2.split(',')]
    super1_a1 = super1_a1_a2[:2]
    super1_a2 = super1_a1_a2[2:]
    twist_2d.add_layer(
        super1_a1, super1_a2, 
        next_layer_dis=next_layer_dis, 
        prim_poscar=prim_poscar1
    )
    
    # Add second layer
    super2_a1_a2 = [int(v) for v in super2_a1_a2.split(',')]
    super2_a1 = super2_a1_a2[:2]
    super2_a2 = super2_a1_a2[2:]
    twist_2d.add_layer(
        super2_a1, super2_a2, 
        prim_poscar=prim_poscar2
    )
    
    # Twisting the layers
    twist_2d.twist_layers(start_z=start_z)
    
    # Write results to file in the specified output directory
    twist_2d.write_res_to_poscar()
    
    # Print results if verbose mode is enabled
    click.echo("Twisted 2D structure generated successfully!")
    click.echo(f"Output saved to: {DEFAULT_OUT_POSCAR}")
    click.echo("\nStructure Parameters:")
    click.echo(f"  - Layer distance: {next_layer_dis} Å")
        
    # Calculate and display twisted angles
    click.echo("\nTwisted Angles (degrees):")
    for i, angle in enumerate(twist_2d.twisted_angles):
        click.echo(f"  - Layer {i+1}: {angle:.3f}°")
    
    # Calculate and display strain
    click.echo("\nLayer Strain (volume change):")
    for i, strain in enumerate(twist_2d.layers_strain):
        click.echo(f"  - Layer {i+1}: {strain*100:.2f}%")
    
    return twist_2d

