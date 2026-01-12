from abc import ABC, abstractmethod
from typing import final

from search_agent.models import Citation


class Parser(ABC):
    """Parses text output into citations."""

    @abstractmethod
    def parse(self, output: str) -> list[Citation]:
        """Parse output string into list of citations."""


@final
class Block:
    """Single context block from ugrep output.

    Accumulates lines until separator, then converts to Citation.

    >>> block = Block("report.pdf")
    >>> block.append("First line")
    >>> block.append("Second line")
    >>> citation = block.citation()
    >>> citation.text
    'First line Second line'
    """

    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._lines: list[str] = []

    def append(self, line: str) -> None:
        """Add a line to this block."""
        self._lines.append(line)

    def empty(self) -> bool:
        """Check if block has no content."""
        return len(self._lines) == 0

    def citation(self) -> Citation:
        """Convert block to Citation with merged text."""
        text = " ".join(self._lines)
        return Citation(location=self._filename, text=text)


@final
class UgrepParser(Parser):
    """Parses ugrep output format into citations.

    Handles format: path:content or path-content
    Blocks are separated by "--".
    Extracts filename from path and joins content lines.

    >>> parser = UgrepParser()
    >>> output = "docs/file.txt:Hello\\ndocs/file.txt-World\\n"
    >>> citations = parser.parse(output)
    >>> len(citations)
    1
    >>> citations[0].text
    'Hello World'
    """

    def __init__(self) -> None:
        self._block: Block | None = None
        self._citations: list[Citation] = []
        self._filename: str = ""

    def parse(self, output: str) -> list[Citation]:
        """Parse ugrep output into list of citations."""
        self._block = None
        self._citations = []
        self._filename = ""
        for line in output.split("\n"):
            self._process(line)
        self._flush()
        return self._citations

    def _process(self, line: str) -> None:
        """Process a single line of output."""
        stripped = line.strip()
        if stripped == "--":
            self._flush()
            return
        if "/" not in stripped:
            return
        for ext in (".pdf", ".txt", ".md"):
            idx = stripped.find(ext)
            if idx > 0:
                sep_idx = idx + len(ext)
                if sep_idx < len(stripped) and stripped[sep_idx] in (":", "-"):
                    path = stripped[:sep_idx]
                    content = stripped[sep_idx + 1 :].strip()
                    filename = path.split("/")[-1]
                    if self._filename != filename:
                        self._flush()
                        self._filename = filename
                        self._block = Block(filename)
                    if self._block is None:
                        self._block = Block(filename)
                    if content:
                        self._block.append(content)
                    return

    def _flush(self) -> None:
        """Emit current block as citation if non-empty."""
        if self._block is not None and not self._block.empty():
            self._citations.append(self._block.citation())
        self._block = None
