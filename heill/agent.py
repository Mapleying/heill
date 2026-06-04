"""
Agentic loop — Ollama via OpenAI-compatible API.

Event shapes:
  {"type": "text", "content": "..."}
  {"type": "tool_start", "tool": "...", "tool_id": "..."}
  {"type": "tool_end", "tool": "...", "tool_id": "..."}
  {"type": "tool_error", "tool": "...", "tool_id": "...", "error": "..."}
  {"type": "done"}
  {"type": "error", "content": "..."}
"""
import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from heill.prompts import SYSTEM_PROMPT
from heill.session import save
from heill.tools.registry import TOOL_SCHEMAS, dispatch_tool

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    return _client


def _sse(**kwargs) -> str:
    return f"data: {json.dumps(kwargs)}\n\n"


async def run_agent(session: dict, supabase) -> AsyncIterator[str]:
    """Drive the agentic loop; yield SSE-formatted strings."""
    client = _get_client()
    rounds = 0

    while rounds < MAX_TOOL_ROUNDS:
        rounds += 1

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session["messages"]

        # Accumulate tool calls across stream chunks: {index: {id, name, arguments}}
        tool_calls_acc: dict[int, dict] = {}
        finish_reason: str | None = None

        stream = await client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            stream=True,
        )

        async for chunk in stream:
            choice = chunk.choices[0]
            delta = choice.delta

            if delta.content:
                yield _sse(type="text", content=delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {
                            "id": tc.id or f"call_{idx}",
                            "name": "",
                            "arguments": "",
                        }
                    if tc.id:
                        tool_calls_acc[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            if not tool_calls_acc[idx]["name"]:
                                tool_calls_acc[idx]["name"] = tc.function.name
                                yield _sse(
                                    type="tool_start",
                                    tool=tc.function.name,
                                    tool_id=tool_calls_acc[idx]["id"],
                                )
                        if tc.function.arguments:
                            tool_calls_acc[idx]["arguments"] += tc.function.arguments

            if choice.finish_reason:
                finish_reason = choice.finish_reason

        await stream.close()

        # Build assistant message for session history
        if tool_calls_acc:
            assistant_msg: dict = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls_acc.values()
                ],
            }
        else:
            # Collect any text that accumulated but wasn't a tool call
            assistant_msg = {"role": "assistant", "content": ""}

        session["messages"].append(assistant_msg)

        if finish_reason == "stop" or (finish_reason != "tool_calls" and not tool_calls_acc):
            await save(session, supabase)
            yield _sse(type="done")
            return

        if not tool_calls_acc:
            yield _sse(type="error", content=f"Unexpected finish reason: {finish_reason}")
            await save(session, supabase)
            return

        # Dispatch all tools concurrently
        tool_list = list(tool_calls_acc.values())
        logger.info("Dispatching tools: %s", [t["name"] for t in tool_list])

        results = await asyncio.gather(
            *[
                dispatch_tool(tc["name"], json.loads(tc["arguments"] or "{}"))
                for tc in tool_list
            ],
            return_exceptions=True,
        )

        for tc, result in zip(tool_list, results):
            if isinstance(result, Exception):
                yield _sse(type="tool_error", tool=tc["name"], tool_id=tc["id"], error=str(result))
                result_str = json.dumps({"error": str(result)})
            else:
                yield _sse(type="tool_end", tool=tc["name"], tool_id=tc["id"])
                result_str = json.dumps(result)

            session["messages"].append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_str,
            })

    yield _sse(type="error", content="Maximum tool iterations reached.")
    await save(session, supabase)
