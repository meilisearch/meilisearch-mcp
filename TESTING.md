# Testing Documentation

## Overview

This document describes the testing infrastructure for the Meilisearch MCP server.

## Test Structure

### Integration Tests (`tests/test_mcp_integration.py`)

Comprehensive end-to-end tests that verify the MCP server functionality by testing actual tool execution:

#### Test Coverage

- **Basic Functionality** (2 tests)
  - Server creation and initialization
  - Tool listing and availability

- **Connection Management** (2 tests)
  - Getting current connection settings
  - Updating connection settings dynamically

- **Health and Version** (3 tests)
  - Health check endpoint
  - Version information retrieval
  - Database statistics

- **Index Management** (2 tests)
  - Creating new indexes
  - Listing existing indexes

- **Document Operations** (2 tests)
  - Adding documents to indexes
  - Retrieving documents from indexes

- **Search Functionality** (2 tests)
  - Searching within specific indexes
  - Multi-index search capabilities

- **Settings Management** (2 tests)
  - Getting index settings
  - Updating index settings

- **Task Management** (1 test)
  - Retrieving task information

- **Error Handling** (2 tests)
  - Invalid tool names
  - Operations on non-existent indexes

### Basic Tests (`tests/test_server.py`)

Simple unit test for basic server instantiation.

## Running Tests

### Prerequisites

1. Install development dependencies:
   ```bash
   uv pip install -r requirements-dev.txt
   ```

2. Ensure Meilisearch is running:
   ```bash
   # Using Docker
   docker run -d -p 7700:7700 getmeili/meilisearch:v1.6
   
   # Or using local installation
   meilisearch
   ```

### Local Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_mcp_integration.py -v

# Run tests with coverage
python -m pytest --cov=src tests/
```

### CI Testing

Tests run automatically in GitHub Actions on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

The CI environment:
- Tests against Python 3.10, 3.11, and 3.12
- Uses Docker to run Meilisearch v1.6
- Includes health checks and readiness verification
- Runs code formatting checks with Black

## Test Design

### Tool Simulation

The tests use a `simulate_tool_call()` function that:
1. Attempts to find specific tool methods on the server
2. Falls back to request handlers if available
3. Uses a monkey-patched `_execute_tool_directly()` method for direct tool execution
4. Returns proper MCP `TextContent` responses

### Fixtures

- `meilisearch_url`: Provides the test Meilisearch URL
- `mcp_server`: Creates and cleans up MCP server instances
- `clean_index`: Provides unique index names for isolation

### Test Isolation

Each test uses unique index names to prevent interference between tests.
The `clean_index` fixture generates timestamped index names.

## Known Issues

- One deprecation warning in logging.py for `datetime.utcnow()` (cosmetic)
- Some tools may not be fully functional (as expected per project requirements)

## Continuous Integration

The CI workflow (`.github/workflows/ci.yml`) includes:

1. **Test Job**: 
   - Matrix testing across Python versions
   - Meilisearch service with health checks
   - Full test suite execution

2. **Integration Test Job**:
   - Dedicated integration testing
   - MCP server startup verification
   - End-to-end functionality validation

## Future Improvements

- Add more comprehensive error scenario testing
- Implement performance benchmarks
- Add integration with real MCP clients
- Expand test coverage for API key management tools