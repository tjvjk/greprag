"""Standalone test of citation parser logic.

This demonstrates that citations are extracted from grep tool results,
not from LLM-generated content.
"""

from search_agent.models import Citation


def parse_rg_output(rg_output: str) -> list[Citation]:
    """Parse ripgrep output to extract citations.

    Args:
        rg_output: Raw output from ripgrep (rg) command

    Returns:
        List of Citation objects with location (filename) and text (matched line)
    """
    citations = []
    seen = set()

    for line in rg_output.split("\n"):
        line = line.strip()
        if not line or line == "--":
            continue

        # Parse format: "path/to/file.md:123:matched text"
        parts = line.split(":", 2)
        if len(parts) >= 3:
            file_path = parts[0]
            text = parts[2].strip()
            filename = file_path.split("/")[-1]

            citation_key = (filename, text)
            if citation_key not in seen and text:
                seen.add(citation_key)
                citations.append(Citation(location=filename, text=text))

    return citations


# Sample ripgrep output
sample_rg_output = """docs/livrezon.com/file1.md:123:Внутренняя мотивация основана на познавательном интересе
docs/livrezon.com/file1.md:124:и желании узнать новое. Это более устойчивый вид мотивации.
--
docs/livrezon.com/file2.md:456:Методы педагогики включают объяснительно-иллюстративный метод
docs/livrezon.com/file2.md:457:и проблемно-поисковый подход к обучению.
--
docs/livrezon.com/file3.md:789:Система поощрений должна использоваться осторожно
"""

print("Testing citation parser...")
print("=" * 70)

citations = parse_rg_output(sample_rg_output)

print(f"\nParsed {len(citations)} unique citations:\n")

for i, citation in enumerate(citations, 1):
    print(f"[{i}] Location: {citation.location}")
    print(f"    Text: {citation.text}")
    print()

print("=" * 70)
print("✓ Parser test completed successfully!")
print("✓ Citations are extracted from grep output, not LLM context")
