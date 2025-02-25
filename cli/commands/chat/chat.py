import click
import requests
import os
import json
import pyperclip
import uuid
import base64
import stat

from ...utils import log_error
from ...utils import log_link
from ...utils import log_success

XDG_CONFIG_HOME = os.getenv(
    "XDG_CONFIG_HOME", os.path.expanduser("~/.config/solace_agent_mesh")
)

XDG_DOWNLOAD_DIR = os.getenv(
    "XDG_DOWNLOAD_DIR", os.path.expanduser("~/Downloads/solace_agent_mesh")
)

TOKEN_FILE = os.path.join(XDG_CONFIG_HOME, "token.json")
CONFIG_FILE = os.path.join(XDG_CONFIG_HOME, "setting.conf")


def validate_token(server, access_token):
    """
    Validate the access token with the server.
    """
    response = requests.post(
        f"{server}/is_token_valid",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.status_code


def config_directory():
    """
    Get the configuration directory path.
    """
    return XDG_CONFIG_HOME


def file_directory():
    """
    Get the file directory path.
    """
    return XDG_DOWNLOAD_DIR


def set_permission(file_path):
    """
    Set file permissions to be readable and writable only by the owner.
    """
    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)


def save_configuration(conf: dict):
    """
    Save the server address to the configuration file.
    """
    home_dir = config_directory()

    # Create the home directory if it does not exist
    os.makedirs(home_dir, exist_ok=True)

    # Load existing configuration if it exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            existing_conf = json.load(f)
    else:
        existing_conf = {}

    # Update the existing configuration with new values
    existing_conf.update(conf)

    # Save the updated configuration
    with open(CONFIG_FILE, "w") as f:
        json.dump(existing_conf, f)
    set_permission(CONFIG_FILE)


def save_files(files):
    """
    Save files to the file directory.
    """
    if files:
        file_directory_path = file_directory()
        os.makedirs(file_directory_path, exist_ok=True)
        for file in files:
            file_name = file["name"]
            file_content = file["content"]
            file_type = file["mime_type"]
            if file_type.startswith("image/"):
                # Decode Base64
                file_content = base64.b64decode(file_content)
            else:
                file_content = file_content.encode("utf-8")

            file_path = os.path.join(file_directory_path, file_name)
            with open(file_path, "wb") as f:
                f.write(file_content)
            click.echo(f"File saved in {file_path}")


