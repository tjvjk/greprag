import asyncio
import secrets
import tempfile
from pathlib import Path

import settings
from search_agent.agent import list_folder


class TestListFolder:
    """Tests for list_folder function that discovers files in topic folders."""

    def test_returns_full_paths_for_prefixed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = settings.DOCS_FOLDER
            settings.DOCS_FOLDER = tmp
            try:
                prefix = f"topic_{secrets.token_hex(4)}"
                name = f"{prefix}_document.txt"
                (Path(tmp) / name).write_text("content")
                result = asyncio.run(list_folder(prefix))
                assert tmp in result, "expected full path in result"
                assert name in result, "expected filename in result"
            finally:
                settings.DOCS_FOLDER = original

    def test_returns_absolute_paths_usable_by_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = settings.DOCS_FOLDER
            settings.DOCS_FOLDER = tmp
            try:
                prefix = f"solid_{secrets.token_hex(4)}"
                name = f"{prefix}_Phase_diagram.txt"
                path = Path(tmp) / name
                path.write_text("pressure melting curve")
                result = asyncio.run(list_folder(prefix))
                lines = result.strip().split("\n")
                returned = lines[-1]
                assert Path(returned).exists(), "expected returned path to exist"
            finally:
                settings.DOCS_FOLDER = original

    def test_returns_no_files_message_for_unknown_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = settings.DOCS_FOLDER
            settings.DOCS_FOLDER = tmp
            try:
                folder = f"nonexistent_{secrets.token_hex(8)}"
                result = asyncio.run(list_folder(folder))
                assert "No files found" in result, "expected no files message"
            finally:
                settings.DOCS_FOLDER = original

    def test_lists_files_in_actual_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = settings.DOCS_FOLDER
            settings.DOCS_FOLDER = tmp
            try:
                folder = f"subdir_{secrets.token_hex(4)}"
                subdir = Path(tmp) / folder
                subdir.mkdir()
                name = f"document_{secrets.token_hex(4)}.txt"
                (subdir / name).write_text("nested content")
                result = asyncio.run(list_folder(folder))
                assert name in result, "expected filename in subdirectory listing"
                assert str(subdir) in result, "expected full path for subdirectory"
            finally:
                settings.DOCS_FOLDER = original

    def test_handles_unicode_folder_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = settings.DOCS_FOLDER
            settings.DOCS_FOLDER = tmp
            try:
                prefix = f"тема_{secrets.token_hex(4)}"
                name = f"{prefix}_документ.txt"
                (Path(tmp) / name).write_text("содержимое")
                result = asyncio.run(list_folder(prefix))
                assert name in result, "expected unicode filename in result"
            finally:
                settings.DOCS_FOLDER = original

    def test_sorts_files_alphabetically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = settings.DOCS_FOLDER
            settings.DOCS_FOLDER = tmp
            try:
                prefix = f"sort_{secrets.token_hex(4)}"
                names = [f"{prefix}_zebra.txt", f"{prefix}_alpha.txt", f"{prefix}_beta.txt"]
                for name in names:
                    (Path(tmp) / name).write_text("content")
                result = asyncio.run(list_folder(prefix))
                alpha_pos = result.find("alpha")
                beta_pos = result.find("beta")
                zebra_pos = result.find("zebra")
                assert alpha_pos < beta_pos < zebra_pos, "expected alphabetical order"
            finally:
                settings.DOCS_FOLDER = original

    def test_excludes_directories_from_listing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = settings.DOCS_FOLDER
            settings.DOCS_FOLDER = tmp
            try:
                prefix = f"mixed_{secrets.token_hex(4)}"
                file_name = f"{prefix}_file.txt"
                dir_name = f"{prefix}_subdir"
                (Path(tmp) / file_name).write_text("content")
                (Path(tmp) / dir_name).mkdir()
                result = asyncio.run(list_folder(prefix))
                assert file_name in result, "expected file in result"
                assert dir_name not in result, "expected directory excluded"
            finally:
                settings.DOCS_FOLDER = original

    def test_strips_folder_path_prefix_from_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = settings.DOCS_FOLDER
            settings.DOCS_FOLDER = tmp
            try:
                prefix = f"nested_{secrets.token_hex(4)}"
                name = f"{prefix}_doc.txt"
                (Path(tmp) / name).write_text("content")
                result = asyncio.run(list_folder(f"docs/{prefix}"))
                assert name in result, "expected file found with path prefix"
            finally:
                settings.DOCS_FOLDER = original
