import click, sys
from .utils import get_version
from .commands import assistant, scan, thread
from .settings import Settings

VERSION = get_version()
CONTEXT_SETTINGS = {"max_content_width": sys.maxsize}

@click.group(context_settings = CONTEXT_SETTINGS)
@click.version_option(str(VERSION), "-v", "--version")
@click.option("--debug", is_flag = True, hidden = True, help = "Enable debug mode")
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    """A tool to use AI to analyze and interact with vectorized data from custom sources of information."""
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug

def register_commands():
    cli.add_command(scan)
    cli.add_command(assistant)
    cli.add_command(thread)

def main():
    Settings.init()
    register_commands()
    cli()
