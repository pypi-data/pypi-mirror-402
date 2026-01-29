import click
from microgen.constants import DEFAULT_SERVICES
from microgen.generators import create_service, create_root_files


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

    if not names:
        click.echo("ERROR: Provide at least one name or use --all")
        return

    # Create root files with only the services being created
    create_root_files(names)

    for name in names:
        create_service(name)
        click.echo(f"Created microservice: {name} (with help.md)")
