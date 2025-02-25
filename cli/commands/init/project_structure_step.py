from cli.utils import ask_if_not_provided


def project_structure_step(options, default_options, none_interactive, abort):
    """
    Initialize the project structure.
    """
    namespace = ask_if_not_provided(
        options,
        "namespace",
        "Enter a namespace for the project (It will be used as the topic prefix for all events.)",
        default_options["namespace"],
        none_interactive,
    )
    if namespace and not namespace.endswith("/"):
        options["namespace"] = f"{namespace}/"

    ask_if_not_provided(
        options,
        "config_dir",
        "Enter base directory for config files",
        default_options["config_dir"],
        none_interactive,
    )
    ask_if_not_provided(
        options,
        "module_dir",
        "Enter base directory for python modules",
        default_options["module_dir"],
        none_interactive,
    )
    ask_if_not_provided(
        options,
        "build_dir",
        "Enter base directory for the build output",
        default_options["build_dir"],
        none_interactive,
    )
    ask_if_not_provided(
        options,
        "env_file",
        "Enter environment file path",
        default_options["env_file"],
        none_interactive,
    )
