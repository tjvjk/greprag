from search_agent.parser import UgrepParser


class TestUgrepParser:
    """Tests for UgrepParser that extracts citations from ugrep output."""

    def test_returns_empty_list_for_empty_input(self) -> None:
        parser = UgrepParser()
        citations = parser.parse("")
        assert len(citations) == 0, "expected empty list for empty input"

    def test_parses_single_block_into_one_citation(self) -> None:
        output = """docs/folder/report.pdf:First line
docs/folder/report.pdf-Second line
docs/folder/report.pdf-Third line
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert len(citations) == 1, "expected single citation for one block"

    def test_separates_blocks_by_double_dash_delimiter(self) -> None:
        output = """docs/alpha.pdf:First match
--
docs/beta.pdf:Second match
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert len(citations) == 2, "expected two citations separated by delimiter"

    def test_extracts_filename_from_path(self) -> None:
        output = """docs/subdir/nested/report.pdf:Some content
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert citations[0].location == "report.pdf", "expected filename without path"

    def test_joins_multiple_lines_with_single_space(self) -> None:
        output = """docs/file.pdf:Alpha
docs/file.pdf-Beta
docs/file.pdf-Gamma
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert citations[0].text == "Alpha Beta Gamma", "expected space-joined text"

    def test_handles_cyrillic_and_unicode_characters(self) -> None:
        output = """docs/utf.pdf:Привет мир
docs/utf.pdf-你好世界
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert "Привет" in citations[0].text, "expected Cyrillic preserved"
        assert "你好" in citations[0].text, "expected Chinese preserved"

    def test_handles_emoji_in_text(self) -> None:
        output = """docs/emoji.pdf:Hello 🎉 World 🌍
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert "🎉" in citations[0].text, "expected emoji preserved"

    def test_ignores_lines_without_path_pattern(self) -> None:
        output = """Some garbage line
Another garbage
docs/file.pdf:Actual content
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert len(citations) == 1, "expected single citation"
        assert "garbage" not in citations[0].text, "expected garbage lines ignored"

    def test_handles_same_file_multiple_blocks(self) -> None:
        output = """docs/multi.pdf:First block
--
docs/multi.pdf:Second block
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert len(citations) == 2, "expected two citations from same file"
        assert citations[0].location == "multi.pdf", "expected same filename"
        assert citations[1].location == "multi.pdf", "expected same filename"

    def test_handles_empty_content_lines(self) -> None:
        output = """docs/empty.pdf:Content
docs/empty.pdf-
docs/empty.pdf:More content
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert "Content" in citations[0].text, "expected non-empty lines preserved"
        assert "More content" in citations[0].text, "expected non-empty lines preserved"

    def test_handles_colons_in_content(self) -> None:
        output = """docs/colon.pdf:Time: 10:30 AM
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert "10:30" in citations[0].text, "expected colons in content preserved"

    def test_handles_hyphens_in_content(self) -> None:
        output = """docs/hyphen.pdf-AI-powered technology
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert "AI-powered" in citations[0].text, (
            "expected hyphens in content preserved"
        )

    def test_handles_hyphens_in_filename(self) -> None:
        output = """docs/ACTIVATE - Technology & Media Outlook 2026.pdf:First line
docs/ACTIVATE - Technology & Media Outlook 2026.pdf-Second line
"""
        parser = UgrepParser()
        citations = parser.parse(output)
        assert len(citations) == 1, "expected single citation"
        assert citations[0].location == "ACTIVATE - Technology & Media Outlook 2026.pdf", (
            "expected full filename with hyphens preserved"
        )
        assert "First line" in citations[0].text, "expected content parsed correctly"
        assert "Second line" in citations[0].text, "expected context line parsed correctly"
