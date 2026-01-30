import logging
import requests
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger()
mcp = FastMCP("transactions_server")


@mcp.tool()
def greetPeople(name: str) -> str:
    """Say hello to the person in a happy tone
        args:
            name: person name
        return: string
    """
    return "Hello " + name


if __name__ == "__main__":
    mcp.run(transport='stdio')
