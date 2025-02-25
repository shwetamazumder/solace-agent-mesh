import click

from .agent import add_agent_command
from .gateway import add_gateway_command, add_interface_command
from .copy_from_plugin import copy_from_plugin
from ...config import Config
from ...utils import log_error


def add_command(add):
    @add.command()
    @click.argument("name")
    @click.option(
        "-c",
        "--copy-from",
        help="Name of the plugin. Copying over an agent config from an existing plugin instead of creating a new one to allow for customization. If your desired agent name is different from the source agent name, use the format <plugin>:<source_agent_name>",
    )
    def agent(name, copy_from):
        """
        Creates a template for an agent.

        name: Name of the component to create. Must be kebab-case. (don't add 'agent' to the name)
        """
        if copy_from:
            return copy_from_plugin(name, copy_from, "agents")
        return add_agent_command(name)

    @add.command()
    @click.argument("name")
    @click.option(
        "-i",
        "--interface",
        help="The interface(s) to add to the gateway. For example, to add rest and slack interfaces use: --interface slack --interface rest-api",
        multiple=True,
    )
    @click.option(
        "-c",
        "--copy-from",
        help="Name of the plugin. Copying over a gateway configs from an existing plugin instead of creating a new one to allow for customization. If your desired gateway name is different from the source gateway name, use the format <plugin>:<source_gateway_name>",
    )
    @click.option(
        "-n",
        "--new-interface",
        default=False,
        is_flag=True,
        help="Create a new gateway interface - supported only in plugin projects.",
    )
    def gateway(
        name,
        interface,
        copy_from,
        new_interface,
    ):
        """
        Creates a template for a gateway.

        name: Name of the component to create. Must be kebab-case. (don't add 'gateway' to the name)

        If no interfaces is provided, a gateway from scratch will be created.
        """
        interface = list(interface)

        if new_interface and interface:
            log_error(
                "Error: The --new-interface/-n flag is supported only when no interfaces are provided."
            )
            return 1
        
        if copy_from and interface:
            log_error(
                "Error: The --copy-from/-c flag is supported only when no interfaces are provided."
            )
        
        # Copy from plugin
        if copy_from:
            return copy_from_plugin(name, copy_from, "gateways")
        
        # Creating a new gateway interface
        if new_interface:
            if not Config.is_plugin_project():
                log_error(
                    "Error: The --new-interface flag is supported only in plugin projects."
                )
                return 1
            return add_interface_command(name)
        
        # Create a new gateway from an interface
        return add_gateway_command(name, interface)
