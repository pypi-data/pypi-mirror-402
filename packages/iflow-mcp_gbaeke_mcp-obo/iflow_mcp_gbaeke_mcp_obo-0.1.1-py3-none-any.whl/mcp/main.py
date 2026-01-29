#!/usr/bin/env python3
"""
Simple MCP Server with with Azure Entra ID Authentication and OBO flow for Microsoft Search
"""

import logging
import os
from dotenv import load_dotenv
from fastmcp import FastMCP, Context
import asyncio
import random
import requests
import jwt
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import json

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Azure Entra ID configuration
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("API_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Check the required environment variables
if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
    logger.warning("TENANT_ID, CLIENT_ID, or CLIENT_SECRET not set. Running in demo mode without authentication.")

# API audience
API_AUDIENCE = f"api://{CLIENT_ID}" if CLIENT_ID else None

# Azure Entra ID JWKS endpoint
JWKS_URI = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys" if TENANT_ID else None

# Create the MCP server without authentication (for compatibility with FastMCP 2.4.0)
mcp = FastMCP("Simple Reverse Server with Azure Auth")

async def exchange_token(original_token: str, scope: str) -> dict:
    """
    Exchange JWT token for downstream service token using OBO flow
    """
    if not CLIENT_SECRET:
        return {
            "success": False,
            "error": "CLIENT_SECRET not configured",
            "method": "OBO"
        }

    obo_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "assertion": original_token,
        "scope": scope,
        "requested_token_use": "on_behalf_of"
    }

    try:
        response = requests.post(obo_url, data=data)

        if response.status_code == 200:
            token_data = response.json()
            return {
                "success": True,
                "access_token": token_data["access_token"],
                "expires_in": token_data.get("expires_in"),
                "token_type": token_data.get("token_type"),
                "scope_used": scope,
                "method": "OBO"
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code,
                "scope_attempted": scope,
                "method": "OBO"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "method": "OBO"
        }

def decode_token_info(token: str) -> dict:
    """
    Decode token to show basic info (without verification)
    """
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return {
            "audience": decoded.get("aud"),
            "issuer": decoded.get("iss"),
            "subject": decoded.get("sub"),
            "user_id": decoded.get("oid"),
            "email": decoded.get("email"),
            "scopes": decoded.get("scp"),
            "expires": decoded.get("exp"),
            "roles": decoded.get("roles"),
            "app_id": decoded.get("appid")
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_documents(ctx: Context, query: str = "*") -> dict:
    """
    Retrieve documents from Azure Search using the provided query.

    Args:
        ctx: FastMCP context
        query: The search query

    Returns:
        list of documents
    """
    logger.info(f"get_documents called with query: {query}")

    # Check if Azure Search credentials are configured
    azure_search_key = os.getenv("AZURE_SEARCH_KEY")
    if not azure_search_key or azure_search_key == "test_search_key":
        logger.warning("Azure Search not properly configured. Returning demo data.")
        return {
            "documents": [
                {"name": "Demo Document 1", "oid": "demo-oid-1", "group": "demo-group-1"},
                {"name": "Demo Document 2", "oid": "demo-oid-2", "group": "demo-group-2"}
            ],
            "note": "This is demo data. Configure AZURE_SEARCH_KEY to use real Azure Search."
        }

    try:
        search_client = SearchClient(
            endpoint="https://srch-geba.search.windows.net",
            index_name="document-permissions-push-idx",
            credential=AzureKeyCredential(azure_search_key)
        )
        results = search_client.search(
            search_text="*",
            select="name,oid,group",
            order_by="id asc"
        )
        documents = [
            {
                "name": result.get("name"),
                "oid": result.get("oid"),
                "group": result.get("group")
            }
            for result in results
        ]
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        return {
            "error": f"Could not retrieve documents: {str(e)}",
            "documents": []
        }


@mcp.tool()
async def search_documents(ctx: Context, query: str) -> dict:
    """
    Search for documents in Azure Search using a specific query.

    Args:
        ctx: FastMCP context
        query: The search query string

    Returns:
        Search results with matching documents
    """
    logger.info(f"search_documents called with query: {query}")

    # Check if Azure Search credentials are configured
    azure_search_key = os.getenv("AZURE_SEARCH_KEY")
    if not azure_search_key or azure_search_key == "test_search_key":
        logger.warning("Azure Search not properly configured. Returning demo data.")
        return {
            "query": query,
            "documents": [
                {"name": f"Demo result for: {query}", "oid": "demo-oid-1", "group": "demo-group-1"}
            ],
            "note": "This is demo data. Configure AZURE_SEARCH_KEY to use real Azure Search."
        }

    try:
        search_client = SearchClient(
            endpoint="https://srch-geba.search.windows.net",
            index_name="document-permissions-push-idx",
            credential=AzureKeyCredential(azure_search_key)
        )
        results = search_client.search(
            search_text=query,
            select="name,oid,group",
            order_by="id asc"
        )
        documents = [
            {
                "name": result.get("name"),
                "oid": result.get("oid"),
                "group": result.get("group")
            }
            for result in results
        ]
        return {"query": query, "documents": documents}
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return {
            "query": query,
            "error": f"Could not search documents: {str(e)}",
            "documents": []
        }


def main():
    """Main entry point for the FastMCP server"""
    logger.info("Starting FastMCP server...")
    if TENANT_ID:
        logger.info(f"Azure Tenant ID: {TENANT_ID}")
        logger.info(f"Azure Client ID: {CLIENT_ID}")
        logger.info(f"JWKS URI: {JWKS_URI}")
    else:
        logger.info("Running in demo mode without Azure authentication")

    try:
        # Run the server with HTTP transport
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8000
        )
    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise


if __name__ == "__main__":
    main()