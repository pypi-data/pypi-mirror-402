# Media Watcher MCP Server

An MCP server implementation for [Media Watcher](https://mediawatcher.ai/), allowing you to search news and YouTube content for sentiment analysis and monitoring.

## Installation

```bash
pip install .
```

## Configuration

You need a Media Watcher API key to use this server.

## Usage

### Running the Server

You can run the server directly:

```bash
python -m media_watcher_mcp.server --api-key YOUR_API_KEY
```

Or using the installed script:

```bash
barie-media-watcher-mcp --api-key YOUR_API_KEY
```

### Tools

#### `media_watcher_search`

Search for news or YouTube content.

- `query` (string, required): The search term (e.g., "Apple Inc").
- `source` (string, optional): "news" (default) or "youtube".
- `country` (string, optional): ISO 3166-1 alpha-2 country code (e.g., "US").

Example:
```json
{
  "query": "Tesla",
  "source": "news",
  "country": "US"
}
```

## Structure

- `media_watcher_mcp/client.py`: Async client for Media Watcher API handling polling logic.
- `media_watcher_mcp/server.py`: MCP server implementation.
