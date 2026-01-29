from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase, FuncMetadata
from mcp.client.streamable_http import streamablehttp_client
from typing import List, Tuple, Callable, Optional
from mcp.server.fastmcp.tools.base import Tool
from pydantic import BaseModel, Field
from pydantic import create_model
from datetime import timedelta
from mcp import ClientSession
import dtlpy as dl
import traceback
import requests
import logging
import time
import jwt
import json

logger = logging.getLogger("dtlpymcp")


class MCPSource(BaseModel):
    dpk_name: Optional[str] = None
    app_url: Optional[str] = None
    dpk_version: Optional[str] = None
    app_trusted: Optional[bool] = None
    server_url: Optional[str] = None
    app_jwt: Optional[str] = None
    tools: Optional[List[Tool]] = []


class DataloopContext:
    """
    DataloopContext manages authentication, tool discovery, and proxy registration for Dataloop MCP servers.
    Handles JWTs, server URLs, and dynamic tool registration for multi-tenant environments.
    """

    def __init__(self, token: str = None, sources_file: str = None, env: str = 'prod'):
        self._token = token
        self.env = env
        self.mcp_sources: List[MCPSource] = []
        logger.info("DataloopContext initialized.")
        self.sources_file = sources_file
        self.initialized = False

    async def initialize(self, force: bool = False):
        if not self.initialized or force:
            await self.register_sources(self.sources_file)
            self.initialized = True

    async def register_sources(self, sources_file: str = None):
        if sources_file is None:
            logger.info("Loading MCP sources from all system apps")
            # load all system apps
            filters = dl.Filters(resource='apps')
            filters.add(field="dpkName", values="dataloop-mcp*")
            filters.add(field="scope", values="system")
            # IMPORTANT: Listing with `all()` cause everything to get stuck. getting only first page using `items` for now
            apps = dl.apps.list(filters=filters).items
            if len(apps) == 0:
                raise ValueError(f"No app found for DPK name: dataloop-mcp*")
            sources = []
            for app in apps:
                sources.append(
                    {
                        "dpk_name": app.dpk_name,
                        "dpk_version": app.dpk_version,	
                        "app_url": next(iter(app.routes.values())),
                        "server_url": None,
                        "app_jwt": None,
                    }
                )
        else:
            logger.info(f"Loading MCP sources from {sources_file}")

            with open(sources_file, "r") as f:
                sources = json.load(f)
        for entry in sources:
            try:
                if not isinstance(entry, dict):
                    raise ValueError(f"Invalid source entry: {entry}")
                logger.info(f"Adding MCP source: {entry.get('dpk_name')}, url: {entry.get('server_url')}")
                await self.add_mcp_source(MCPSource(**entry))
            except Exception as e:
                logger.error(f"Failed to add MCP source: {entry}\n{traceback.format_exc()}")

    async def add_mcp_source(self, mcp_source: MCPSource):

        if mcp_source.server_url is None:
            success = self.load_app_info(mcp_source)
            if not success:
                logger.error(f"Failed to load app info for source {mcp_source.dpk_name}")
                return
        result = await self.list_source_tools(mcp_source)
        if result is None:
            raise ValueError(f"Failed to discover tools for source {mcp_source.dpk_name}")
        server_name, tools, call_fn = result
        for tool in tools.tools:
            tool_name = tool.name
            ns_tool_name = f"{server_name}.{tool_name}"
            description = tool.description
            input_schema = tool.inputSchema
            
            # Normalize input schema to ensure it has "type": "object" at root level
            # This is required by the MCP specification
            input_schema = self.normalize_input_schema(input_schema)

            def build_handler(tool_name):
                async def inner(**kwargs):
                    fn = call_fn(tool_name, kwargs)
                    return await fn()

                return inner

            dynamic_pydantic_model_params = self.build_pydantic_fields_from_schema(input_schema)
            arguments_model = create_model(
                f"{tool_name}Arguments", **dynamic_pydantic_model_params, __base__=ArgModelBase
            )
            resp = FuncMetadata(arg_model=arguments_model)
            t = Tool(
                fn=build_handler(tool_name),
                name=ns_tool_name,
                description=description,
                parameters=input_schema,
                fn_metadata=resp,
                is_async=True,
                context_kwarg="ctx",
                annotations=None,
            )
            mcp_source.tools.append(t)
        self.mcp_sources.append(mcp_source)
        tool_str = ", ".join([tool.name for tool in mcp_source.tools])
        logger.info(f"Added MCP source: {mcp_source.dpk_name}, Available tools: {tool_str}")

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, token: str):
        self._token = token

    def load_app_info(self, source: MCPSource) -> bool:
        """
        Get the source URL and app JWT for a given DPK name using Dataloop SDK.
        """
        try:
            if source.app_url is None:
                dl.setenv(self.env)
                dl.client_api.token = self.token
                filters = dl.Filters(resource='apps')
                filters.add(field="dpkName", values=source.dpk_name)
                filters.add(field="scope", values="system")
                apps = list(dl.apps.list(filters=filters).all())
                if len(apps) == 0:
                    raise ValueError(f"No app found for DPK name: {source.dpk_name}")
                if len(apps) > 1:
                    logger.warning(f"Multiple apps found for DPK name: {source.dpk_name}, using first one")
                app = apps[0]
                logger.info(f"App: {app.name}")
                source.app_url = next(iter(app.routes.values()))
            dpk = dl.dpks.get(dpk_name=source.dpk_name, dpk_version=source.dpk_version).to_json()
            source.app_trusted = dpk.get('trusted', False)
            session = requests.Session()
            response = session.get(source.app_url, headers=dl.client_api.auth)
            logger.info(f"App route URL: {response.url}")
            source.server_url = response.url
            source.app_jwt = session.cookies.get("JWT-APP")
        except Exception:
            logger.error(f"Failed getting app info: {traceback.format_exc()}")
            return False
        return True

    @staticmethod
    def is_expired(app_jwt: str) -> bool:
        """
        Check if the APP_JWT is expired.

        Note: Verification is intentionally skipped - this is only used for
        client-side expiration checking. The server validates the JWT.
        """
        try:
            decoded = jwt.decode(
                app_jwt,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
            return decoded.get("exp", 0) < time.time()
        except Exception as e:
            logger.error(f"Error decoding JWT: {e}")
            return True

    def get_app_jwt(self, source: MCPSource, token: str) -> str:
        """
        Get the APP_JWT from the request headers or refresh if expired.
        """
        if source.app_url is None:
            raise ValueError("App URL is missing. Please set the app URL.")
        if source.app_jwt is None or self.is_expired(source.app_jwt):
            try:
                session = requests.Session()
                response = session.get(source.app_url, headers={'authorization': 'Bearer ' + token})
                source.app_jwt = session.cookies.get("JWT-APP")
            except Exception:
                raise Exception(f"Failed getting app JWT from cookies\n{traceback.format_exc()}") from None
        if not source.app_jwt:
            raise ValueError(
                "APP_JWT is missing. Please set the APP_JWT environment variable or ensure authentication is working."
            )
        return source.app_jwt

    @staticmethod
    def user_info(token: str) -> dict:
        """
        Decode a JWT token and return user info.

        Note: Verification is intentionally skipped - this is only used for
        reading claims client-side. The server validates the JWT.
        """
        return jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )

    async def list_source_tools(self, source: MCPSource) -> Tuple[str, List[dict], Callable]:
        """
        Discover tools for a given source and return (server_name, list_of_tools, call_fn).
        """
        if source.server_url is None:
            logger.error("DataloopContext required for DPK servers")
            raise ValueError("DataloopContext required for DPK servers")
        if source.app_trusted:
            headers = {"authorization": f"Bearer {self.token}", "x-dl-info": f"{self.token}"}
        else:
            headers = {"Cookie": f"JWT-APP={source.app_jwt}", "x-dl-info": f"{self.token}"}
        async with streamablehttp_client(source.server_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=60)) as session:
                await session.initialize()
                tools = await session.list_tools()

                def call_fn(tool_name, kwargs):
                    async def inner():
                        async with streamablehttp_client(source.server_url, headers=headers) as (read, write, _):
                            async with ClientSession(
                                read, write, read_timeout_seconds=timedelta(seconds=60)
                            ) as session:
                                await session.initialize()
                                return await session.call_tool(tool_name, kwargs)

                    return inner

                logger.info(f"Discovered {len(tools.tools)} tools for source {source.dpk_name}")
                return (source.dpk_name, tools, call_fn)

    @staticmethod
    def normalize_input_schema(input_schema: dict) -> dict:
        """
        Normalize input schema to ensure it conforms to MCP specification.
        The schema must have "type": "object" at the root level.
        """
        if not isinstance(input_schema, dict):
            return {"type": "object", "properties": {}, "required": []}
        
        # Create a copy to avoid mutating the original
        normalized = input_schema.copy()
        
        # Ensure type is "object" at root level
        if "type" not in normalized:
            normalized["type"] = "object"
        elif normalized.get("type") != "object":
            # If type exists but isn't "object", log a warning and fix it
            logger.warning(f"Input schema has type '{normalized.get('type')}' instead of 'object', fixing...")
            normalized["type"] = "object"
        
        # Ensure properties exist
        if "properties" not in normalized:
            normalized["properties"] = {}
        
        # Ensure required exists (can be empty list)
        if "required" not in normalized:
            normalized["required"] = []
        
        return normalized

    @staticmethod
    def openapi_type_to_python(type_str):
        return {"string": str, "integer": int, "number": float, "boolean": bool, "array": list, "object": dict}.get(
            type_str, str
        )

    @staticmethod
    def build_pydantic_fields_from_schema(input_schema):
        required = set(input_schema.get("required", []))
        properties = input_schema.get("properties", {})
        fields = {}
        for name, prop in properties.items():
            py_type = DataloopContext.openapi_type_to_python(prop.get("type", "string"))
            if name in required:
                fields[name] = (py_type, Field(...))
            else:
                default = prop.get("default", None)
                fields[name] = (py_type, Field(default=default))
        return fields
