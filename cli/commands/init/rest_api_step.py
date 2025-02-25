from cli.utils import ask_if_not_provided
import click

def rest_api_step(options, default_options, none_interactive, abort):
    """
    Initialize the REST API.
    """

    enabled = ask_if_not_provided(
        options,
        "rest_api_enabled",
        "Set up the REST API interface? (Required for Web UI setup in the next step.)",
        default_options["rest_api_enabled"],
        none_interactive,
    )

    if not enabled:
       return
    
    ask_if_not_provided(
        options,
        "rest_api_server_input_port",
        "REST API server port",
        default_options["rest_api_server_input_port"],
        none_interactive,
    )
    ask_if_not_provided(
        options,
        "rest_api_server_host",
        "REST API server host", 
        default_options["rest_api_server_host"],
        none_interactive,
    )
    ask_if_not_provided(
        options,
        "rest_api_server_input_endpoint",
        "REST API endpoint",
        default_options["rest_api_server_input_endpoint"],
        none_interactive,
    )
    ask_if_not_provided(
        options,
        "rest_api_gateway_name",
        "What would you like to call the gateway",
        default_options["rest_api_gateway_name"],
        none_interactive,
    )

    click.echo("\nAdditional configuration options are availale for the REST API such as enabling authentication, rate limits etc.")
    click.echo("Please refer to our documentation for detailed setup instructions.\n")
