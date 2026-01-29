import click
from microgen.constants import DEFAULT_SERVICES
from microgen.generators import create_service, create_root_files, create_root_files_in_service


@click.group()
def cli():
    """Microgen CLI - Generate microservice folder structures"""
    pass


@cli.command()
@click.argument("names", nargs=-1)
@click.option("--all", "all_services", is_flag=True, help="Generate all default microservices & root files")
def create(names, all_services):
    """Create one OR multiple microservices"""

    if all_services:
        names = DEFAULT_SERVICES
        # Create root files at root level for --all
        create_root_files(names)
    else:
        if not names:
            click.echo("ERROR: Provide at least one name or use --all")
            return

    for name in names:
        create_service(name)
        # For single service, create root files inside the service folder
        if not all_services and len(names) == 1:
            create_root_files_in_service(name, names)
        click.echo(f"Created microservice: {name} (with help.md)")
