import os
import click

from cli.config import Config
from cli.utils import load_template, get_display_path


def config_command():
    """Update the config file with new default settings."""
    config_path = Config.user_config_file

    if not os.path.exists(config_path):
        click.echo(
            click.style(
                (
                    "No config file found. "
                    "\n\tRun `solace-agent-mesh init` to generate a new config file."
                ),
                fg="yellow",
            )
        )
        return 1

    config = Config.get_config(config_path)
    Config.write_config(config, config_path)

    click.echo(
        f"Config file updated with latest default configurations at {get_display_path(config_path)}"
    )
