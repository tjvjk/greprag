import asyncio
from abc import ABC, abstractmethod
from typing import final

import settings

MAX_OUTPUT_CHARS = 30000


class Search(ABC):
    """Searches documents for patterns."""

    @abstractmethod
    async def execute(self, pattern: str, path: str | None) -> str:
        """Execute search and return raw output."""


@final
class UgrepSearch(Search):
    """Executes ugrep search with PDF support.

    Passes --config flag to ensure .ugrep file is loaded.

    >>> import asyncio
    >>> search = UgrepSearch()
    >>> result = asyncio.run(search.execute("test", "docs/"))
    >>> isinstance(result, str)
    True
    """

    def __init__(self) -> None:
        self._folder = settings.DOCS_FOLDER

    async def execute(self, pattern: str, path: str | None) -> str:
        """Execute ugrep search and return truncated output."""
        target = path if path else self._folder
        cmd = ["ug", "--config=.ugrep", "-r", pattern, target]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        result = stdout.decode() if stdout else "No matches found"
        return result[:MAX_OUTPUT_CHARS]
