import click, sys
from .commands import scan, assistant
from .settings import Settings

CONTEXT_SETTINGS = {"max_content_width": sys.maxsize}

@click.group(context_settings = CONTEXT_SETTINGS)
def cli():
    """A tool to use AI to analyze and interact with vectorized data from custom sources of information."""
    pass

def register_commands():
    cli.add_command(scan)
    cli.add_command(assistant)

def main():
    Settings.init()
    register_commands()
    cli()
