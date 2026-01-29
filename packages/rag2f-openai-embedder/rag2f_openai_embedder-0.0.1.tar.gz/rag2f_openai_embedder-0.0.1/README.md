# RAG2F OpenAI Embedder Plugin


Plugin for integrating OpenAI embeddings into RAG2F.

## Plugin Structure

```
rag2f_openai_embedder/
├── __init__.py                    # Plugin entry point
├── plugin.json                    # Plugin metadata
├── settings.json                  # Settings (empty)
├── pyproject.toml                 # Python package configuration
├── config.json.example            # Configuration example
├── CONFIG.md                      # Configuration documentation
├── src/
│   ├── __init__.py               # src package
│   ├── plugin_context.py         # Thread-safe plugin_id management
│   ├── embedder.py               # OpenAIEmbedder implementation
│   └── bootstrap_hook.py         # Bootstrap hook
└── test/
  ├── conftest.py               # pytest configuration
  ├── test_embedder_unit.py     # Embedder unit test
  └── test_bootstrap_hook.py    # Bootstrap hook test
```

## Configuration Parameters

### Required
- **api_key**: OpenAI API key (e.g. `"sk-..."`)
- **model**: Embedding model name
  - `"text-embedding-3-small"` (1536 dim, economical)
  - `"text-embedding-3-large"` (3072 dim, high quality)
  - `"text-embedding-ada-002"` (1536 dim, legacy)
- **size**: Vector size (1536 or 3072)

### Optional
- **timeout**: Request timeout in seconds (default: 30.0)
- **max_retries**: Maximum number of retries (default: 2)

## Differences from Azure OpenAI

The standard OpenAI plugin differs from Azure OpenAI in:

1. **Does NOT require** `azure_endpoint` (uses OpenAI public endpoint)
2. **Does NOT require** `api_version` (automatically uses the latest version)
3. **Does NOT require** `deployment` (uses `model` directly)
4. Uses the `OpenAI` class instead of `AzureOpenAI`
## Configuration

### Using JSON (config.json)

```json
{
  "plugins": {
    "openai_embedder": {
      "api_key": "sk-your-api-key",
      "model": "text-embedding-3-small",
      "size": 1536,
      "timeout": 30.0,
      "max_retries": 2
    }
  }
}
```

### Using Environment Variables

```bash
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__API_KEY="sk-your-api-key"
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__MODEL="text-embedding-3-small"
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__SIZE="1536"
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__TIMEOUT="30.0"
export RAG2F__PLUGINS__RAG2F_OPENAI_EMBEDDER__MAX_RETRIES="2"
```

## Installation

```bash
cd plugins/rag2f_openai_embedder
pip install -e .
```

## Testing

```bash
cd plugins/rag2f_openai_embedder
pytest test/
```

## Usage in Code

The plugin registers itself automatically via the bootstrap hook. Once configured, the embedder is available in RAG2F under the `openai_embedder` ID.

```python
# Plugin loads automatically
rag2f = await RAG2F.create(
  plugins_folder="plugins/",
  config=config
)

# The embedder is available via OptimusPrime
embedder = rag2f.optimus_prime.get("rag2f_openai_embedder")
vector = embedder.getEmbedding("Hello, world!")
```

## Validation

The plugin includes comprehensive validation:
- Ensures required parameters are present
- Type checking for `size`, `timeout`, and `max_retries`
- Detailed logging
- Appropriate error handling

## Test Coverage

- ✅ Configuration validation
- ✅ Client initialization
- ✅ Correct API calls
- ✅ Edge cases (empty strings, Unicode)
- ✅ Error handling
- ✅ Various OpenAI models
- ✅ Bootstrap hook

## Release Management

This project uses automated releases with semantic versioning and setuptools-scm.

### Version Schema (PEP 440)

- **Development builds** (branch `dev`): `X.Y.Z.devN` (e.g., `0.1.0.dev123`)
  - Published automatically to TestPyPI on every commit
  - `N` = GitHub Actions run number (monotonically increasing)
  - Base version (`X.Y.Z`) read from `NEXT_VERSION` file

- **Release Candidates** (tags `vX.Y.ZrcN`): `X.Y.ZrcN` (e.g., `1.0.0rc1`)
  - Published to PyPI as pre-release
  - GitHub Release marked as pre-release

- **Stable Releases** (tags `vX.Y.Z`): `X.Y.Z` (e.g., `1.0.0`)
  - Published to PyPI as stable
  - GitHub Release (normal)

### Installing Versions

```bash
# Install latest stable from PyPI
pip install rag2f-openai-embedder

# Install specific stable version
pip install rag2f-openai-embedder==1.0.0

# Install specific release candidate
pip install rag2f-openai-embedder==1.0.0rc1

# Install specific dev build from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            rag2f-openai-embedder==0.1.0.dev123
```

### Version Information at Runtime

Every published package includes commit information:

```python
from rag2f_openai_embedder._version import __version__, __commit__, __distance__

print(f"Version: {__version__}")    # e.g., "1.0.0" or "0.1.0.dev123"
print(f"Commit: {__commit__}")      # Git commit hash
print(f"Distance: {__distance__}")  # Commits since last tag
```

### For Maintainers

#### Publishing Dev Builds
- Push to `dev` branch → automatic publish to TestPyPI
- Version: `<NEXT_VERSION>.dev<run_number>`

#### Creating Releases

**Release Candidate:**
```bash
git tag v1.0.0rc1
git push origin v1.0.0rc1
```

**Stable Release:**
```bash
git tag v1.0.0
git push origin v1.0.0
```

#### Updating Next Version
Edit the `NEXT_VERSION` file and commit to `dev`:
```bash
echo "1.1.0" > NEXT_VERSION
git add NEXT_VERSION
git commit -m "Bump next version to 1.1.0"
git push origin dev
```

### CI/CD Workflows

- **`.github/workflows/ci-dev-testpypi.yml`**: Validates structure, builds, and publishes dev versions to TestPyPI
- **`.github/workflows/release-tags.yml`**: Builds from tags, publishes to PyPI, creates GitHub Releases