import asyncio

import pytest

from search_agent.ugrep import UgrepSearch


@pytest.mark.integration
class TestUgrepSearch:
    """Integration tests for UgrepSearch requiring ugrep and pdftotext."""

    def test_searches_pdf_file_and_returns_matches(
        self,
        search: UgrepSearch,
        gartner_pdf_path: str,
    ) -> None:
        result = asyncio.run(search.execute("trend", gartner_pdf_path))
        assert "trend" in result.lower(), "expected trend matches in Gartner PDF"

    def test_returns_no_matches_for_nonexistent_pattern(
        self,
        search: UgrepSearch,
        gartner_pdf_path: str,
    ) -> None:
        result = asyncio.run(search.execute("xyznonexistent", gartner_pdf_path))
        assert result == "No matches found", "expected no matches message"

    def test_respects_ugrep_config_case_insensitive(
        self,
        search: UgrepSearch,
        gartner_pdf_path: str,
    ) -> None:
        result = asyncio.run(search.execute("TREND", gartner_pdf_path))
        assert "trend" in result.lower(), "expected case-insensitive match from config"

    def test_handles_special_regex_characters_in_pattern(
        self,
        search: UgrepSearch,
        gartner_pdf_path: str,
    ) -> None:
        result = asyncio.run(search.execute("AI-powered", gartner_pdf_path))
        assert isinstance(result, str), "expected string result for regex pattern"

    def test_returns_context_lines_around_match(
        self,
        search: UgrepSearch,
        gartner_pdf_path: str,
    ) -> None:
        result = asyncio.run(search.execute("Strategic", gartner_pdf_path))
        assert "--" in result or result.count("\n") > 5, (
            "expected context lines in output"
        )

    def test_returns_filepath_in_output(
        self,
        search: UgrepSearch,
        gartner_pdf_path: str,
    ) -> None:
        result = asyncio.run(search.execute("2026", gartner_pdf_path))
        assert "GARTNER" in result, "expected filepath in output"

    def test_searches_plain_text_file(
        self,
        search: UgrepSearch,
        sample_txt_path: str,
    ) -> None:
        result = asyncio.run(search.execute("technology", sample_txt_path))
        assert "technology" in result.lower(), "expected match in text file"

    def test_searches_plain_text_returns_filename(
        self,
        search: UgrepSearch,
        sample_txt_path: str,
    ) -> None:
        result = asyncio.run(search.execute("AI", sample_txt_path))
        assert "sample.txt" in result, "expected filename in output"
