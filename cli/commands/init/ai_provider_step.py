import click

from cli.utils import ask_if_not_provided


def ai_provider_step(options, default_options, none_interactive, abort):
    """
    Initialize the AI provider.
    """
    ask_if_not_provided(
        options,
        "llm_endpoint_url",
        "Provide LLM endpoint URL",
        default_options["llm_endpoint_url"],
        none_interactive,
    )

    ask_if_not_provided(
        options,
        "llm_api_key",
        "Provide LLM API Key",
        default_options["llm_api_key"],
        none_interactive,
        hide_input=True,
    )
    click.echo(
        click.style(
            (
                "The model name should follow the format `provider/model-name`."
                "\n\t For example: openai/gpt-4o or openai/my-model-that-follows-openai-api"
            ),
            fg="yellow",
        )
    )
    ask_if_not_provided(
        options,
        "llm_model_name",
        "Provide LLM model name to use",
        default_options["llm_model_name"],
        none_interactive,
    )

    ask_if_not_provided(
        options,
        "embedding_endpoint_url",
        "Provide Embedding endpoint URL",
        default_options["embedding_endpoint_url"],
        none_interactive,
    )

    ask_if_not_provided(
        options,
        "embedding_api_key",
        "Provide Embedding API Key",
        default_options["embedding_api_key"],
        none_interactive,
        hide_input=True,
    )

    click.echo(
        click.style(
            (
                "The model name should follow the format `provider/model-name`."
                "\n\t For example: openai/text-embedding-ada-002 or openai/my-model-that-follows-openai-api"
            ),
            fg="yellow",
        )
    )

    ask_if_not_provided(
        options,
        "embedding_model_name",
        "Provide Embedding model name to use",
        default_options["embedding_model_name"],
        none_interactive,
    )
