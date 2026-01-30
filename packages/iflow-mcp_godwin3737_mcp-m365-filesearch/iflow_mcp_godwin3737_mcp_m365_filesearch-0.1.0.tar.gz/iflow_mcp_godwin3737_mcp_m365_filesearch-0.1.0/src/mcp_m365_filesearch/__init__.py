from mcp_m365_filesearch.server import mcp
import os
import sys

def main():
    """Initialize and run the MCP server."""

    # For testing purposes, don't require environment variables
    # required_keys = ["CLIENT_ID", "CLIENT_SECRET", "TENANT_ID"]

    # # Check for required environment variables
    # for key in required_keys:
    #     if key not in os.environ:
    #         print(
    #             f"Error: ${key} environment variable is required",
    #             file=sys.stderr,
    #         )
    #         sys.exit(1)

    print("Starting Microsoft 365 Search MCP server...", file=sys.stderr)

    mcp.run(transport="stdio")

__all__ = ["main", "mcp"]