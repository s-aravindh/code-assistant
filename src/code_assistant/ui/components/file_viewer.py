"""File viewer widget with syntax highlighting and file search."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, TextArea, DirectoryTree, Input, OptionList
from textual.widgets.option_list import Option
from textual.message import Message


class FileViewer(ModalScreen):
    """Modal file viewer with syntax highlighting, directory browser, and file search."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close", show=False),
        Binding("tab", "switch_focus", "Switch"),
        Binding("ctrl+f", "toggle_search", "Search"),
    ]

    CSS = """
    FileViewer {
        align: center middle;
    }

    FileViewer > Vertical {
        width: 90%;
        height: 90%;
        background: $surface;
        border: thick $primary;
    }

    FileViewer #header {
        height: 3;
        background: $primary;
        color: $text;
        padding: 1;
    }

    FileViewer #search-bar {
        height: 3;
        background: $panel;
        display: none;
    }

    FileViewer #search-bar.visible {
        display: block;
    }

    FileViewer #search-bar Input {
        border: none;
        background: $surface;
        margin: 0 1;
    }

    FileViewer #content {
        height: 1fr;
    }

    FileViewer #tree-panel {
        width: 30%;
        border-right: solid $primary-darken-2;
    }

    FileViewer #search-results {
        height: 100%;
        display: none;
    }

    FileViewer #search-results.visible {
        display: block;
    }

    FileViewer #tree {
        height: 100%;
    }

    FileViewer #tree.hidden {
        display: none;
    }

    FileViewer #file-panel {
        width: 70%;
    }

    FileViewer DirectoryTree {
        height: 100%;
        scrollbar-gutter: stable;
    }

    FileViewer OptionList {
        height: 100%;
        border: none;
        background: transparent;
    }

    FileViewer #file-content {
        height: 100%;
    }

    FileViewer #footer {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }
    """

    class FileSelected(Message):
        """Message sent when a file is selected."""
        def __init__(self, path: str) -> None:
            self.path = path
            super().__init__()

    def __init__(self, root_path: str, initial_file: str | None = None):
        super().__init__()
        self.root_path = Path(root_path)
        self.initial_file = initial_file
        self.current_file: str | None = None
        self.search_active = False
        self.all_files: list[Path] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                "[bold]📁 File Viewer[/bold] [dim]Tab switch │ Ctrl+F search │ Esc close[/dim]",
                id="header"
            )

            with Vertical(id="search-bar"):
                yield Input(placeholder="Search files... (type to filter)", id="search-input")

            with Horizontal(id="content"):
                with Vertical(id="tree-panel"):
                    yield DirectoryTree(str(self.root_path), id="tree")
                    yield OptionList(id="search-results")

                with Vertical(id="file-panel"):
                    yield TextArea(
                        "",
                        id="file-content",
                        read_only=True,
                        show_line_numbers=True,
                        theme="monokai",
                    )

            yield Static("[dim]Ctrl+F to search files[/dim]", id="footer")

    def on_mount(self) -> None:
        """Load initial file if provided and index files."""
        self._index_files()
        if self.initial_file:
            self._load_file(self.initial_file)
        self.query_one("#tree", DirectoryTree).focus()

    def _index_files(self) -> None:
        """Index all files in the project for search."""
        self.all_files = []
        ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox", "dist", "build"}

        def scan_dir(path: Path, depth: int = 0) -> None:
            if depth > 10:  # Limit depth
                return
            try:
                for item in path.iterdir():
                    if item.name.startswith(".") and item.name not in {".env", ".gitignore"}:
                        continue
                    if item.is_dir():
                        if item.name not in ignore_dirs:
                            scan_dir(item, depth + 1)
                    elif item.is_file():
                        self.all_files.append(item)
            except PermissionError:
                pass

        scan_dir(self.root_path)
        self.all_files.sort(key=lambda p: p.name.lower())

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection from tree."""
        self._load_file(str(event.path))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle file selection from search results."""
        if event.option.id:
            self._load_file(event.option.id)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter files as user types in search."""
        if event.input.id == "search-input":
            self._filter_files(event.value)

    def _filter_files(self, query: str) -> None:
        """Filter files based on search query."""
        results = self.query_one("#search-results", OptionList)
        results.clear_options()

        if not query:
            # Show all files (limited)
            for file_path in self.all_files[:100]:
                rel_path = self._relative_path(file_path)
                results.add_option(Option(rel_path, id=str(file_path)))
            return

        query_lower = query.lower()
        matches = []

        for file_path in self.all_files:
            rel_path = self._relative_path(file_path)
            # Match against filename and path
            if self._fuzzy_match(query_lower, rel_path.lower()):
                matches.append((file_path, rel_path))
                if len(matches) >= 50:  # Limit results
                    break

        for file_path, rel_path in matches:
            results.add_option(Option(rel_path, id=str(file_path)))

        if matches:
            results.highlighted = 0

    def _fuzzy_match(self, query: str, text: str) -> bool:
        """Fuzzy match - all query chars must appear in order."""
        if not query:
            return True
        query_idx = 0
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
        return query_idx == len(query)

    def _relative_path(self, path: Path) -> str:
        """Get path relative to root."""
        try:
            return str(path.relative_to(self.root_path))
        except ValueError:
            return str(path)

    def _load_file(self, file_path: str) -> None:
        """Load and display a file."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return

        self.current_file = file_path
        content_area = self.query_one("#file-content", TextArea)
        footer = self.query_one("#footer", Static)

        try:
            # Check file size (limit to 1MB)
            if path.stat().st_size > 1024 * 1024:
                content_area.text = "# File too large to display (>1MB)"
                footer.update(f"[red]File too large: {file_path}[/red]")
                return

            content = path.read_text(encoding="utf-8", errors="replace")
            content_area.text = content

            # Set language based on extension
            lang = self._detect_language(path.suffix)
            content_area.language = lang

            # Update footer with file info
            lines = len(content.splitlines())
            size = path.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
            rel_path = self._relative_path(path)
            footer.update(f"[bold]{rel_path}[/bold] │ {lines} lines │ {size_str}")

        except Exception as e:
            content_area.text = f"# Error loading file: {e}"
            footer.update(f"[red]Error: {e}[/red]")

    def _detect_language(self, suffix: str) -> str | None:
        """Detect language from file extension."""
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".md": "markdown",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".rs": "rust",
            ".go": "go",
            ".rb": "ruby",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }
        return mapping.get(suffix.lower())

    def action_close(self) -> None:
        """Close the file viewer."""
        self.dismiss(self.current_file)

    def action_toggle_search(self) -> None:
        """Toggle the search bar."""
        self.search_active = not self.search_active

        search_bar = self.query_one("#search-bar")
        tree = self.query_one("#tree", DirectoryTree)
        results = self.query_one("#search-results", OptionList)
        search_input = self.query_one("#search-input", Input)

        if self.search_active:
            search_bar.add_class("visible")
            tree.add_class("hidden")
            results.add_class("visible")
            search_input.focus()
            self._filter_files("")  # Show all files initially
        else:
            search_bar.remove_class("visible")
            tree.remove_class("hidden")
            results.remove_class("visible")
            search_input.value = ""
            tree.focus()

    def action_switch_focus(self) -> None:
        """Switch focus between panels."""
        tree = self.query_one("#tree", DirectoryTree)
        results = self.query_one("#search-results", OptionList)
        content = self.query_one("#file-content", TextArea)
        search_input = self.query_one("#search-input", Input)

        if self.search_active:
            # Cycle: search input -> results -> content -> search input
            if search_input.has_focus:
                results.focus()
            elif results.has_focus:
                content.focus()
            else:
                search_input.focus()
        else:
            # Cycle: tree -> content -> tree
            if tree.has_focus:
                content.focus()
            else:
                tree.focus()
