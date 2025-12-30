"""Test the citation parser without needing API credentials."""

from search_agent.agent import parse_rg_output

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

print(f"\nParsed {len(citations)} citations:\n")

for i, citation in enumerate(citations, 1):
    print(f"[{i}] Location: {citation.location}")
    print(f"    Text: {citation.text}")
    print()

print("=" * 70)
print("✓ Parser test completed successfully!")
