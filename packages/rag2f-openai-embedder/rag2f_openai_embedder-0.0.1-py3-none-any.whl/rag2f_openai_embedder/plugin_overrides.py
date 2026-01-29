import logging

from rag2f.core.morpheus.decorators.plugin_decorator import plugin
from rag2f.core.morpheus.plugin import Plugin
from rag2f.core.rag2f import RAG2F

from .plugin_context import set_plugin_id

logger = logging.getLogger(__name__)


@plugin
def activated(plugin: Plugin, rag2f_instance: RAG2F):
    """Bootstrap OpenAI embedder from Spock configuration.

    This function loads the OpenAIEmbedder using configuration from
    Spock (either JSON or environment variables).

    Configuration is retrieved using the plugin ID: 'rag2f_openai_embedder'

    Required configuration:
    - api_key: OpenAI API key
    - model: Model name (e.g., 'text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002')
    - size: Embedding vector dimension

    Example JSON configuration:
    {
      "plugins": {
        "rag2f_openai_embedder": {
          "api_key": "sk-...",
          "model": "text-embedding-3-small",
          "size": 1536
        }
      }
    }

    Example environment variables:
    RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__API_KEY=sk-...
    RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__MODEL=text-embedding-3-small
    RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__SIZE=1536

    Args:
        plugin: This plugin in memory of RAG2F
        rag2f: RAG2F instance providing access to Spock configuration

    """
    # Get plugin_id from the RAG2F instance
    plugin_id = plugin.id
    set_plugin_id(plugin_id)

    logger.debug(f"🔍 Plugin '{plugin_id}' ovveride activate execution: {activated}")

    config = rag2f_instance.spock.get_plugin_config(plugin_id)

    if not config:
        logger.warning(
            "No configuration found for plugin '%s'. "
            "Embedder will not be registered. "
            "Provide configuration via JSON or environment variables.",
            plugin_id,
        )
        return

    try:
        # Import embedder (lazy import to avoid issues if dependencies not installed)
        from .embedder import OpenAIEmbedder

        # Initialize embedder with Spock configuration
        embedder = OpenAIEmbedder(config)
        rag2f_instance.optimus_prime.register(plugin_id, embedder)

        logger.info(
            "OpenAI embedder registered as '%s' (size=%d, model=%s)",
            plugin_id,
            embedder.size,
            config.get("model"),
        )

    except ImportError as e:
        logger.error(
            "Failed to import OpenAIEmbedder. Ensure 'openai' package is installed: %s", e
        )
    except ValueError as e:
        logger.error("Failed to initialize OpenAIEmbedder due to configuration error: %s", e)
    except Exception as e:
        logger.error("Unexpected error bootstrapping OpenAI embedder: %s", e)

    return
