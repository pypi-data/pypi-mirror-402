# OpenAI Embedder Configuration (Spock)


This plugin now reads its configuration through the centralized **Spock** system of RAG2F.
The plugin configuration must be placed in the main configuration file (or via environment variables) under the `plugins.<plugin_id>` node.

Note: The APIs in this repository expect the plugin to retrieve the configuration using the `plugin_id` (e.g. `rag2f_openai_embedder`) via `rag2f.spock.get_plugin_config(plugin_id)`.

## Where to put the configuration

In the main configuration file (e.g. `config.json`), the plugin section should have this structure:

```json
{
  "plugins": {
    "rag2f_openai_embedder": {
      "api_key": "sk-your-api-key-here",
      "model": "text-embedding-3-small",
      "size": 1536,
      "timeout": 30.0,
      "max_retries": 2
    }
  }
}
```

In this example, the `plugin_id` is `rag2f_openai_embedder` and Spock will load the configuration when the plugin requests it.

## Environment variables (Spock)

Spock also supports environment variables. The format is based on double underscore prefixes to represent the hierarchy.

Examples to set the plugin configuration via ENV:

```bash
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__API_KEY="sk-your-api-key"
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__MODEL="text-embedding-3-small"
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__SIZE="1536"
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__TIMEOUT="30.0"
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__MAX_RETRIES="2"
```

Spock will parse types (int, float, bool, JSON) whenever possible.

## Source priorities

1. **Environment Variables** (highest priority)
2. **JSON files** (config.json passed to RAG2F)
3. **Default values in code** (lowest priority)

## Example: how the plugin accesses its configuration

In the code, the plugin retrieves its configuration like this:

```python
plugin_cfg = rag2f.spock.get_plugin_config("rag2f_openai_embedder")
```

After obtaining `plugin_cfg`, the plugin can validate required fields and raise a clear error if any are missing.

### Required parameters

- `api_key`: OpenAI API key
- `model`: Embedding model name (e.g. `"text-embedding-3-small"`, `"text-embedding-3-large"`, `"text-embedding-ada-002"`)
- `size`: Embedding vector size (1536 for `text-embedding-3-small`, 3072 for `text-embedding-3-large`, 1536 for `ada-002`)
- `timeout`: Timeout in seconds (default: 30.0)
- `max_retries`: Maximum number of retries (default: 2)