def chat_command(chat):
    """
    Login and start a chat conversation.
    """

    @chat.command()
    @click.argument("server")
    def login(server):
        """Log in to the solace-agent-mesh application."""
        if not server:
            log_error("Server address is required.")
            return

        # Save the server address
        save_configuration({"auth_server": server})

        try:
            url = f"{server}/login"
            click.secho(
                "\U0001F447 Please authenticate by visiting the following URL:",
                fg="green",
            )
            log_link(url)

            click.prompt(
                click.style(
                    "\U0001F4C4 Copy the entire json object and press Enter (Ctrl+D to exit)",
                    fg="green",
                ),
                default="",
                show_default=False,
            )

            token = pyperclip.paste()

            # Save the response as JSON
            with open(TOKEN_FILE, "w") as f:
                json.dump(json.loads(token), f)
            set_permission(TOKEN_FILE)

            token_data = json.loads(token)

            # Verify the token
            try:
                status_code = validate_token(server, token_data.get("access_token"))
                if status_code == 200:
                    log_success("Login successful.")
                else:
                    log_error("Token is invalid or expired. Please log in again.")
                    return
            except requests.exceptions.RequestException as e:
                log_error(f"Token validation failed: {e}")
                return

        except requests.exceptions.RequestException as e:
            log_error(f"Login failed: {e}")

    @chat.command()
    def logout():
        """Log out from the solace-agent-mesh application."""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            log_success("Logout successful.")
        else:
            log_error("No active session found.")

    @chat.command()
    @click.option(
        "-s",
        "--stream",
        is_flag=True,
        help="Stream mode.",
        default=False,
    )
    @click.option(
        "-a",
        "--auth",
        is_flag=True,
        help="Enable authentication.",
        default=False,
    )
    @click.option(
        "-u",
        "--url",
        help="Chat endpoint url (e.g., https://<server>/api/v1/request).",
    )
    @click.option(
        "-f",
        "--file",
        type=click.Path(exists=True, dir_okay=False, resolve_path=True),
        multiple=True,
        help="Attach files to the chat. Use -f or --file for each file.",
    )
    def start(stream, auth, url, file):
        """Establish a chat with solace-agent-mesh plugin application."""

        # Load the rest server address
        rest_server = None
        if url is not None:
            # save the server address
            rest_server = url
            save_configuration({"rest_api_server": rest_server})
        elif os.path.exists(CONFIG_FILE):
            # load the server address from the configuration file
            with open(CONFIG_FILE, "r") as f:
                setting_data = json.load(f)
                rest_server = setting_data.get("rest_api_server", None)
        if rest_server is None:
            rest_server = click.prompt(
                click.style(
                    "💬 Enter the server address (e.g., https://<server>/api/v1/request): ",
                    fg="green",
                )
            )
            # Save the server address
            save_configuration({"rest_api_server": rest_server})

        session_id = str(uuid.uuid4())
        rest_endpoint_headers = {}

        # Authenticate if it is enabled
        if auth:
            # Load authentication server
            with open(CONFIG_FILE, "r") as f:
                setting_data = json.load(f)
                auth_server = setting_data.get("auth_server", "")
                if not auth_server:
                    log_error(
                        "Authentication server not found. Please log in using 'sam login <server name>'."
                    )
                    return

            # Load the token
            if not os.path.exists(TOKEN_FILE):
                log_error(
                    "Token not found. Please log in using 'sam login <server name>'."
                )
                return

            try:
                with open(TOKEN_FILE, "r") as f:
                    token_data = json.load(f)
                    access_token = token_data.get("access_token")
                    refresh_token = token_data.get("refresh_token")

                    if access_token and refresh_token:
                        # Validate token
                        try:
                            status_code = validate_token(auth_server, access_token)
                            if status_code != 200:
                                # Refresh token
                                response = requests.post(
                                    f"{auth_server}/refresh_token",
                                    headers={
                                        "Content-Type": "application/json",
                                        "Authorization": f"Bearer {access_token}",
                                    },
                                    json={"refresh_token": refresh_token},
                                )
                                if response.status_code == 200:
                                    access_token = response.json()
                                else:
                                    log_error(
                                        "Failed to refresh token. Please log in again."
                                    )
                                    return
                            rest_endpoint_headers = {
                                "Authorization": f"Bearer {access_token}"
                            }
                        except requests.exceptions.RequestException as e:
                            log_error(f"Token validation failed: {e}")
                            return
                    else:
                        log_error(
                            "Invalid token data. Please log in again using 'sam login <server name>'."
                        )
                        return
            except Exception as e:
                log_error(
                    f"Token data not found: {e}. Please log in again using 'sam login <server name>'."
                )
                return

        try:
            files_to_send = []
            if file:
                for file_path in file:
                    file_name = os.path.basename(file_path)
                    files_to_send.append(("files", (file_name, open(file_path, "rb"))))

            while True:
                user_prompt = click.prompt(
                    click.style("💬 How can I help you? (Ctrl+D to exit)", fg="green")
                )
                # Exit the chat
                if user_prompt.lower() == "exit":
                    break
                    # Skip empty prompts
                if not user_prompt.strip():
                    continue

                try:
                    response = requests.post(
                        f"{rest_server}",
                        headers=rest_endpoint_headers,
                        data={
                            "prompt": user_prompt,
                            "stream": stream,
                            "session_id": session_id,
                        },
                        files=files_to_send,
                    )
                    response.raise_for_status()

                    if stream:
                        buffer = ""
                        for chunk in response.iter_content(chunk_size=1):
                            utf_chunk = chunk.decode("utf-8")
                            buffer += utf_chunk

                            while "\n\n" in buffer:
                                split_chunk = buffer.split("\n\n", 1)
                                data_chunk = split_chunk[0]
                                buffer = split_chunk[1]

                                if data_chunk == "data: [DONE]":
                                    break
                                data = json.loads(data_chunk[6:])
                                content = data.get("content", "")
                                if content:
                                    click.echo(content, nl=False)
                                status_message = data.get("status_message", "")
                                if status_message:
                                    click.secho(status_message, nl=True, fg="yellow")
                                # Save files
                                if "files" in data:
                                    files = data["files"]
                                    save_files(files)
                    else:
                        data = response.json()
                        click.echo(f"{data['response']['content']}")
                        # Save files
                        if "files" in data["response"]:
                            files = data["response"]["files"]
                            save_files(files)
                    click.echo("\n")

                except requests.exceptions.RequestException as e:
                    log_error(f"Request failed: {e}")
                    return

        except json.JSONDecodeError:
            log_error(
                "Sorry! I could not response to your request. Please try again later."
            )
            return
