import asyncio
import json
import logging
import sys
import time
from pathlib import Path

from openai import AsyncOpenAI

from search_agent.models import AgentResponse, AgentResult, UsageStats
from search_agent.parser import UgrepParser
from search_agent.prompts import SYSTEM_PROMPT_TEMPLATE
from search_agent.tools import TOOLS
from search_agent.ugrep import UgrepSearch
import settings

logger = logging.getLogger(__name__)
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY
)


async def tree() -> str:
    """Generate tree output of DOCS_FOLDER structure."""
    cmd = ["tree", "-L", "2", settings.DOCS_FOLDER]
    logger.debug(f"tree command: {' '.join(cmd)}")
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    result = stdout.decode() if stdout else ""
    if stderr:
        logger.debug(f"tree stderr: {stderr.decode()}")
    return result


async def list_folder(folder: str) -> str:
    """List files in a folder within DOCS_FOLDER."""
    base = Path(settings.DOCS_FOLDER)
    folder_name = folder.split("/")[-1]
    target = base / folder if not folder.startswith(str(base)) else Path(folder)
    if not target.exists():
        target = base / folder_name
    if target.exists() and target.is_dir():
        files = sorted([str(f) for f in target.iterdir() if f.is_file()])
        if files:
            return f"Files in {target.name}/:\n" + "\n".join(files)
    prefix = folder_name + "_"
    matching = sorted([str(f) for f in base.iterdir() if f.is_file() and f.name.startswith(prefix)])
    if matching:
        return f"Files with prefix '{prefix}':\n" + "\n".join(matching)
    return f"No files found for: {folder}"


async def run_agent(query: str, max_iterations: int = 15) -> AgentResult:
    """Run the search agent with the given query."""
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
    search = UgrepSearch()
    parser = UgrepParser()
    for _ in range(max_iterations):
        start = time.perf_counter()
        response = await client.chat.completions.create(
            model=settings.MODEL, messages=messages, tools=TOOLS
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
            if tc.function.name == "search":
                result = await search.execute(
                    args.get("pattern", ""),
                    args.get("path"),
                )
                logger.info("search: tool finished")
                logger.debug(f"search result preview: {result[:200]}...")
                if result != "No matches found":
                    citations = parser.parse(result)
                    collected_citations.extend(citations)
                    logger.info(f"Extracted {len(citations)} citations from search")
                else:
                    logger.info("No matches found for this search")
            elif tc.function.name == "list_folder":
                result = await list_folder(args.get("folder", ""))
                logger.info(f"list_folder: {result}...")
            else:
                result = f"Unknown tool: {tc.function.name}"
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
        model=settings.MODEL, messages=messages, response_format=AgentResponse
    )
    elapsed = time.perf_counter() - start
    stats.add(final_response.usage, elapsed)
    parsed_response = final_response.choices[0].message.parsed
    logger.info(
        f"Collected {len(collected_citations)} total citations from search results"
    )
    parsed_response.citations = collected_citations[:100]
    logger.info(f"Added {len(parsed_response.citations)} citations from search results")
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
    cost = agent_result.usage.cost(settings.INPUT_PRICE, settings.OUTPUT_PRICE)
    logger.info(f"Agent estimated cost: ${cost:.4f}")
    return agent_result


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    asyncio.run(run_agent(query))
