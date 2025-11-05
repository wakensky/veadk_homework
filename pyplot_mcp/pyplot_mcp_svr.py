import asyncio
import json
import sys
import logging
import random
import base64
import io
import uvicorn
from mcp import types as mcp_types
from mcp import server as mcp_server
from google.adk import tools as adk_tools
from veadk.tools.builtin_tools.web_search import web_search
from veadk import Agent
from veadk import Runner


def setup_logger() -> logging.Logger:
  logger = logging.getLogger("pyplot_mcp")
  if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
      "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
  logger.setLevel(logging.INFO)
  logger.propagate = False
  return logger
logger = setup_logger()

async def _web_search_for_statistics(
    prompt: str
):
  return await web_search(f'search statistics for {prompt}')

plotter = Agent(
    name="statistics_plotter",
    description="A tool for searching statistics for a given prompt.",
    instruction=(
      "Given a user prompt, call the `_web_search_for_statistics` tool to search statistics. "
      "Then generate python code matplotlib to plot the statistics."
    ),
    tools=[_web_search_for_statistics],
  )

# Initialize the MCP server
pyplot_mcp = mcp_server.Server("pyplot_mcp")

@pyplot_mcp.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
  return [
    mcp_types.Tool(
      name="draw",
      description="A tool for querying and drawing data",
      parameters=mcp_types.ToolParameter(
        name="query",
        description=("ask anything that could be answered by a plot depends on objective statistics."
                     "for example: the price of apple stock in 2025."),
        type=mcp_types.String,
        required=True,
      ),
    ), ]

@pyplot_mcp.call_tool()
async def call_draw(name: str, arguments: dict[str, any] | None) -> str:
  if name != "draw":
    return [
        mcp_types.TextContent(
            type="text",
            text=f"Unknown tool '{name}'",
        ),
    ]

  runner = Runner(
    agent=plotter,
    app_name="veadk-homework",
    user_id="veadk-homework-user",
  )
  response = asyncio.run(
    runner.run(messages=arguments["query"],
               session_id=f"veadk-homework-sess-{random.randint(1, 1000000)}")
  )
  return [mcp_types.TextContent(type="text", text=response.content)]

# Set up an HTTP session manager (stateless here keeps each HTTP call separate).
session_manager = mcp_server.streamable_http_manager.StreamableHTTPSessionManager(
    pyplot_mcp,
    json_response=True,   # or False if you prefer SSE streaming responses
    stateless=True,
)

class MCPHttpApp:
    """Minimal ASGI wrapper around the MCP HTTP transport."""
    def __init__(self, manager: mcp_server.streamable_http_manager.StreamableHTTPSessionManager):
        self._manager = manager
        self._context = None

    async def __call__(self, scope: dict[str, any], receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    self._context = self._manager.run()
                    await self._context.__aenter__()
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    if self._context is not None:
                        await self._context.__aexit__(None, None, None)
                    await send({"type": "lifespan.shutdown.complete"})
                    break
        elif scope["type"] == "http":
            await self._manager.handle_request(scope, receive, send)
        else:
            await send(
                {"type": "http.response.start", "status": 404, "headers": []}
            )
            await send(
                {"type": "http.response.body", "body": b"", "more_body": False}
            )

app = MCPHttpApp(session_manager)

if __name__ == "__main__":
  try:
      uvicorn.run(app, host="localhost", port=30123)
  except KeyboardInterrupt:
      print("\nMCP服务器 (stdio) 已被用户停止。", file=sys.stderr)
  except Exception as e:
      print(f"MCP服务器 (stdio) 遇到错误: {e}", file=sys.stderr)
  finally:
      print("MCP服务器 (stdio) 进程退出。", file=sys.stderr)
