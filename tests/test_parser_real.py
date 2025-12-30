"""Test parser with real ripgrep output."""

import asyncio
from search_agent.agent import parse_rg_output


async def test_real_rg():
    """Test with real ripgrep output."""
    pattern = "педагогик"
    search_target = "docs"

    cmd = [
        "rg",
        "--line-number",
        "--context=2",
        "--no-ignore",
        "--ignore-case",
        pattern,
        search_target,
    ]

    print("Running ripgrep...")
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    result = stdout.decode() if stdout else "No matches found"
    truncated_result = result[:10000]  # Same truncation as in rg_search function

    print(f"Result length: {len(result)} chars (truncated to {len(truncated_result)})")
    print("First 300 chars:")
    print(truncated_result[:300])
    print("=" * 70)

    if result != "No matches found":
        citations = parse_rg_output(truncated_result)
        print(f"\nParsed {len(citations)} unique citations")
        print("\nFirst 5 citations:")
        for i, citation in enumerate(citations[:5], 1):
            print(f"\n[{i}] Location: {citation.location}")
            print(f"    Text: {citation.text[:80]}...")


if __name__ == "__main__":
    asyncio.run(test_real_rg())
