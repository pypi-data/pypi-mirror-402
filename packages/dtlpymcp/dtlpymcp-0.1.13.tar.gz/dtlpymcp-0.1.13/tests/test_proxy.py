import asyncio
import random
import json
import sys
import os
from datetime import timedelta
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import dtlpy as dl

dl.setenv('prod')
if dl.token_expired():
    dl.login()
token = dl.token()
env = {"DATALOOP_API_KEY": str(token)} if token else None
# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command=sys.executable,  # Use current Python interpreter
    args=["-m", "dtlpymcp.min_proxy"],  # Run as module with start command
    env=env,  # Optional environment variables
    cwd=os.getcwd(),
)



async def test_health_check():
    print("[TEST CLIENT] Connecting to MCP server and calling test tool...")
    async with stdio_client(server=server_params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=60)) as session:
            await session.initialize()
            num = str(random.randint(1, 1000000))
            tool_result = await session.call_tool("test", {"ping": num})
            print("[RESULT]", tool_result)
            assert json.loads(tool_result.content[0].text).get("status") == "ok", "Health check failed!"
            assert json.loads(tool_result.content[0].text).get("ping") == num, "Ping failed!"


if __name__ == "__main__":
    

    asyncio.run(test_health_check())
