import os
import yaml


def load_runtime_config(default_config_path=None):
    config_path = (
        default_config_path if default_config_path else os.getenv("RUNTIME_CONFIG_PATH")
    )
    if not config_path:
        raise ValueError("Environment variable RUNTIME_CONFIG_PATH not set.")
    config = {}
    try:
        with open(config_path, "r", encoding="utf-8") as yaml_str:
            yaml_str = os.path.expandvars(yaml_str.read())
            config = yaml.safe_load(yaml_str)
    except FileNotFoundError as er:
        raise FileNotFoundError(
            f"Runtime config file not found at {config_path}"
        ) from er
    return config


def get_service_config(service_name, default_config_path=None):
    config = load_runtime_config(default_config_path)
    services = config.get("services", {})
    return services.get(service_name, {})
