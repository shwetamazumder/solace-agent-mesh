---
title: REST API
sidebar_position: 10
---

# Advanced REST API Configuration

Environment variables control the REST API's rate limiting setting. Basic configuration is set during initialization, but you can adjust additional options to enhance security and customize access controls.

## Basic Configuration
The following settings are included in the default setup:

| Environment Variable | Default Value | Description |
|----------------------|--------------|-------------|
| `REST_API_SERVER_INPUT_PORT` | `5050` | Specifies the port number for the REST API server. |
| `REST_API_SERVER_HOST` | `127.0.0.1` | Sets the host address for the REST API server. |
| `REST_API_SERVER_INPUT_ENDPOINT` | `/api/v1/request` | Defines the endpoint path for REST API requests. |

### API Rate Limiting
| Environment Variable | Description |
|----------------------|-------------|
| `REST_API_SERVER_INPUT_RATE_LIMIT` | Specifies the maximum number of API requests allowed per minute. |