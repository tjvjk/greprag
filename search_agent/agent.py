import asyncio
import json
import logging
import sys
import time

from openai import AsyncOpenAI

from search_agent.models import AgentResponse, AgentResult, UsageStats
from search_agent.prompts import SYSTEM_PROMPT
from search_agent.tools import TOOLS
from settings import (
    DOCS_FOLDER,
    INPUT_PRICE,
    MODEL,
    OPENROUTER_API_KEY,
    OUTPUT_PRICE,
)

logger = logging.getLogger(__name__)
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY
)


async def rg_search(
    pattern: str,
    ignore_case: bool = True,
    context_lines: int = 2,
    fixed_string: bool = False,
    file_path: str | None = None,
) -> str:
    """Search for pattern using ripgrep.

    Args:
        pattern: Regex pattern to search for
        ignore_case: Case insensitive search (default: True)
        context_lines: Number of context lines to show (default: 2)
        fixed_string: Treat pattern as fixed string, not regex (default: False)
        file_path: Optional specific file or folder to search. If None, searches DOCS_FOLDER
    """
    cmd = ["rg", "--line-number", f"--context={context_lines}"]
    if ignore_case:
        cmd.append("--ignore-case")
    if fixed_string:
        cmd.append("--fixed-strings")

    # Default to searching the docs folder if no specific file provided
    search_target = file_path if file_path else DOCS_FOLDER
    cmd.extend([pattern, search_target])

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    result = stdout.decode() if stdout else "No matches found"
    return result[:10000]


async def read_lines(start_line: int, end_line: int, file_path: str) -> str:
    """Read specific line range from a file using sed.

    Args:
        start_line: Starting line number
        end_line: Ending line number
        file_path: Path to the file to read from (REQUIRED for multi-file support)
    """
    cmd = ["sed", "-n", f"{start_line},{end_line}p", file_path]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    result = stdout.decode() if stdout else ""
    return result[:10000]


async def execute_tool(name: str, args: dict) -> str:
    if name == "rg_search":
        return await rg_search(**args)
    elif name == "read_lines":
        return await read_lines(**args)
    return f"Unknown tool: {name}"


async def run_agent(query: str, max_iterations: int = 15) -> AgentResult:
    logger.info(f"Running agent for query: {query}")
    stats = UsageStats()
    tool_calls_log = []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    for _ in range(max_iterations):
        start = time.perf_counter()
        response = await client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        elapsed = time.perf_counter() - start
        stats.add(response.usage, elapsed)

        msg = response.choices[0].message

        msg_dict = {"role": msg.role, "content": msg.content or ""}
        if msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(msg_dict)

        if not msg.tool_calls:
            break

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            logger.info(f"{tc.function.name}: tool call {args}")
            tool_calls_log.append({tc.function.name: args})
            result = await execute_tool(tc.function.name, args)
            logger.info(f"{tc.function.name}: tool finished")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    messages.append(
        {
            "role": "user",
            "content": "Now provide your final answer in the required JSON format.",
        }
    )
    logger.info("Cooking json response")
    start = time.perf_counter()
    final_response = await client.beta.chat.completions.parse(
        model=MODEL, messages=messages, response_format=AgentResponse
    )
    elapsed = time.perf_counter() - start
    stats.add(final_response.usage, elapsed)

    agent_result = AgentResult(
        response=final_response.choices[0].message.parsed,
        usage=stats,
        tool_calls=tool_calls_log,
    )
    logger.info(f"Agent response: {agent_result.response.model_dump()}")
    logger.info(f"Agent usage: {agent_result.usage.model_dump()}")
    logger.info(f"Agent tool calls: {agent_result.tool_calls}")

    cost = agent_result.usage.cost(INPUT_PRICE, OUTPUT_PRICE)
    logger.info(f"Agent estimated cost: ${cost:.4f}")

    return agent_result


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    result = asyncio.run(run_agent(query))
    response_data = result.response.model_dump()
    logger.info(json.dumps(response_data, ensure_ascii=False, indent=2))
    logger.info(result.usage)
    logger.info(
        f"\nEstimated cost: ${result.usage.cost(INPUT_PRICE, OUTPUT_PRICE):.4f}"
    )
