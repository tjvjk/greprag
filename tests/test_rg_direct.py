"""Test ripgrep directly to see what it returns."""

import asyncio


async def test_rg():
    """Test ripgrep command."""
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

    print(f"Running command: {' '.join(cmd)}")
    print("=" * 70)

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    result = stdout.decode() if stdout else "No matches found"

    print(f"Return code: {proc.returncode}")
    print(f"Stdout length: {len(stdout) if stdout else 0} bytes")
    print(f"Stderr length: {len(stderr) if stderr else 0} bytes")
    print(f"Result length: {len(result)} chars")
    print("Result preview (first 500 chars):")
    print(result[:500])
    print("=" * 70)

    # Try parsing
    if result != "No matches found":
        lines = result.split("\n")
        print(f"Total lines in result: {len(lines)}")
        print("First 5 lines:")
        for i, line in enumerate(lines[:5], 1):
            print(f"  {i}: {line[:100]}")


if __name__ == "__main__":
    asyncio.run(test_rg())
