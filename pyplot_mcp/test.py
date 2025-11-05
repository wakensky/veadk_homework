#!/usr/bin/env python3
"""
Minimal MCP HTTP client:
  1. initialize
  2. send notifications/initialized
  3. tools/list
  4. tools/call -> draw
"""

import asyncio
import json
import sys

import aiohttp

SERVER_URL = "http://localhost:30123/"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


async def send(session: aiohttp.ClientSession, payload: dict) -> dict:
    async with session.post(SERVER_URL, json=payload, headers=HEADERS) as resp:
        resp.raise_for_status()
        text = await resp.text()
        if not text.strip():            # 204 or empty body
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise RuntimeError(f"Non-JSON response:\n{text}")


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        print("• initialize")
        init_result = await send(
            session,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"experimental": {}},
                    "clientInfo": {"name": "python-demo", "version": "0.1.0"},
                },
            },
        )
        print(json.dumps(init_result, indent=2), "\n")

        print("• notifications/initialized (optional)")
        initialized_result = await send(
            session,
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )
        # This request has no id; server usually replies with {"result":null}
        if initialized_result is not None:
          print(json.dumps(initialized_result, indent=2), "\n")
        else:
          print("No initialized result")

        print("• tools/list")
        list_result = await send(
            session,
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        print(json.dumps(list_result, indent=2), "\n")

        print("• tools/call -> draw")
        call_result = await send(
            session,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "draw",
                    "arguments": {"query": "apple stock price 2025"},
                },
            },
        )
        print(json.dumps(call_result, indent=2), "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)