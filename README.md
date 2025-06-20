<div align="center">
  <img src="https://github.com/meilisearch/meilisearch/blob/main/assets/logo.svg" alt="Meilisearch" width="200" height="200" />
</div>

<h1 align="center">Meilisearch MCP Server</h1>

<h4 align="center">
  <a href="https://github.com/meilisearch/meilisearch">Meilisearch</a> |
  <a href="https://www.meilisearch.com/cloud?utm_campaign=oss&utm_source=github&utm_medium=meilisearch-mcp">Meilisearch Cloud</a> |
  <a href="https://www.meilisearch.com/docs">Documentation</a> |
  <a href="https://discord.meilisearch.com">Discord</a>
</h4>

<p align="center">
  <a href="https://pypi.org/project/meilisearch-mcp/"><img src="https://img.shields.io/pypi/v/meilisearch-mcp.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/meilisearch-mcp/"><img src="https://img.shields.io/pypi/pyversions/meilisearch-mcp.svg" alt="Python Versions"></a>
  <a href="https://github.com/meilisearch/meilisearch-mcp/actions"><img src="https://github.com/meilisearch/meilisearch-mcp/workflows/Test%20and%20Lint/badge.svg" alt="Tests"></a>
  <a href="https://github.com/meilisearch/meilisearch-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-informational" alt="License"></a>
  <a href="https://pypi.org/project/meilisearch-mcp/"><img src="https://img.shields.io/pypi/dm/meilisearch-mcp" alt="Downloads"></a>
</p>

<p align="center">⚡ Connect any LLM to Meilisearch and supercharge your AI with lightning-fast search capabilities! 🔍</p>

## 🤔 What is this?

The Meilisearch MCP Server is a Model Context Protocol server that enables any MCP-compatible client (including Claude, OpenAI agents, and other LLMs) to interact with Meilisearch. This stdio-based server allows AI assistants to manage search indices, perform searches, and handle your data through natural conversation.

**Why use this?**
- 🤖 **Universal Compatibility** - Works with any MCP client, not just Claude
- 🗣️ **Natural Language Control** - Manage Meilisearch through conversation with any LLM
- 🚀 **Zero Learning Curve** - No need to learn Meilisearch's API
- 🔧 **Full Feature Access** - All Meilisearch capabilities at your fingertips
- 🔄 **Dynamic Connections** - Switch between Meilisearch instances on the fly
- 📡 **stdio Transport** - Currently uses stdio; native Meilisearch MCP support coming soon!

## ✨ Key Features

- 📊 **Index & Document Management** - Create, update, and manage search indices
- 🔍 **Smart Search** - Search across single or multiple indices with advanced filtering
- ⚙️ **Settings Configuration** - Fine-tune search relevancy and performance
- 📈 **Task Monitoring** - Track indexing progress and system operations
- 🔐 **API Key Management** - Secure access control
- 🏥 **Health Monitoring** - Keep tabs on your Meilisearch instance
- 🐍 **Python Implementation** - [TypeScript version also available](https://github.com/devlimelabs/meilisearch-ts-mcp)

## 🚀 Quick Start

Get up and running in just 3 steps!

### 1️⃣ Install the package

```bash
# Using pip
pip install meilisearch-mcp

# Or using uvx (recommended)
uvx -n meilisearch-mcp
```

### 2️⃣ Configure Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meilisearch": {
      "command": "uvx",
      "args": ["-n", "meilisearch-mcp"]
    }
  }
}
```

### 3️⃣ Start Meilisearch

```bash
# Using Docker (recommended)
docker run -d -p 7700:7700 getmeili/meilisearch:v1.6

# Or using Homebrew
brew install meilisearch
meilisearch
```

That's it! Now you can ask your AI assistant to search and manage your Meilisearch data! 🎉

## 📚 Examples

### 💬 Talk to your AI assistant naturally:

```
You: "Create a new index called 'products' with 'id' as the primary key"
AI: I'll create that index for you... ✓ Index 'products' created successfully!

You: "Add some products to the index"
AI: I'll add those products... ✓ Added 5 documents to 'products' index

You: "Search for products under $50 with 'electronics' in the category"
AI: I'll search for those products... Found 12 matching products!
```

### 🔍 Advanced Search Example:

```
You: "Search across all my indices for 'machine learning' and sort by date"
AI: Searching across all indices... Found 47 results from 3 indices:
- 'blog_posts': 23 articles about ML
- 'documentation': 15 technical guides  
- 'tutorials': 9 hands-on tutorials
```

## 🔧 Installation

### Prerequisites

- Python ≥ 3.9
- Running Meilisearch instance
- MCP-compatible client (Claude Desktop, OpenAI agents, etc.)

### From PyPI

```bash
pip install meilisearch-mcp
```

### From Source (for development)

```bash
# Clone repository
git clone https://github.com/meilisearch/meilisearch-mcp.git
cd meilisearch-mcp

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Using Docker

Perfect for containerized environments like n8n workflows!

#### From Docker Hub

