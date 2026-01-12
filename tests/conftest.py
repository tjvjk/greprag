import logging
from pathlib import Path

import pytest

from search_agent.ugrep import UgrepSearch

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers and disable logging."""
    config.addinivalue_line(
        "markers",
        "integration: tests requiring external tools (ugrep, pdftotext)",
    )
    logging.disable(logging.CRITICAL)


@pytest.fixture
def gartner_pdf_path() -> str:
    """Path to Gartner PDF for integration tests."""
    return str(FIXTURES_DIR / "GARTNER - Technology Trends 2026_ACIG.pdf")


@pytest.fixture
def sample_txt_path() -> str:
    """Path to sample text file for integration tests."""
    return str(FIXTURES_DIR / "sample.txt")


@pytest.fixture
def search() -> UgrepSearch:
    """UgrepSearch instance for integration tests."""
    return UgrepSearch()
