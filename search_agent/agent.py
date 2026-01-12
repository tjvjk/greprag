import asyncio
import json
import logging
import sys
import time

from openai import AsyncOpenAI

from search_agent.models import AgentResponse, AgentResult, Citation, UsageStats
from search_agent.prompts import SYSTEM_PROMPT_TEMPLATE
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


async def tree() -> str:
    """Generate tree output of DOCS_FOLDER structure."""
    cmd = ["tree", "-L", "2", DOCS_FOLDER]
    logger.debug(f"tree command: {' '.join(cmd)}")
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    result = stdout.decode() if stdout else ""
    logger.debug(f"tree output:\n{result}")
    if stderr:
        logger.debug(f"tree stderr: {stderr.decode()}")
    return result


async def rg_search(
    pattern: str,
    ignore_case: bool = True,
    context_lines: int = 2,
    fixed_string: bool = False,
    file_path: str | None = None,
) -> str:
    """Search for pattern using ugrep with PDF support.

    Args:
        pattern: Regex pattern to search for
        ignore_case: Case insensitive search (default: True)
        context_lines: Number of context lines to show (default: 2)
        fixed_string: Treat pattern as fixed string, not regex (default: False)
        file_path: Optional specific file or folder to search. If None, searches DOCS_FOLDER
    """
    cmd = [
        "ug",
        "-r",
        "--line-number",
        f"--context={context_lines}",
        "--filter=pdf:pdftotext % -",
    ]
    if ignore_case:
        cmd.append("--ignore-case")
    if fixed_string:
        cmd.append("--fixed-strings")

    search_target = file_path if file_path else DOCS_FOLDER
    cmd.extend([pattern, search_target])

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await proc.communicate()
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
    stdout, _ = await proc.communicate()
    result = stdout.decode(errors="replace") if stdout else ""
    return result[:10000]


def parse_rg_output(rg_output: str) -> list[Citation]:
    """Parse ripgrep/ugrep output to extract citations with file locations and matched text.

    Handles two output formats:
    1. Standard format: path:line:text or path-line-text
    2. Grouped format: filename on own line, then lines like "  N: text" or "  N- text"

    Groups consecutive lines into single citations. Blocks separated by "--".

    Args:
        rg_output: Raw output from ripgrep/ugrep command

    Returns:
        List of Citation objects with location (filename) and grouped text

    >>> output = "docs/FILE.pdf:10:Match\\ndocs/FILE.pdf-11-Context"
    >>> citations = parse_rg_output(output)
    >>> len(citations)
    1
    """
    citations = []
    block = []
    filename = ""
    for line in rg_output.split("\n"):
        stripped = line.strip()
        if stripped == "--":
            if block:
                text = " ".join(block)
                citations.append(Citation(location=filename, text=text))
                block = []
            continue
        if f"/{DOCS_FOLDER}/" in stripped or stripped.startswith(f"{DOCS_FOLDER}/"):
            parts = stripped.split(":", 3)
            if len(parts) >= 3 and parts[1].isdigit():
                name = parts[0].split("/")[-1]
                if filename and filename != name and block:
                    text = " ".join(block)
                    citations.append(Citation(location=filename, text=text))
                    block = []
                filename = name
                content = ":".join(parts[2:]).strip()
                if content and not content.startswith(("url:", "title:", "---")):
                    block.append(content)
                continue
            parts = stripped.split("-", 3)
            if len(parts) >= 3 and parts[1].isdigit():
                name = parts[0].split("/")[-1]
                if filename and filename != name and block:
                    text = " ".join(block)
                    citations.append(Citation(location=filename, text=text))
                    block = []
                filename = name
                content = "-".join(parts[2:]).strip()
                if content and not content.startswith(("url:", "title:", "---")):
                    block.append(content)
                continue
            name = stripped.split("/")[-1]
            if filename and filename != name and block:
                text = " ".join(block)
                citations.append(Citation(location=filename, text=text))
                block = []
            filename = name
            continue
        if not filename:
            continue
        content = None
        for sep in [":", "-"]:
            idx = stripped.find(sep)
            if idx > 0 and stripped[:idx].strip().isdigit():
                content = stripped[idx + 1 :].strip()
                break
        if content is None:
            content = stripped
        if content and not content.startswith(("url:", "title:", "---")):
            block.append(content)
    if block:
        text = " ".join(block)
        citations.append(Citation(location=filename, text=text))
    return citations


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
    collected_citations = []
    structure = await tree()
    prompt = SYSTEM_PROMPT_TEMPLATE.format(tree=structure)
    logger.debug(f"System prompt:\n{prompt}")
    messages = [
        {"role": "system", "content": prompt},
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

            if tc.function.name == "rg_search":
                logger.debug(f"rg_search result preview: {result[:200]}...")
                if result != "No matches found":
                    citations_from_result = parse_rg_output(result)
                    collected_citations.extend(citations_from_result)
                    logger.info(
                        f"Extracted {len(citations_from_result)} citations from rg_search"
                    )
                else:
                    logger.info("No matches found for this search")

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    messages.append(
        {
            "role": "user",
            "content": "Now provide your final answer (question and answer only, no citations).",
        }
    )
    logger.info("Cooking json response")
    start = time.perf_counter()
    final_response = await client.beta.chat.completions.parse(
        model=MODEL, messages=messages, response_format=AgentResponse
    )
    elapsed = time.perf_counter() - start
    stats.add(final_response.usage, elapsed)

    parsed_response = final_response.choices[0].message.parsed
    logger.info(
        f"Collected {len(collected_citations)} total citations from grep results"
    )
    parsed_response.citations = collected_citations[:50]
    logger.info(f"Added {len(parsed_response.citations)} citations from grep results")

    agent_result = AgentResult(
        response=parsed_response,
        usage=stats,
        tool_calls=tool_calls_log,
    )
    response_data = agent_result.response.model_dump()
    logger.info(
        f"Agent response data: {json.dumps(response_data, ensure_ascii=False, indent=2)}"
    )
    logger.info(f"Agent usage: {agent_result.usage.model_dump()}")
    logger.info(f"Agent tool calls: {agent_result.tool_calls}")

    cost = agent_result.usage.cost(INPUT_PRICE, OUTPUT_PRICE)
    logger.info(f"Agent estimated cost: ${cost:.4f}")

    return agent_result


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    asyncio.run(run_agent(query))
