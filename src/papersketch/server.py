# src/papersketch/server.py

from .tools import mcp


def main() -> None:
    # Run the MCP server using Streamable HTTP transport.
    # By default this serves at:
    #   http://localhost:8000/mcp
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
