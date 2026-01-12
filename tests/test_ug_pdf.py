"""Test ugrep search with PDF support."""

import asyncio


async def test_ugrep_text():
    """Test ugrep command on text files."""
    pattern = "педагогик"
    target = "docs/livrezon"
    cmd = [
        "ug",
        "--line-number",
        "--context=2",
        "--ignore-case",
        "--filter=pdf:pdftotext % -",
        pattern,
        target,
    ]
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 70)
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await proc.communicate()
    result = stdout.decode() if stdout else "No matches found"
    print(f"Return code: {proc.returncode}")
    print(f"Result length: {len(result)} chars")
    print("Result preview (first 500 chars):")
    print(result[:500])
    print("=" * 70)


async def test_ugrep_pdf():
    """Test ugrep command on PDF files."""
    pattern = "trend"
    target = "docs/trends 2026"
    cmd = [
        "ug",
        "--line-number",
        "--context=2",
        "--ignore-case",
        "--filter=pdf:pdftotext % -",
        pattern,
        target,
    ]
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 70)
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await proc.communicate()
    result = stdout.decode() if stdout else "No matches found"
    print(f"Return code: {proc.returncode}")
    print(f"Result length: {len(result)} chars")
    print("Result preview (first 500 chars):")
    print(result[:500])
    print("=" * 70)


if __name__ == "__main__":
    print("Testing ugrep on text files:")
    asyncio.run(test_ugrep_text())
    print("\nTesting ugrep on PDF files:")
    asyncio.run(test_ugrep_pdf())
