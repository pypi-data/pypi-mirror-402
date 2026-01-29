import logging

from openai import OpenAI
from rag2f.core.protocols.embedder import Vector

logger = logging.getLogger(__name__)


class OpenAIEmbedder:
    """Embedder for OpenAI using the `openai` library (OpenAI class).

    Configuration is managed through RAG2F's Spock configuration system.
    The plugin retrieves its configuration via the RAG2F instance using the plugin ID.

    Required configuration parameters:
      - api_key: OpenAI API key
      - model: Name of the embedding model (e.g., 'text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002')
      - size: Dimension of the output vector
      - timeout: Request timeout (default: 30.0)
      - max_retries: Maximum number of retries (default: 2)

    Optional configuration parameters:
      - base_url: Base URL for the API endpoint (default: None, uses OpenAI's official API)

    Configuration can be provided via:
    1. JSON file (specified in RAG2F initialization)
    2. Environment variables with prefix RAG2F__PLUGINS__<PLUGIN_ID>__

    Example environment variables:
      RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__API_KEY=sk-xxx
      RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__MODEL=text-embedding-3-small
      RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__SIZE=1536
      RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__BASE_URL=http://localhost:8000/v1
    """

    def __init__(self, config: dict):
        """Initialize the embedder using a configuration dictionary.

        Args:
            config: Dictionary containing configuration parameters
        """
        self._config = config
        # Extract and validate required parameters
        self._api_key = config.get("api_key")
        self._model = config.get("model")
        self._size = config.get("size")
        # Optional parameters with defaults
        self._timeout = config.get("timeout", 30.0)
        self._max_retries = config.get("max_retries", 2)
        self._base_url = config.get("base_url")  # Optional: for custom endpoints like localhost

        # Validate required parameters
        missing = []
        if not self._model:
            missing.append("model")
        if not self._size:
            missing.append("size")

        if missing:
            raise ValueError(
                f"Missing required configuration parameters: {', '.join(missing)}. "
                "Provide them via JSON config file or environment variables."
            )

        # Ensure size is an integer
        try:
            self._size = int(self._size)
        except (ValueError, TypeError) as err:
            raise ValueError(f"Parameter 'size' must be an integer, got: {self._size}") from err

        # Ensure timeout is a float
        try:
            self._timeout = float(self._timeout)
        except (ValueError, TypeError) as err:
            raise ValueError(
                f"Parameter 'timeout' must be a number, got: {self._timeout}"
            ) from err

        # Ensure max_retries is an integer
        try:
            self._max_retries = int(self._max_retries)
        except (ValueError, TypeError) as err:
            raise ValueError(
                f"Parameter 'max_retries' must be an integer, got: {self._max_retries}"
            ) from err

        # Initialize OpenAI client
        client_kwargs = {
            "timeout": self._timeout,
            "max_retries": self._max_retries,
        }
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        if self._api_key:
            client_kwargs["api_key"] = self._api_key

        self._client = OpenAI(**client_kwargs)

        logger.info("OpenAIEmbedder initialized with model '%s'", self._model)

    @property
    def size(self) -> int:
        """Return the embedding vector size."""
        return self._size

    def getEmbedding(self, text: str) -> Vector:
        """Generate embedding vector for the given text.

        Args:
            text: Input text to embed
        Returns:
            List of floats representing the embedding vector
        """
        try:
            resp = self._client.embeddings.create(model=self._model, input=text)
            return list(resp.data[0].embedding)
        except Exception as e:
            logger.error("Error generating embedding: %s", e)
            raise
