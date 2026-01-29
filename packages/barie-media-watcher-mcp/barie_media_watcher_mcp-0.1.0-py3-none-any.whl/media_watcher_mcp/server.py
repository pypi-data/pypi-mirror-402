"""Media Watcher MCP Server implementation."""

import argparse
import asyncio
import json
import logging
from typing import Optional

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from media_watcher_mcp.client import MediaWatcherClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

media_watcher_client: Optional[MediaWatcherClient] = None

async def main(api_key: str):
    """
    Main entry point for Media Watcher MCP server.

    Args:
        api_key: Media Watcher API key
    """
    global media_watcher_client
    logger.info("Initializing Media Watcher MCP Server...")
    try:
        media_watcher_client = MediaWatcherClient(api_key=api_key)
        logger.info("Media Watcher client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        return

    server = Server("media-watcher")
    logger.info("MCP Server created")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """Returns list of available tools."""
        return [
            types.Tool(
                name="media_watcher_search",
                description=(
                    "Search news articles or YouTube videos to analyze sentiment (positive, negative, neutral) "
                    "about a person, entity, or topic. Use this tool to check how sources are reporting on a specific subject. "
                    "Optionally filter by country using ISO 3166-1 alpha-2 codes."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "A simple search query such as a person's name, company name, or entity name. For example: 'John Doe', 'Apple Inc', 'climate change'."
                        },
                        "source": {
                            "type": "string",
                            "description": "Source to search from. Options: 'news' or 'youtube'. Default is 'news'.",
                            "enum": ["news", "youtube"],
                            "default": "news"
                        },
                        "country": {
                            "type": "string",
                            "description": "Optional ISO 3166-1 alpha-2 country code to filter content by country. Examples: 'US', 'GB', 'CA', 'IN'. Leave empty to search all countries."
                        }
                    },
                    "required": ["query"]
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        if media_watcher_client is None:
            raise RuntimeError("Media Watcher client not initialized")
        
        if arguments is None:
            arguments = {}
        
        try:
            if name == "media_watcher_search":
                query = arguments.get("query")
                if not query:
                    raise ValueError("Missing required parameter: query")
                
                source = arguments.get("source", "news")
                country = arguments.get("country", "")
                
                results = await media_watcher_client.search(
                    query=query,
                    source=source,
                    country=country
                )
                
                return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    logger.info("Starting MCP server with stdio transport...")
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="media-watcher",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Fatal error in MCP server: {str(e)}")
        raise


def cli_main():
    """CLI entry point for the Media Watcher MCP server."""
    parser = argparse.ArgumentParser(description='Media Watcher MCP Server')
    parser.add_argument('--api-key',
                        required=True,
                        help='Media Watcher API key')
    
    args = parser.parse_args()
    
    asyncio.run(main(
        api_key=args.api_key
    ))


if __name__ == "__main__":
    cli_main()
