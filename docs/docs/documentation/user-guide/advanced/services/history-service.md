---
title: History Service  
sidebar_position: 20  
---

# History Service  

The History service is a global service that provides flexible memory storage capabilities for Solace Agent Mesh. This service enables components to store and retrieve session histories and system internal states.  

Key features of the History service include:  

1. **Flexible Longevity**: The service offers storage with configurable durations.  
2. **Efficient File Management**: The service can store references to [file metadata](./file-service.md#file-metadata) and automatically remove entries when they expire.

The following examples are use cases for the History service: 

- Storing temporary calculation results during a multi-step process.  
- Maintaining conversation context in a chatbot application.  
- Saving user preferences across multiple sessions.  
- Storing system-wide configurations accessible to all components.  

The History service provides a flexible and efficient way to manage state and share data within the framework of Solace Agent Mesh, enabling more complex workflows and improving system performance by reducing redundant computations or API calls.  

## Usage  

The History service is a global service that creates singleton instances per identifier. Instances with the same identifier share the same memory.  

To get started, you first import the History service:  

```python
from solace_agent_mesh.services.history_service import HistoryService
```  

Then, create a new instance of the History service:  

```python
history_service = HistoryService(config, identifier="my_identifier")
```  

### Configuration  

The History service requires a configuration object when creating a new instance. The configuration object should have the following structure:  

```json
{
   "type": "memory",
   "time_to_live": 3600,
   "expiration_check_interval": 60,
   "history_policy": {
      "max_characters": 30000,
      "max_turns": 10,
      "enforce_alternate_message_roles": false
   }
}
```  

- `type`: The history provider name. For more information, see [History Providers](#history-providers).  
- `time_to_live`: The duration (in seconds) that history will be stored.  
- `expiration_check_interval`: The interval (in seconds) at which expired history is checked and removed.  
- `history_policy`: The configurations passed to the history provider.  
  - `max_characters`: The maximum number of characters the history can store.  
  - `max_turns`: The maximum number of message turns the history can store.  
  - `enforce_alternate_message_roles`: A boolean that indicates whether the history should enforce alternate message roles (`user`/`system`).  
  - The `history_policy` object can include additional properties for [custom history providers](#custom-history-provider).  

### Storing Data  

There are two methods to store data in the History service:  
- `store_history(session_id: str, role: str, content: Union[str, dict])`  
- `store_file(session_id: str, file: dict)`  

To store a message in the History service, use the `store_history` method:  

```python
role = "user"
content = "Hello, World!"

history_service.store_history(session_id, role, content)
```  

To store a file in the History service, use the `store_file` method:  

```python
file_meta = get_file_metadata()

history_service.store_file(session_id, file_meta)
```  

:::note  
The `file_meta` object is the returned output of the [`File Service`](./file-service.md#file-metadata) when uploading a file.  
:::  

### Retrieving Data  

There are two methods to retrieve data from the History service:  
- `get_history(session_id: str) -> list`  
- `get_files(session_id: str) -> dict`  

To retrieve messages from the History service, use the `get_history` method:  

```python
history = history_service.get_history(session_id)
```  

To retrieve files from the History service, use the `get_files` method:  

```python
files = history_service.get_files(session_id)
```  

### Clearing Data  

To clear data from the History service, use the `clear` method:  

```python
history_service.clear(session_id)
```  

:::note  
You can optionally pass a second parameter, `keep_levels`, to specify the number of most recent history entries to retain. By default, all history entries are cleared.  
:::  

## History Providers  

The `History service` class uses a history provider to store and manage history data. The provider is defined in the configuration object passed to the service.  

The Solace Agent Mesh Framework provides the following built-in history providers:  

- **Memory History Provider**: Stores history in memory.  
- **Redis History Provider**: Stores history in a Redis database.  

### Custom History Provider  

To create a custom history provider, you can define a class that extends the `BaseHistoryProvider` class provided by Solace Agent Mesh framework:  

```python
from solace_agent_mesh.services.history_service.history_providers.base_history_provider import BaseHistoryProvider
```  

Then, implement all abstract methods of the `BaseHistoryProvider` class.  

Once completed, you can add the `module_path` key to the configuration object with the path to the custom history provider module:  

```json
{
   "type": "custom",
   "module_path": "path.to.custom.history.provider",
   "time_to_live": 3600,
   "expiration_check_interval": 60,
   "history_policy": {
      "max_characters": 30000,
      "max_turns": 10,
      "custom_key_1": "value_1",
      "custom_key_2": "value_2"
   }
}
```
