import os
from cli.commands.add.gateway import add_gateway_command

def create_if_not_exists(file_path, content):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)


def add_pair_to_file_if_not_exists(file_path, pairs):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    for key, value in pairs:
        if key not in content:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"{key}{value}\n")


def create_other_project_files_step(options, default_options, none_interactive, abort):
    """
    Creates the other project files. i.e. .gitignore, .env, requirements.txt, etc.
    """
    # Create .gitignore file
    ignore = (
        "*.pyc\n"
        "__pycache__\n"
        ".env\n"
        ".venv\n"
        "env/\n"
        "venv/\n"
        "log\n"
        f"{options['env_file']}\n"
        f"{options['build_dir']}\n"
    )
    create_if_not_exists(".gitignore", ignore)

    # Create requirements.txt file
    required_dependencies = [
        ("solace-agent-mesh", "~=0.1.0"),
    ]
    create_if_not_exists("requirements.txt", "")
    add_pair_to_file_if_not_exists("requirements.txt", required_dependencies)

    # Create .env file
    required_env_variables = [
        ("SOLACE_AGENT_MESH_NAMESPACE", f"={options['namespace']}"),
        ("SOLACE_DEV_MODE", f"={options['dev_mode']}"),
        ("SOLACE_BROKER_URL", f"={options['broker_url']}"),
        ("SOLACE_BROKER_VPN", f"={options['broker_vpn']}"),
        ("SOLACE_BROKER_USERNAME", f"={options['broker_username']}"),
        ("SOLACE_BROKER_PASSWORD", f"={options['broker_password']}"),
        ("LLM_SERVICE_API_KEY", f"={options['llm_api_key']}"),
        ("LLM_SERVICE_ENDPOINT", f"={options['llm_endpoint_url']}"),
        ("LLM_SERVICE_PLANNING_MODEL_NAME", f"={options['llm_model_name']}"),
        ("EMBEDDING_SERVICE_MODEL_NAME", f"={options['embedding_model_name']}"),
        ("EMBEDDING_SERVICE_API_KEY", f"={options['embedding_api_key']}"),
        ("EMBEDDING_SERVICE_ENDPOINT", f"={options['embedding_endpoint_url']}"),
        ("RUNTIME_CONFIG_PATH", f"={options['build_dir']}/config.yaml"),
    ]

    if options.get("rest_api_enabled"):
        #REST API env variables
        rest_api_env_variables = [
            ("REST_API_SERVER_INPUT_PORT", f"={options.get('rest_api_server_input_port', '')}"),
            ("REST_API_SERVER_HOST", f"={options.get('rest_api_server_host', '')}"),
            ("REST_API_SERVER_INPUT_ENDPOINT", f"={options.get('rest_api_server_input_endpoint', '')}"),
        ]

        required_env_variables.extend(rest_api_env_variables)

    if options.get("webui_enabled"):
        webui_env_variables = [
            #Web UI env variables
            ("WEBUI_ENABLED", f"={options['webui_enabled']}"),
            ("WEBUI_PORT", f"={options['webui_listen_port']}"),
            ("WEBUI_HOST", f"={options['webui_host']}"),
            ("WEBUI_RESPONSE_API_URL", f"=http://{options['rest_api_server_host']}:{options['rest_api_server_input_port']}{options['rest_api_server_input_endpoint']}"),
            ("WEBUI_FRONTEND_SERVER_URL", f"=http://{options['webui_host']}:{options['webui_listen_port']}"),
            ("WEBUI_FRONTEND_URL", f"=http://{options['webui_host']}:{options['webui_listen_port']}"),
        ]

        required_env_variables.extend(webui_env_variables)

    env_var_list = [
        *default_options.get("env_var", []),
        *list(options.get("env_var", [])),
    ]
    for env_var in env_var_list:
        if "=" in env_var:
            key, value = env_var.split("=")
            required_env_variables.append((key, f"={value}"))

    create_if_not_exists(options["env_file"], "")
    add_pair_to_file_if_not_exists(options["env_file"], required_env_variables)
    add_gateway_command(options["rest_api_gateway_name"],["rest-api"])
