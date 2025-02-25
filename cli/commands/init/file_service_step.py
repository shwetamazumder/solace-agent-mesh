import click

from cli.utils import ask_if_not_provided, get_display_path


def file_service_step(options, default_options, none_interactive, abort):
    """
    Initialize the file service.
    """
    provider = ask_if_not_provided(
        options,
        "file_service_provider",
        (
            "Choose a file service provider\n"
            "\t-  Volume: Use a local volume (directory) to store files\n"
            "\t-  Bucket: Use a cloud bucket to store files (Must use AWS S3 API)\n"
            "Enter the provider"
        ),
        default_options["file_service_provider"],
        none_interactive,
        ("volume", "bucket"),
    )

    configs = {}
    if "file_service_config" in options and options["file_service_config"]:
        config_list = list(options["file_service_config"])
        for config in config_list:
            if "=" in config:
                key, value = config.split("=")
                configs[key] = value

    default_config = {
        "directory": "/tmp/solace-agent-mesh"
    }
    for config in default_options["file_service_config"]:
        if "=" in config:
            key, value = config.split("=")
            default_config[key] = value

    if provider == "volume":
        ask_if_not_provided(
            configs,
            "directory",
            "Provide the path to the volume directory",
            default_config.get("directory"),
            none_interactive,
        )
    elif provider == "bucket":
        ask_if_not_provided(
            configs,
            "bucket_name",
            "Provide the name of the bucket",
            default_config.get("bucket_name"),
            none_interactive,
        )
        # endpoint_url
        ask_if_not_provided(
            configs,
            "endpoint_url",
            "Provide the endpoint URL",
            default_config.get("endpoint_url", ""),
            none_interactive,
        )
        click.echo(
            click.style(
                f"You can setup the Boto3 authentication configuration in the {get_display_path('solace-agent-mesh.yaml')} file",
                fg="yellow",
            )
        )

    options["file_service_config"] = [
        f"{key}={value}" for key, value in configs.items()
    ]
