from cli.utils import ask_if_not_provided
import click

def webui_step(options, default_options, none_interactive, abort):
    """
    Initialize the Web UI configuration.
    """
    if not options.get("rest_api_enabled"):
        click.echo(click.style("Skipping setup for Web UI because REST API was not enabled", bold=False, fg="yellow"))
        return
    
    enabled = ask_if_not_provided(
        options,
        "webui_enabled",
        "Enable Web UI?",
        default_options["webui_enabled"],
        none_interactive=none_interactive,
    )

    if not enabled:
       return
     
    ask_if_not_provided(
        options,
        "webui_listen_port",
        "Server listen port",
        default_options["webui_listen_port"],
        none_interactive,
    )

    ask_if_not_provided(
        options,
        "webui_host",
        "Server host",
        default_options["webui_host"],
        none_interactive,
    )

    click.echo("\nAdditional configuration options are availale for the Web UI such as enabling authentication, collecting feedback etc.")
    click.echo("Please refer to our documentation for detailed setup instructions.\n")