```bash
# Pull the latest image
docker pull getmeili/meilisearch-mcp:latest

# Or a specific version
docker pull getmeili/meilisearch-mcp:0.5.0

# Run the container
docker run -it \
  -e MEILI_HTTP_ADDR=http://your-meilisearch:7700 \
  -e MEILI_MASTER_KEY=your-master-key \
  getmeili/meilisearch-mcp:latest
```

#### Build from Source

```bash
# Build your own image
docker build -t meilisearch-mcp .
docker run -it \
  -e MEILI_HTTP_ADDR=http://your-meilisearch:7700 \
  -e MEILI_MASTER_KEY=your-master-key \
  meilisearch-mcp
```

#### Integration with n8n

For n8n workflows, you can use the Docker image directly in your setup:
```yaml
meilisearch-mcp:
  image: getmeili/meilisearch-mcp:latest
  environment:
    - MEILI_HTTP_ADDR=http://meilisearch:7700
    - MEILI_MASTER_KEY=masterKey
```

## 🛠️ What Can You Do?

<details>
<summary><b>🔗 Connection Management</b></summary>

- View current connection settings
- Switch between Meilisearch instances dynamically
- Update API keys on the fly

</details>

<details>
<summary><b>📁 Index Operations</b></summary>

- Create new indices with custom primary keys
- List all indices with stats
- Delete indices and their data
- Get detailed index metrics

</details>

<details>
<summary><b>📄 Document Management</b></summary>

- Add or update documents
- Retrieve documents with pagination
- Bulk import data

</details>

<details>
<summary><b>🔍 Search Capabilities</b></summary>

- Search with filters, sorting, and facets
- Multi-index search
- Semantic search with vectors
- Hybrid search (keyword + semantic)

</details>

<details>
<summary><b>⚙️ Settings & Configuration</b></summary>

- Configure ranking rules
- Set up faceting and filtering
- Manage searchable attributes
- Customize typo tolerance

</details>

<details>
<summary><b>🔐 Security</b></summary>

- Create and manage API keys
- Set granular permissions
- Monitor key usage

</details>

<details>
<summary><b>📊 Monitoring & Health</b></summary>

- Health checks
- System statistics
- Task monitoring
- Version information

</details>

## 🌍 Environment Variables

Configure default connection settings:

```bash
MEILI_HTTP_ADDR=http://localhost:7700  # Default Meilisearch URL
MEILI_MASTER_KEY=your_master_key       # Optional: Default API key
```

## 💻 Development

### Setting Up Development Environment

1. **Start Meilisearch**:
   ```bash
   docker run -d -p 7700:7700 getmeili/meilisearch:v1.6
   ```

2. **Install Development Dependencies**:
   ```bash
   uv pip install -r requirements-dev.txt
   ```

3. **Run Tests**:
   ```bash
   python -m pytest tests/ -v
   ```

4. **Format Code**:
   ```bash
   black src/ tests/
   ```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python -m src.meilisearch_mcp
```

## 🤝 Community & Support

We'd love to hear from you! Here's how to get help and connect:

- 💬 [Join our Discord](https://discord.meilisearch.com) - Chat with the community
- 🐛 [Report Issues](https://github.com/meilisearch/meilisearch-mcp/issues) - Found a bug? Let us know!
- 💡 [Feature Requests](https://github.com/meilisearch/meilisearch-mcp/issues) - Have an idea? We're listening!
- 📖 [Meilisearch Docs](https://www.meilisearch.com/docs) - Learn more about Meilisearch

## 🤗 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Make your changes and run tests
5. Format your code with `black`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

See our [Contributing Guidelines](#contributing-1) for more details.

## 📦 Release Process

This project uses automated versioning and publishing. When the version in `pyproject.toml` changes on the `main` branch, the package is automatically published to PyPI.

See the [Release Process](#release-process-1) section for detailed instructions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>Meilisearch</b> is an open-source search engine that offers a delightful search experience.<br>
  Learn more about Meilisearch at <a href="https://www.meilisearch.com">meilisearch.com</a>
</p>

---

<details>
<summary><h2>📖 Full Documentation</h2></summary>

### Available Tools

#### Connection Management
- `get-connection-settings`: View current Meilisearch connection URL and API key status
- `update-connection-settings`: Update URL and/or API key to connect to a different instance

#### Index Management
- `create-index`: Create a new index with optional primary key
- `list-indexes`: List all available indexes
- `delete-index`: Delete an existing index and all its documents
- `get-index-metrics`: Get detailed metrics for a specific index

#### Document Operations
- `get-documents`: Retrieve documents from an index with pagination
- `add-documents`: Add or update documents in an index

#### Search
- `search`: Flexible search across single or multiple indices with filtering and sorting options

#### Settings Management
- `get-settings`: View current settings for an index
- `update-settings`: Update index settings (ranking, faceting, etc.)

#### API Key Management
- `get-keys`: List all API keys
- `create-key`: Create new API key with specific permissions
- `delete-key`: Delete an existing API key

#### Task Management
- `get-task`: Get information about a specific task
- `get-tasks`: List tasks with optional filters
- `cancel-tasks`: Cancel pending or enqueued tasks
- `delete-tasks`: Delete completed tasks

#### System Monitoring
- `health-check`: Basic health check
- `get-health-status`: Comprehensive health status
- `get-version`: Get Meilisearch version information
- `get-stats`: Get database statistics
- `get-system-info`: Get system-level information

### Development Setup

#### Prerequisites

1. **Start Meilisearch server**:
   ```bash
   # Using Docker (recommended for development)
   docker run -d -p 7700:7700 getmeili/meilisearch:v1.6
   
   # Or using brew (macOS)
   brew install meilisearch
   meilisearch
   
   # Or download from https://github.com/meilisearch/meilisearch/releases
   ```

2. **Install development tools**:
   ```bash
   # Install uv for Python package management
   pip install uv
   
   # Install Node.js for MCP Inspector testing
   # Visit https://nodejs.org/ or use your package manager
   ```

### Running Tests

This project includes comprehensive integration tests that verify MCP tool functionality:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_mcp_client.py -v

# Run tests with coverage report
python -m pytest --cov=src tests/

# Run tests in watch mode (requires pytest-watch)
pytest-watch tests/
```

