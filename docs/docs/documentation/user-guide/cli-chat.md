---
title: CLI Chat
sidebar_position: 50
---

# CLI Chat

In this tutorial, you will learn how to configure a command-line chat interface and integrate it with Solace Agent Mesh. This chat allows you to communicate with Solace Agent Mesh through your terminal.

:::info[Learn about agents]
We recommend reading about [CLI](../concepts/cli.md) before starting this tutorial.
:::

## Setting Up the Environment

First, you need to [install the Solace Agent Mesh SDK and CLI](../getting-started/installation.md). Then, you'll need to [create a new SAM project](../getting-started/quick-start.md).

## Setup REST Interface

The CLI chat uses the REST interface to communicate with the Solace Agent Mesh. Depending on your REST interface settings, the CLI chat may need to authenticate using the REST interface authentication endpoint.

You can configure the CLI chat during the creation of a new SAM project. You'll need to set the host, port, and endpoint of the REST interface, which together form a URL. During installation, you can enable authentication by adding the required authentication configuration to the `.env` file. The authentication is disabled by default. If authentication is enabled, you'll need to log in to SAM; otherwise, login is not required.

## Running the CLI Chat

If authentication is enabled in the REST interface, you must log in using the following command before starting a chat:

```sh
sam chat login SERVER
```

- Replace `SERVER` with your authentication host address. 
- This command provides a URL for OAuth2.0 authentication. Click the URL and authenticate in your browser to generate a token in JSON format. 
- Copy the JSON object.
- Press Enter in the terminal to paste and save the token.

After successfully logging in, start a chat with:

```sh
sam chat start -a
```

The `-a` argument ensures each chat session is authenticated in the background. If authentication is not configured, omit this argument.
During your first chat session after login, the command will ask for the REST interface's endpoint. Subsequent chats will reuse the saved endpoint information until you log out.
The token is automatically renewed using the refresh token in the background, so you only need to log in once. If you no longer need the token, you can log out using:

```sh
sam chat logout
```

This command permanently deletes the token. After logging out, you'll need to log in again to start a new chat.

