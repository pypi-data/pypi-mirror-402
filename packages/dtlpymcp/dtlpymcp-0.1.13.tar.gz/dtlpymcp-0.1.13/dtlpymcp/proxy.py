from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.tools.base import Tool, FuncMetadata
from typing import Any, Optional, List
import traceback
from datetime import datetime
from pathlib import Path
import os
import asyncio
import logging
from pydantic import create_model
from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase

from dtlpymcp.utils.dtlpy_context import DataloopContext


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration with the specified log level.
    
    Args:
        log_level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Setup logging directory and file
    log_dir = Path.home() / ".dataloop" / "mcplogs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # File handler with timestamp
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )

    # Console handler (default format)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(fmt="[%(levelname)s] %(name)s: %(message)s"))

    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(level=numeric_level, handlers=[file_handler, console_handler])

    # Get the main logger
    logger = logging.getLogger("dtlpymcp")
    logger.info(f"Logging configured with level: {log_level.upper()}")
    logger.info(f"Log file: {log_file}")
    
    return logger


def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running
        return asyncio.run(coro)
    else:
        # Already running event loop
        return loop.create_task(coro)


async def initialize_dataloop_context(sources_file: Optional[str] = None, init_timeout: float = 30.0) -> List[Tool]:
    """
    Initialize Dataloop context with timeout protection.

    Args:
        sources_file: Path to sources file
        init_timeout: Timeout in seconds for initialization

    Returns:
        List[Tool]: List of tools
    """
    logger = logging.getLogger("dtlpymcp")
    try:
        tools = []
        dl_context = DataloopContext(
            token=os.environ.get('DATALOOP_API_KEY'),
            env=os.environ.get('DATALOOP_ENV', 'prod'),
            sources_file=sources_file,
        )
        logger.info("Initializing Dataloop context...")
        await dl_context.initialize()
        logger.info("Dataloop context initialized successfully")

        logger.info(f"Adding tools from {len(dl_context.mcp_sources)} sources")
        for source in dl_context.mcp_sources:
            logger.info(f"Adding tools from source: {source.dpk_name}")
            for tool in source.tools:
                tools.append(tool)
                logger.info(f"Registered tool: {tool.name}")

        return tools

    except asyncio.TimeoutError:
        logger.error("Timeout during Dataloop context initialization")
        return []
    except Exception as e:
        logger.error(f"Failed to initialize Dataloop context: {e}")
        return []


def create_dataloop_mcp_server(sources_file: Optional[str] = None, init_timeout: float = 30.0) -> FastMCP:
    """Create a FastMCP server for Dataloop with Bearer token authentication."""

    async def test(ctx: Context, ping: Any = None) -> dict[str, Any]:
        """Health check tool. Returns status ok and echoes ping if provided."""
        result = {"status": "ok"}
        if ping is not None:
            result["ping"] = ping
        return result

    tool_name = "test"
    input_schema = {"type": "object", "properties": {"ping": {"type": "string"}}, "required": ["ping"]}
    dynamic_pydantic_model_params = DataloopContext.build_pydantic_fields_from_schema(input_schema)
    arguments_model = create_model(f"{tool_name}Arguments", **dynamic_pydantic_model_params, __base__=ArgModelBase)
    resp = FuncMetadata(arg_model=arguments_model)
    t = Tool(
        fn=test,
        name=tool_name,
        description="Test tool for health checks",
        parameters=input_schema,
        is_async=True,
        context_kwarg="ctx",
        fn_metadata=resp,
        annotations=None,
    )
    tools = [t]
    tools.extend(run_async(initialize_dataloop_context(sources_file=sources_file, init_timeout=init_timeout)))
    app = FastMCP(
        name="Dataloop MCP Server",
        instructions="A multi-tenant MCP server for Dataloop with authentication",
        debug=True,
        tools=tools,
    )

    return app


def main(sources_file: Optional[str] = None, init_timeout: float = 30.0, log_level: str = "INFO") -> int:
    # Setup logging with the specified level
    logger = setup_logging(log_level)
    
    logger.info("Starting Dataloop MCP server in stdio mode")

    # Validate environment variables
    if not os.environ.get('DATALOOP_API_KEY'):
        logger.error("DATALOOP_API_KEY environment variable is required")
        return 1

    try:
        mcp_server = create_dataloop_mcp_server(sources_file=sources_file, init_timeout=init_timeout)
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
