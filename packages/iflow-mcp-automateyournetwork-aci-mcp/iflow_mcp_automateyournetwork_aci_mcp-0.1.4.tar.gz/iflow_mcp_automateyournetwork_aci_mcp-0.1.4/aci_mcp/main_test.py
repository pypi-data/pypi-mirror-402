import os
import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

# 禁用外部请求，仅用于测试
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ACIMCPServer")

# ------------------------------- Mock APIC Controller -------------------------------

class MockACIController:
    """Mock controller for testing without external dependencies"""

    def get_token(self):
        logger.info("✅ Mock authenticated with APIC.")
        return {}

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None):
        logger.info(f"Mock GET {endpoint} with params: {params}")
        return {
            "totalCount": "1",
            "imdata": [{
                "fvTenant": {
                    "attributes": {
                        "name": "MockTenant",
                        "status": "created"
                    }
                }
            }]
        }

    def post(self, endpoint: str, payload: Dict[str, Any]):
        logger.info(f"Mock POST {endpoint} with payload: {payload}")
        return {
            "totalCount": "1",
            "imdata": [{
                "fvTenant": {
                    "attributes": {
                        "name": payload.get("fvTenant", {}).get("attributes", {}).get("name", "Unknown"),
                        "status": "created"
                    }
                }
            }]
        }

    def put(self, endpoint: str, payload: Dict[str, Any]):
        logger.info(f"Mock PUT {endpoint} with payload: {payload}")
        return {"imdata": []}

    def delete(self, endpoint: str):
        logger.info(f"Mock DELETE {endpoint}")
        return {"imdata": []}

aci_controller = MockACIController()

# ------------------------------- Load URLs -------------------------------

def load_urls(file_path='urls.json') -> List[Dict[str, Any]]:
    try:
        with open(file_path, 'r') as f:
            raw = json.load(f)

        endpoints = []
        for item in raw:
            if "Group" in item:
                group = item["Group"]
                for ep in item["Endpoints"]:
                    ep["Group"] = group
                    endpoints.append(ep)
            else:
                item["Group"] = "ungrouped"
                endpoints.append(item)
        return endpoints
    except Exception as e:
        logger.error(f"❌ Failed to load URLS: {e}")
        return []

URLS = load_urls(os.getenv("URLS_PATH", "urls.json"))

# ------------------------------- FastMCP Setup -------------------------------

mcp = FastMCP(
    name="ACI MCP Server",
    instructions="Tools for full CRUD access to Cisco ACI API."
)

# ------------------------------- Input Models -------------------------------

class GroupToolInput(BaseModel):
    endpoint: str = Field(..., description="The endpoint URL within the group.")
    filter_expression: Optional[str] = Field(default=None)
    query_params: Optional[Dict[str, Any]] = Field(default=None)

class NonFilterableToolInput(BaseModel):
    query_params: Optional[Dict[str, Any]] = Field(default=None)

class CreateToolInput(BaseModel):
    payload: Dict[str, Any] = Field(..., description="JSON payload for POST.")

# ------------------------------- Tool Registration -------------------------------

# Group entries
grouped: Dict[str, List[Dict[str, Any]]] = {}

# Standalone entries
ungrouped: List[Dict[str, Any]] = []

# Separate into grouped and ungrouped
for entry in URLS:
    group = entry.get("Group", "ungrouped")
    if group == "ungrouped":
        ungrouped.append(entry)
    else:
        grouped.setdefault(group, []).append(entry)

# 1️⃣ Register grouped tools
for group, endpoints in grouped.items():
    endpoint_choices = [e["URL"] for e in endpoints if e.get("URL")]

    # Create closure for each group
    def make_group_tool(valid_endpoints, group_name):
        @mcp.tool()
        def group_tool(input: GroupToolInput) -> dict:
            """GET any endpoint from the specified group."""
            if input.endpoint not in valid_endpoints:
                raise ToolError(f"Invalid endpoint for group '{group_name}'. Must be one of: {valid_endpoints}")
            args = {}
            if input.filter_expression:
                args["query-target-filter"] = input.filter_expression
            if input.query_params:
                args.update(input.query_params)
            return aci_controller.get(input.endpoint, args)

        tool_base = re.sub(r'[^a-z0-9_-]', '_', group_name.replace(" ", "_").lower())
        group_tool.__name__ = f"{tool_base}_get"
        group_tool.__doc__ = f"GET any endpoint from group '{group_name}' ({len(valid_endpoints)} endpoints)."
        return group_tool

    make_group_tool(endpoint_choices, group)
    logger.info(f"✅ Registered grouped GET tool for {group} ({len(endpoint_choices)} endpoints)")

# 2️⃣ Register ungrouped tools as standalone CRUD
for entry in ungrouped:
    name = entry.get("Name", "") or entry["URL"].split("/")[-1]
    api_url_path = entry.get("URL")
    if not api_url_path:
        logger.warning(f"⚠️ Skipping: missing URL for {name}")
        continue

    tool_base = re.sub(r'[^a-z0-9_-]', '_', name.replace(" ", "_").lower())

    # READ
    def make_read_tool(endpoint: str, tool_name: str, desc_name: str):
        @mcp.tool()
        def read_tool(params: NonFilterableToolInput = Field(default_factory=NonFilterableToolInput)) -> dict:
            """GET data from ACI (ungrouped)."""
            args = {}
            if params.query_params:
                args.update(params.query_params)
            return aci_controller.get(endpoint, args)

        read_tool.__name__ = tool_name
        read_tool.__doc__ = f"GET data for {desc_name} from ACI (ungrouped)."
        return read_tool

    make_read_tool(api_url_path, f"{tool_base}_get", name or api_url_path)

    # CREATE (POST)
    def make_post_tool(endpoint: str, tool_name: str, desc_name: str):
        @mcp.tool()
        def post_tool(input: CreateToolInput) -> dict:
            """POST (create) data to ACI (ungrouped)."""
            return aci_controller.post(endpoint, input.payload)

        post_tool.__name__ = tool_name
        post_tool.__doc__ = f"POST (create) data to {desc_name} in ACI (ungrouped)."
        return post_tool

    make_post_tool(api_url_path, f"{tool_base}_post", name or api_url_path)

    # DELETE
    def make_delete_tool(endpoint: str, tool_name: str, desc_name: str):
        @mcp.tool()
        def delete_tool() -> dict:
            """DELETE resource at ACI (ungrouped)."""
            return aci_controller.delete(endpoint)

        delete_tool.__name__ = tool_name
        delete_tool.__doc__ = f"DELETE resource at {desc_name} in ACI (ungrouped)."
        return delete_tool

    make_delete_tool(api_url_path, f"{tool_base}_delete", name or api_url_path)

    logger.info(f"✅ Registered individual tools for {name or api_url_path}")

# ------------------------------- Entry Point -------------------------------

def main():
    if not URLS:
        logger.error("❌ No tools registered.")
    else:
        try:
            logger.info(f"🚀 Starting ACI FastMCP server...")
        except Exception as e:
            logger.error(f"Tool discovery error: {e}")
        asyncio.run(mcp.run_async())

def _main_async():
    """Async entry point for compatibility"""
    main()

if __name__ == "__main__":
    main()
    logger.info("🚀 ACI FastMCP server is running.")