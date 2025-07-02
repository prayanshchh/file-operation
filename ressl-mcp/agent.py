import os, json, httpx
from dotenv import load_dotenv
load_dotenv()
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("LLM_API_KEY"))
MCP_URL = os.getenv("MCP_URL", "http://localhost:3000/")

SSE_HEADERS  = {"accept": "text/event-stream"}               
JSON_HEADERS = {
    "accept": "application/json, text/event-stream",
    "content-type": "application/json"
}        

_tools_cache: list[dict] | None = None           

def _parse_sse_for_json(text: str):
    """Extract the first JSON object from SSE stream text."""
    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                return json.loads(line[len("data: "):])
            except Exception:
                continue
    raise RuntimeError("No valid JSON found in SSE response")

# ── helper: convert MCP schema → OpenAI schema ──────────────────────────
def _to_openai(tool: dict) -> dict:
    return {
        "type": "function",
        "function": {
            "name":        tool["name"],
            "description": tool.get("description", ""),
            "parameters":  tool["inputSchema"],   # already JSON-Schema
        },
    }

async def ensure_session() -> None:
    """
    For stateless MCP: just fetch the tool list, no session handshake.
    Handles both JSON and SSE responses.
    """
    global _tools_cache
    if _tools_cache:
        return

    async with httpx.AsyncClient() as client_httpx:
        payload = {
            "jsonrpc": "2.0",
            "id":      1,
            "method":  "tools/list",
            "params":  {},  # No session_id needed
        }
        rsp = await client_httpx.post(MCP_URL, json=payload,
                                headers=JSON_HEADERS, timeout=30)
        try:
            data = rsp.json()
        except Exception:
            # Try to parse as SSE
            data = _parse_sse_for_json(rsp.text)
        # Convert to OpenAI tool schema
        _tools_cache = [_to_openai(t) for t in data["result"]["tools"]]
        print("Tool list fetched from MCP server:", json.dumps(_tools_cache, indent=2))


async def rpc(method: str, params: dict | None = None, *, rid=1):
    """JSON-RPC helper for stateless MCP (no session_id). Handles JSON and SSE."""
    await ensure_session()
    body = {
        "jsonrpc": "2.0",
        "id":      rid,
        "method":  method,
        "params":  params or {},
    }
    async with httpx.AsyncClient() as client_httpx:
        rsp = await client_httpx.post(MCP_URL, json=body,
                                headers=JSON_HEADERS, timeout=30)
        try:
            data = rsp.json()
        except Exception:
            data = _parse_sse_for_json(rsp.text)
        if "error" in data:
            raise RuntimeError(data["error"])
        return data["result"]


async def call_tool(name: str, arguments: dict, *, rid=99):
    """Convenience wrapper for tools/call."""
    return await rpc("tools/call",
                     {"name": name, "arguments": arguments}, rid=rid)             # already OpenAI-schema

async def agent(
    user_msg: str,
    zip_filename: str,
    file_path: str,
    file_content: str,
    model: str = "gpt-4o-mini",
):
    """Round‑trip user prompt through an LLM that can call FastMCP tools."""
    await ensure_session()
    tools = _tools_cache              # ← use ready-made list

    messages = [
        {
            "role": "system",
            "content": "You are a file‑editing assistant. Call the provided tools when needed.",
        },
        {
            "role": "user",
            "content": (
                f"{user_msg}\n\n"
                f"File: {file_path}\n"
                f"Current content:\n{file_content}"
            ),
        },
    ]

    while True:
        chat = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = chat.choices[0].message
        messages.append(msg)   

        if msg.tool_calls:
            for call in msg.tool_calls:
                params = json.loads(call.function.arguments)
                # Unwrap if LLM returns {"params": {...}}
                if "params" in params and isinstance(params["params"], dict):
                    params = params["params"]
                # inject defaults the LLM might omit
                params["zip_filename"] = zip_filename 
                params["file_path"]   = file_path

                result = await call_tool(call.function.name, params, rid=call.id)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result if isinstance(result, str) else json.dumps(result),
                })
            continue

        return msg.content

if __name__ == "__main__":
    import asyncio
    async def test_tool_list():
        await ensure_session()
        print("\nFetched tool list from MCP server:")
        for tool in _tools_cache:
            print(f"- {tool['name']}: {tool.get('description', '')}")
    asyncio.run(test_tool_list())