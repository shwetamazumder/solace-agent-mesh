import os
import http.server
import socketserver
import socket
import click
import json

from cli.utils import get_cli_root_dir, log_error


def get_local_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external address, doesn't send any packets, just determines IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "localhost"
    finally:
        s.close()
    return ip


def get_wss_url(url: str) -> str:
    """Get the WSS URL from a WS URL."""
    if url.startswith("ws://") or url.startswith("wss://"):
        return url
    elif url.startswith("tcp://"):
        url = url.replace("tcp://", "ws://")
        # Change port to 443
        if len(url.split(":")) > 1:
            url = url.split(":")
            url[-1] = "443"
            url = ":".join(url)
    elif url.startswith("tcps://"):
        url = url.replace("tcps://", "wss://")
        # Change port to 443
        if len(url.split(":")) > 1:
            url = url.split(":")
            url[-1] = "443"
            url = ":".join(url)
    return url


def visualizer_command(port, find_unused_port=False, host=False, use_env=False):
    """Runs a GUI web-based visualizer for inspecting events inside the solace agent mesh."""
    config = click.get_current_context().obj["solace_agent_mesh"]
    if use_env:
        try:
            from dotenv import load_dotenv

            env_file = config["env_file"]
            load_dotenv(env_file, override=True)
        except ImportError:
            log_error(
                "Failed to import dotenv. Please install it using 'pip install python-dotenv'"
            )
            return 1
        except Exception as e:
            log_error(f"Failed to load environment variables. {e}")
            return 1

    visualizer_directory = os.path.join(get_cli_root_dir(), "assets", "web-visualizer")
    # Check if the visualizer directory exists
    if not os.path.exists(visualizer_directory):
        visualizer_directory = os.path.join(
            get_cli_root_dir(), "web-visualizer", "dist"
        )
        if not os.path.exists(visualizer_directory):
            log_error("Error: Built Web-Visualizer directory not found.")
            return 1

    # Find an unused port if the specified port is in use
    while True:
        # Check if port is available
        try:
            with socketserver.TCPServer(("localhost", port), None) as s:
                pass
        except OSError:
            log_error(f"Error: Port {port} is already in use.")
            if find_unused_port:
                port += 1
                click.echo(f"Trying port {port}...")
                continue
            else:
                return 1
        break

    # Change the current working directory to the visualizer directory
    os.chdir(visualizer_directory)

    # Write the Solace broker configuration to a file for client pickup
    config = {
        "url": get_wss_url(os.getenv("SOLACE_BROKER_URL", "")),
        "username": os.getenv("SOLACE_BROKER_USERNAME", ""),
        "password": os.getenv("SOLACE_BROKER_PASSWORD", ""),
        "vpn": os.getenv("SOLACE_BROKER_VPN", ""),
        "namespace": os.getenv("SOLACE_AGENT_MESH_NAMESPACE", ""),
    }
    with open("config.json", "w") as f:
        json.dump(config, f)

    # Set up a handler to serve files from the specified directory
    handler = http.server.SimpleHTTPRequestHandler

    # Determine the host binding
    if host:
        # Bind to '0.0.0.0' to expose to the network
        bind_address = "0.0.0.0"
        local_ip = get_local_ip()  # Get local network IP address
    else:
        # Bind to 'localhost' to restrict access to the local machine
        bind_address = "localhost"
        local_ip = "localhost"

    # Start the server
    with socketserver.TCPServer((bind_address, port), handler) as httpd:
        click.echo(f"Serving solace-agent-mesh web-visualizer.")
        click.echo(
            click.style(f"\tLocal: http://localhost:{port}", bold=True, fg="blue")
        )
        click.echo(
            click.style(
                "\tNetwork: "
                + (f"http://{local_ip}:{port}" if host else "use --host to expose"),
                bold=True,
                fg="blue",
            )
        )
        click.echo("Press Ctrl+C to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("Shutting down server.")
            httpd.shutdown()
        finally:
            os.remove("config.json")
