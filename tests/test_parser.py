"""Tests for the citation parser module."""

import random
import string

from hamcrest import assert_that, equal_to, has_length

from search_agent.agent import parse_rg_output
from settings import DOCS_FOLDER


def random_suffix() -> str:
    """Generate random suffix for test uniqueness."""
    return "".join(random.choices(string.ascii_lowercase, k=6))


class TestParseRgOutput:
    """Tests for parse_rg_output function that extracts citations from ripgrep output."""

    def test_groups_context_lines_with_match_into_single_citation(self) -> None:
        suffix = random_suffix()
        output = f"""{DOCS_FOLDER}/FILE_{suffix}.pdf:100:Match line with AI
{DOCS_FOLDER}/FILE_{suffix}.pdf-101-Context line with 2028
{DOCS_FOLDER}/FILE_{suffix}.pdf-102-Another context line
"""
        citations = parse_rg_output(output)
        assert_that(
            len(citations),
            equal_to(1),
            "expected single citation for grouped context lines",
        )
        assert_that(
            "2028" in citations[0].text,
            equal_to(True),
            "expected context line content in citation text",
        )

    def test_separates_citations_by_double_dash_delimiter(self) -> None:
        suffix = random_suffix()
        output = f"""{DOCS_FOLDER}/A_{suffix}.pdf:10:First match
{DOCS_FOLDER}/A_{suffix}.pdf-11-First context
--
{DOCS_FOLDER}/B_{suffix}.pdf:20:Second match
{DOCS_FOLDER}/B_{suffix}.pdf-21-Second context
"""
        citations = parse_rg_output(output)
        assert_that(
            len(citations),
            equal_to(2),
            "expected two citations separated by delimiter",
        )

    def test_preserves_order_of_lines_in_grouped_citation(self) -> None:
        suffix = random_suffix()
        output = f"""{DOCS_FOLDER}/DOC_{suffix}.pdf-98-Before context
{DOCS_FOLDER}/DOC_{suffix}.pdf-99-Another before
{DOCS_FOLDER}/DOC_{suffix}.pdf:100:The match line
{DOCS_FOLDER}/DOC_{suffix}.pdf-101-After context
"""
        citations = parse_rg_output(output)
        assert_that(
            len(citations),
            equal_to(1),
            "expected single citation for contiguous block",
        )
        text = citations[0].text
        before_pos = text.find("Before context")
        match_pos = text.find("The match line")
        after_pos = text.find("After context")
        assert_that(
            before_pos < match_pos < after_pos,
            equal_to(True),
            "expected lines in original order",
        )

    def test_handles_non_ascii_characters_in_citation_text(self) -> None:
        suffix = random_suffix()
        output = f"""{DOCS_FOLDER}/УТФ_{suffix}.pdf:50:Привет мир 你好世界
{DOCS_FOLDER}/УТФ_{suffix}.pdf-51-Ещё текст émojis 🎉
"""
        citations = parse_rg_output(output)
        assert_that(
            len(citations),
            equal_to(1),
            "expected single citation with non-ASCII content",
        )
        assert_that(
            "Привет" in citations[0].text,
            equal_to(True),
            "expected Cyrillic text preserved",
        )

    def test_returns_empty_list_for_empty_input(self) -> None:
        citations = parse_rg_output("")
        assert_that(
            citations,
            has_length(0),
            "expected empty list for empty input",
        )

    def test_returns_empty_list_for_no_matches_message(self) -> None:
        citations = parse_rg_output("No matches found")
        assert_that(
            citations,
            has_length(0),
            "expected empty list for no matches message",
        )

    def test_extracts_filename_from_full_path(self) -> None:
        suffix = random_suffix()
        output = f"""{DOCS_FOLDER}/subdir/REPORT_{suffix}.pdf:42:Some text
"""
        citations = parse_rg_output(output)
        assert_that(
            len(citations),
            equal_to(1),
            "expected single citation extracted",
        )
        assert_that(
            citations[0].location,
            equal_to(f"REPORT_{suffix}.pdf"),
            "expected only filename without path",
        )

    def test_parses_grouped_format_with_filename_header(self) -> None:
        suffix = random_suffix()
        output = f"""{DOCS_FOLDER}/GROUPED_{suffix}.pdf
     1- First line
     2: Second line match
     3- Third line
"""
        citations = parse_rg_output(output)
        assert_that(
            len(citations),
            equal_to(1),
            "expected single citation from grouped format",
        )
        assert_that(
            citations[0].location,
            equal_to(f"GROUPED_{suffix}.pdf"),
            "expected filename from header line",
        )
        assert_that(
            "First line" in citations[0].text and "Second line" in citations[0].text,
            equal_to(True),
            "expected all lines joined in text",
        )

    def test_filters_out_metadata_lines_starting_with_url(self) -> None:
        suffix = random_suffix()
        output = f"""{DOCS_FOLDER}/META_{suffix}.pdf:1:url: https://example.com
{DOCS_FOLDER}/META_{suffix}.pdf:2:Actual content here
"""
        citations = parse_rg_output(output)
        texts = [c.text for c in citations]
        assert_that(
            any("url:" in t for t in texts),
            equal_to(False),
            "expected url metadata filtered out",
        )
