"""Facia MCP Server implementation."""

import argparse
import asyncio
import json
import logging
from typing import Optional

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from facia_mcp.client import FaciaClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main(client_id: str, client_secret: str, storage_dir: Optional[str] = None):
    """Main entry point for Facia MCP server."""
    global facia_client
    logger.info("Initializing Facia MCP Server...")
    facia_client = FaciaClient(client_id=client_id, client_secret=client_secret, storage_dir=storage_dir)
    logger.info("Facia client initialized successfully")

    server = Server("facia")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """Returns list of available tools."""
        return [
            types.Tool(
                name="age_estimation",
                description="Perform age estimation on an image using Facia.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_name": {
                            "type": "string",
                            "description": "Image file name (relative to storage directory).",
                        }
                    },
                    "required": ["image_name"],
                },
            ),
            types.Tool(
                name="deepfake_detection",
                description="Perform deepfake detection (liveness) on an image using Facia.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_name": {
                            "type": "string",
                            "description": "Image file name (relative to storage directory).",
                        }
                    },
                    "required": ["image_name"],
                },
            ),
            types.Tool(
                name="face_match",
                description="Perform face match between an original and a matched image using Facia.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "original_image_name": {
                            "type": "string",
                            "description": "Original image file name (relative to storage directory).",
                        },
                        "matched_image_name": {
                            "type": "string",
                            "description": "Matched image file name (relative to storage directory).",
                        },
                    },
                    "required": ["original_image_name", "matched_image_name"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if facia_client is None:
            raise RuntimeError("Facia client not initialized")

        if arguments is None:
            arguments = {}

        try:
            if name == "age_estimation":
                image_name = arguments.get("image_name")
                if not image_name:
                    raise ValueError("Missing required parameter: image_name")

                result = await facia_client.age_estimation(image_name=image_name)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "deepfake_detection":
                image_name = arguments.get("image_name")
                if not image_name:
                    raise ValueError("Missing required parameter: image_name")

                result = await facia_client.deepfake_detection(image_name=image_name)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "face_match":
                original_image_name = arguments.get("original_image_name")
                matched_image_name = arguments.get("matched_image_name")
                if not original_image_name or not matched_image_name:
                    raise ValueError("Missing required parameters: original_image_name, matched_image_name")

                result = await facia_client.face_match(
                    original_image_name=original_image_name,
                    matched_image_name=matched_image_name,
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except FileNotFoundError as e:
            logger.error(str(e))
            return [types.TextContent(type="text", text=str(e))]
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
                    server_name="facia",
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
    """CLI entry point for the Facia MCP server."""
    parser = argparse.ArgumentParser(description="Facia MCP Server")
    parser.add_argument("--client-id", required=True, help="Facia client ID")
    parser.add_argument("--client-secret", required=True, help="Facia client secret")
    parser.add_argument(
        "--storage-dir",
        required=False,
        default=None,
        help="Directory containing images (defaults to current working directory)",
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            client_id=args.client_id,
            client_secret=args.client_secret,
            storage_dir=args.storage_dir,
        )
    )


if __name__ == "__main__":
    cli_main()
