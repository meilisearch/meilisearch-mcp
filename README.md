# Meilisearch MCP Server

A Model Context Protocol (MCP) server for interacting with Meilisearch through LLM interfaces like Claude.

<a href="https://glama.ai/mcp/servers/tbc3n51jja"><img width="380" height="200" src="https://glama.ai/mcp/servers/tbc3n51jja/badge" alt="Meilisearch Server MCP server" /></a>

## Features

- Index and document management 
- Settings configuration with templates for common use cases (e-commerce, content search, SaaS)
- Task monitoring and API key management
- Built-in logging and monitoring tools

## Installation

```bash
# Clone repository
git clone <repository_url>
cd meilisearch-mcp

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Requirements

- Python ≥ 3.9
- Running Meilisearch instance
- Node.js (for testing with MCP Inspector)

## Usage

### Environment Variables

```bash
MEILI_HTTP_ADDR=http://localhost:7700  # Meilisearch URL
MEILI_MASTER_KEY=your_master_key       # Optional: Meilisearch API key
```

### Running the Server

```bash
python -m src.meilisearch_mcp
```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python -m src.meilisearch_mcp
```

## Available Tools

- Index Management: create/update/delete indexes
- Document Operations: add/update/delete documents
- Settings Management: configure search settings with templates
- API Key Management: create/update/delete API keys
- Task Monitoring: track and manage asynchronous tasks
- System Monitoring: health checks and metrics

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Create pull request

## License

MIT
