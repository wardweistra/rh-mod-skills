import click

from rh_mod_skills import __version__
from rh_mod_skills.commands.annotate import annotate
from rh_mod_skills.commands.extract import extract
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.ingest import ingest
from rh_mod_skills.commands.status import status


@click.group()
def main():
    """RH Mod Skills CLI — source models to FHIR logical models."""


@main.command()
def version():
    """Print the CLI version."""
    click.echo(__version__)


main.add_command(init)
main.add_command(ingest)
main.add_command(extract)
main.add_command(annotate)
main.add_command(status)