**Important**: Tests require a running Meilisearch instance on `http://localhost:7700`.

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Run type checking (if mypy is configured)
mypy src/

# Lint code (if flake8 is configured)
flake8 src/ tests/
```

### Contributing Guidelines

1. **Fork and clone** the repository
2. **Set up development environment** following the Development Setup section above
3. **Create a feature branch** from `main`
4. **Write tests first** if adding new functionality (Test-Driven Development)
5. **Run tests locally** to ensure all tests pass before committing
6. **Format code** with Black and ensure code quality
7. **Commit changes** with descriptive commit messages
8. **Push to your fork** and create a pull request

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes, write tests first
# Edit files...

# Run tests to ensure everything works
python -m pytest tests/ -v

# Format code
black src/ tests/

# Commit and push
git add .
git commit -m "Add feature description"
git push origin feature/your-feature-name
```

### Testing Guidelines

- All new features should include tests
- Tests should pass before submitting PRs
- Use descriptive test names and clear assertions
- Test both success and error cases
- Ensure Meilisearch is running before running tests

### Release Process

This project uses automated versioning and publishing to PyPI. The release process is designed to be simple and automated.

#### How Releases Work

1. **Automated Publishing**: When the version number in `pyproject.toml` changes on the `main` branch, a GitHub Action automatically:
   - Builds the Python package
   - Publishes it to PyPI using trusted publishing
   - Creates a new release on GitHub

2. **Version Detection**: The workflow compares the current version in `pyproject.toml` with the previous commit to detect changes

3. **PyPI Publishing**: Uses PyPA's official publish action with trusted publishing (no manual API keys needed)

#### Creating a New Release

To create a new release, follow these steps:

##### 1. Determine Version Number

Follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **PATCH** (e.g., 0.4.0 → 0.4.1): Bug fixes, documentation updates, minor improvements
- **MINOR** (e.g., 0.4.0 → 0.5.0): New features, new MCP tools, significant enhancements
- **MAJOR** (e.g., 0.5.0 → 1.0.0): Breaking changes, major API changes

##### 2. Update Version and Create PR

```bash
# 1. Create a branch from latest main
git checkout main
git pull origin main
git checkout -b release/v0.5.0

# 2. Update version in pyproject.toml
# Edit the version = "0.4.0" line to your new version

# 3. Commit and push
git add pyproject.toml
git commit -m "Bump version to 0.5.0"
git push origin release/v0.5.0

# 4. Create PR and get it reviewed/merged
gh pr create --title "Release v0.5.0" --body "Bump version for release"
```

##### 3. Merge to Main

Once the PR is approved and merged to `main`, the GitHub Action will automatically:

1. Detect the version change
2. Build the package  
3. Publish to PyPI at https://pypi.org/p/meilisearch-mcp
4. Make the new version available via `pip install meilisearch-mcp`

##### 4. Verify Release

After merging, verify the release:

```bash
# Check GitHub Action status
gh run list --workflow=publish.yml

# Verify on PyPI (may take a few minutes)
pip index versions meilisearch-mcp

# Test installation of new version
pip install --upgrade meilisearch-mcp
```

### Release Workflow File

The automated release is handled by `.github/workflows/publish.yml`, which:

- Triggers on pushes to `main` branch
- Checks if `pyproject.toml` version changed
- Uses Python 3.10 and official build tools
- Publishes using trusted publishing (no API keys required)
- Provides verbose output for debugging

### Troubleshooting Releases

**Release didn't trigger**: Check that the version in `pyproject.toml` actually changed between commits

**Build failed**: Check the GitHub Actions logs for Python package build errors

**PyPI publish failed**: Verify the package name and that trusted publishing is configured properly

**Version conflicts**: Ensure the new version number hasn't been used before on PyPI

### Development vs Production Versions

- **Development**: Install from source using `pip install -e .`
- **Production**: Install from PyPI using `pip install meilisearch-mcp`
- **Specific version**: Install using `pip install meilisearch-mcp==0.5.0`

</details>