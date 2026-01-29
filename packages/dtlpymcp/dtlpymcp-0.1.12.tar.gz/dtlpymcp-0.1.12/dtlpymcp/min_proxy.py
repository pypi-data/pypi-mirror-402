from mcp.server.fastmcp import FastMCP, Context
from typing import Any
import traceback
import os
import logging
from mcp.server.fastmcp.tools.base import Tool, FuncMetadata
from pydantic import create_model
from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase
from dtlpymcp.utils.dtlpy_context import DataloopContext

logger = logging.getLogger(__name__)


def create_dataloop_mcp_server() -> FastMCP:
    """Create a FastMCP server for Dataloop with Bearer token authentication."""

    async def test(ctx: Context, ping: Any = None) -> dict[str, Any]:
        """Health check tool. Returns status ok and echoes ping if provided."""
        result = {"status": "ok"}
        if ping is not None:
            result["ping"] = ping
        return result

    app = FastMCP(
        name="Dataloop MCP Server",
        instructions="A multi-tenant MCP server for Dataloop with authentication",
        debug=True,
        log_level="DEBUG",
    )
    tool_name = "test"
    input_schema = {"type": "object", "properties": {"ping": {"type": "string", "default": "pong"}}, "required": ["ping"]}
    # Create Dataloop context
    dynamic_pydantic_model_params = DataloopContext.build_pydantic_fields_from_schema(input_schema)
    arguments_model = create_model(f"{tool_name}Arguments", **dynamic_pydantic_model_params, __base__=ArgModelBase)
    resp = FuncMetadata(arg_model=arguments_model)

    app._tool_manager._tools[tool_name] = Tool(
        fn=test,
        name=tool_name,
        description="Test tool for health checks",
        parameters=input_schema,
        is_async=True,
        context_kwarg="ctx",
        fn_metadata=resp,
        annotations=None,
    )

    return app


def main() -> int:
    logger.info("Starting Dataloop MCP server in stdio mode")

    # Validate environment variables
    if not os.environ.get('DATALOOP_API_KEY'):
        logger.error("DATALOOP_API_KEY environment variable is required")
        return 1

    try:
        mcp_server = create_dataloop_mcp_server()
        logger.info("Dataloop MCP server created successfully")
        logger.info("Starting server in stdio mode...")
        mcp_server.run(transport="stdio")
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    main()
