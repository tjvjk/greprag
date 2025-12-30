"""Test script to verify citations are extracted from grep results."""

import asyncio
import logging

from search_agent.agent import run_agent
from settings import INPUT_PRICE, OUTPUT_PRICE

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():
    """Run a test query and display citations."""
    query = "методы педагогики"

    print(f"\n{'=' * 60}")
    print(f"Testing query: {query}")
    print(f"{'=' * 60}\n")

    result = await run_agent(query)

    print(f"\n{'=' * 60}")
    print("RESPONSE")
    print(f"{'=' * 60}")
    print(f"\nQuestion: {result.response.question}")
    print(f"\nAnswer: {result.response.answer[:500]}...")  # First 500 chars

    print(f"\n{'=' * 60}")
    print(f"CITATIONS ({len(result.response.citations)} total)")
    print(f"{'=' * 60}")

    for i, citation in enumerate(result.response.citations[:5], 1):  # Show first 5
        print(f"\n[{i}] Location: {citation.location}")
        print(f"    Text: {citation.text[:100]}...")  # First 100 chars

    print(f"\n{'=' * 60}")
    print("STATISTICS")
    print(f"{'=' * 60}")
    print(f"Tool calls: {len(result.tool_calls)}")
    print(result.usage)
    print(f"\nEstimated cost: ${result.usage.cost(INPUT_PRICE, OUTPUT_PRICE):.4f}")


if __name__ == "__main__":
    asyncio.run(main())
