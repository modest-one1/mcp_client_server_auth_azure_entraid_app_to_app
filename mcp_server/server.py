from __future__ import annotations
# from fastmcp import FastMCP
import math
from typing import List
import json
import os
from random import random
from rich import print
from fastmcp import FastMCP, Context
import asyncio
from fastmcp.server.auth import JWTVerifier
from logger import logger
from mcp_middleware import ListingFilterMiddleware
from dotenv import load_dotenv
load_dotenv()


# Azure Entra ID configuration
TENANT_ID = os.getenv("TENANT_ID", "your-tenant-id")
CLIENT_ID = os.getenv("CLIENT_ID", "your-client-id")
# API audience can be in multiple formats, so we'll define both common ones
API_AUDIENCE = os.getenv("API_AUDIENCE", f"api://{CLIENT_ID}")

# Azure Entra ID JWKS endpoint
JWKS_URI = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

# Configure Bearer Token authentication for Azure Entra ID
logger.info("Configuring Bearer Token authentication with audience: %s", API_AUDIENCE)
auth = JWTVerifier(
    jwks_uri=JWKS_URI,
    issuer=f"https://sts.windows.net/{TENANT_ID}/",  # Match the token's issuer format in the API
    algorithm="RS256",  # Azure Entra ID uses RS256
    audience=API_AUDIENCE,  # required audience
   # required_scopes=["execute"]  # Optional: add required scopes if needed
)

app = FastMCP("math-tools-server",auth=auth,port=8080, host="0.0.0.0")

middleware = ListingFilterMiddleware()

app.add_middleware(middleware)



@app.tool()
def alice(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

@app.tool()
def bob(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b

@app.tool()
def charlie(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

@app.tool()
def diana(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Division by zero.")
    return a / b

@app.tool()
def ethan(base: float, exponent: float) -> float:
    """Raise base to exponent."""
    return base ** exponent

@app.tool()
def frank(x: float) -> float:
    """Square root of x."""
    if x < 0:
        raise ValueError("Square root of negative number.")
    return math.sqrt(x)

@app.tool()
def grace(n: int) -> int:
    """Factorial of non-negative integer n."""
    if n < 0:
        raise ValueError("Factorial of negative number.")
    return math.factorial(n)

@app.tool()
def helen(values: List[float]) -> float:
    """Average of a list of numbers."""
    if not values:
        raise ValueError("Empty list.")
    return sum(values) / len(values)

@app.tool()
def ian(values: List[float]) -> float:
    """Maximum value in a list."""
    if not values:
        raise ValueError("Empty list.")
    return max(values)

@app.tool()
def julia(values: List[float]) -> float:
    """Minimum value in a list."""
    if not values:
        raise ValueError("Empty list.")
    return min(values)

if __name__ == "__main__":
    # Run the FastMCP server (default binds to localhost)
    app.run(transport="streamable-http")