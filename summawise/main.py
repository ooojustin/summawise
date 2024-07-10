import click, sys
from .commands.scan import scan

CONTEXT_SETTINGS = {"max_content_width": sys.maxsize}

@click.group(context_settings = CONTEXT_SETTINGS)
def cli():
    """A tool to use AI to analyze and interact with vectorized data from custom sources of information."""
    pass

def register_commands():
    cli.add_command(scan)

def main():
    register_commands()
    cli()
