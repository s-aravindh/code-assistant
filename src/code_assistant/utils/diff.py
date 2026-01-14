"""Diff generation and display utilities (Claude Code style)."""

import difflib


def generate_diff(original: str, modified: str, filename: str = "file") -> str:
    """Generate a unified diff between two strings."""
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    return ''.join(diff)


def format_diff_rich(diff: str) -> str:
    """Format diff with rich markup for TUI display (Claude Code style)."""
    if not diff.strip():
        return "[dim]No changes[/dim]"

    lines = []
    for line in diff.split('\n'):
        if line.startswith('+++') or line.startswith('---'):
            lines.append(f"[bold white]{line}[/bold white]")
        elif line.startswith('@@'):
            lines.append(f"[bold cyan]{line}[/bold cyan]")
        elif line.startswith('+'):
            lines.append(f"[green]{line}[/green]")
        elif line.startswith('-'):
            lines.append(f"[red]{line}[/red]")
        else:
            lines.append(f"[dim]{line}[/dim]")
    return '\n'.join(lines)


def format_file_change(filename: str, original: str, modified: str) -> str:
    """Format a file change for display (Claude Code style).

    Returns a formatted string showing:
    - File path
    - Line counts (+added/-removed)
    - Colored diff
    """
    diff = generate_diff(original, modified, filename)
    if not diff.strip():
        return f"[dim]No changes to {filename}[/dim]"

    # Count additions and deletions
    additions = sum(1 for line in diff.split('\n') if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff.split('\n') if line.startswith('-') and not line.startswith('---'))

    header = f"[bold]📄 {filename}[/bold] [green]+{additions}[/green] [red]-{deletions}[/red]"
    formatted_diff = format_diff_rich(diff)

    return f"{header}\n{formatted_diff}"


def format_new_file(filename: str, content: str) -> str:
    """Format a new file creation for display."""
    line_count = len(content.splitlines())
    preview_lines = content.splitlines()[:10]
    preview = '\n'.join(f"[green]+{line}[/green]" for line in preview_lines)

    if line_count > 10:
        preview += f"\n[dim]... and {line_count - 10} more lines[/dim]"

    return f"[bold]📄 {filename}[/bold] [cyan](new file)[/cyan] [green]+{line_count}[/green] lines\n{preview}"


def format_delete_file(filename: str) -> str:
    """Format a file deletion for display."""
    return f"[bold red]🗑️ {filename}[/bold red] [dim](deleted)[/dim]"
