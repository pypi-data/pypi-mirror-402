"""AML Watcher MCP Server implementation."""

import argparse
import asyncio
import json
import logging
from typing import Optional

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from aml_watcher_mcp.client import AMLWatcherClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main(api_key: str):
    """
    Main entry point for AML Watcher MCP server.

    Args:
        api_key: AML Watcher API key
    """
    global aml_watcher_client
    logger.warning("Initializing AML Watcher MCP Server...")
    aml_watcher_client = AMLWatcherClient(api_key=api_key)
    logger.warning("AML Watcher client initialized successfully")
    server = Server("aml-watcher")
    logger.warning("MCP Server created")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """Returns list of available tools."""
        logger.warning("List tools requested")
        return [
            types.Tool(
                name="aml_watcher_search",
                description=(
                    "Perform real-time sanction and PEP (Politically Exposed Persons) screening for any entity type using AML Watcher. "
                    "This tool automatically flags individuals or entities on global sanctions lists, detects PEPs to help meet regulatory requirements, "
                    "screens for adverse media coverage, and uses fuzzy matching to identify close name variations and spelling differences for more accurate results. "
                    "Supports screening of Persons, Companies, Organizations, Vessels, Aircraft, and Crypto Wallets. "
                    "Typical use cases include financial institutions conducting KYC/AML checks, fintech platforms screening users or transactions, "
                    "compliance teams monitoring high-risk customers or partners, maritime industry screening vessels, aviation industry screening aircraft, "
                    "and crypto exchanges screening wallet addresses. "
                    "The tool searches across multiple categories including Sanctions, PEP (all levels), Adverse Media, Warnings and Regulatory Enforcement, "
                    "Business, Businessperson, Fitness and Probity, Insolvency, SIE, and SIP. "
                    "You can optionally filter by entity type, countries, specific categories, birth/incorporation date, or unique identifiers."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name or entity to screen (2-100 characters, required). Can be a person's name, company name, organization, vessel name, aircraft registration, or crypto wallet address. Examples: 'John Doe', 'Acme Corporation', 'MV Evergreen', 'N12345', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'"
                        },
                        "countries": {
                            "type": ["array", "null"],
                            "items": {"type": "string"},
                            "description": "Optional array of ISO 3166-1 alpha-2 country codes to filter results. Examples: ['CA', 'IN'], ['US'], ['GB', 'FR']. Leave empty or null to search all countries."
                        },
                        "categories": {
                            "type": ["array", "null"],
                            "items": {"type": "string"},
                            "description": "Optional array of categories to filter. Available: 'Adverse Media', 'Business', 'Businessperson', 'Fitness and Probity', 'Insolvency', 'PEP', 'PEP Level 1', 'PEP Level 2', 'PEP Level 3', 'PEP Level 4', 'SIE', 'SIP', 'Sanctions', 'Warnings and Regulatory Enforcement'. Leave empty or null to search all categories."
                        },
                        "entity_type": {
                            "type": ["array", "null"],
                            "items": {"type": "string"},
                            "description": "Optional array of entity types to search. Available: 'Aircraft', 'Company', 'Crypto_Wallet', 'Organization', 'Person', 'Vessel'. Leave empty or null to search all entity types. Examples: ['Person'], ['Company', 'Organization'], ['Person', 'Company']."
                        },
                        "birth_incorporation_date": {
                            "type": ["string", "null"],
                            "description": "Optional date in DD-MM-YYYY format to filter results. Supports partial formats: '10-03-1947' (full), '10-03-0000' (day-month only), '00-03-1947' (month-year only), '00-00-1947' (year only). Leave empty or null if not needed."
                        },
                        "unique_identifier": {
                            "type": ["string", "null"],
                            "description": "Optional unique identifier to filter search records (2-50 characters). Can be Passport No, National ID number, or other identifiers. Example: 'TR12345677'. Leave empty or null if not needed."
                        }
                    },
                    "required": ["name"]
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        logger.warning(f"Tool called: {name} with arguments: {arguments}")
        
        if aml_watcher_client is None:
            raise RuntimeError("AML Watcher client not initialized")
        
        if arguments is None:
            arguments = {}
        
        try:
            if name == "aml_watcher_search":
                name_param = arguments.get("name")
                if not name_param:
                    raise ValueError("Missing required parameter: name")
                
                # Filter out None values and only include provided parameters
                search_kwargs = {"name": name_param}
                
                countries = arguments.get("countries")
                if countries is not None:
                    search_kwargs["countries"] = countries
                
                categories = arguments.get("categories")
                if categories is not None:
                    search_kwargs["categories"] = categories
                
                entity_type = arguments.get("entity_type")
                if entity_type is not None:
                    search_kwargs["entity_type"] = entity_type
                
                birth_incorporation_date = arguments.get("birth_incorporation_date")
                if birth_incorporation_date is not None and birth_incorporation_date != "":
                    search_kwargs["birth_incorporation_date"] = birth_incorporation_date
                
                unique_identifier = arguments.get("unique_identifier")
                if unique_identifier is not None and unique_identifier != "":
                    search_kwargs["unique_identifier"] = unique_identifier
                
                result = await aml_watcher_client.search(**search_kwargs)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            else:
                logger.error(f"Unknown tool: {name}")
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {str(e)}")
            raise

    logger.warning("Starting MCP server with stdio transport...")
    logger.warning(f"Server capabilities: {server.get_capabilities(notification_options=NotificationOptions(), experimental_capabilities={})}")
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.warning("Stdio server started, running server...")
            logger.warning("Waiting for client initialization...")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="aml-watcher",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
            logger.warning("Server initialization completed")
    except Exception as e:
        logger.error(f"Fatal error in MCP server: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def cli_main():
    """CLI entry point for the AML Watcher MCP server."""
    parser = argparse.ArgumentParser(description='AML Watcher MCP Server')
    parser.add_argument('--api-key',
                        required=True,
                        help='AML Watcher API key')
    
    args = parser.parse_args()
    
    asyncio.run(main(
        api_key=args.api_key
    ))


if __name__ == "__main__":
    cli_main()
