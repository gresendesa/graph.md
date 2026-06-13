"""Template rendering representation and writing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class TemplateRenderError(RuntimeError):
    """Raised when a template cannot be rendered."""


@dataclass(frozen=True)
class RenderedFile:
    """A rendered template and its target path relative to the project root."""

    path: Path
    content: str


def write_rendered_files(project_root: Path, files: list[RenderedFile]) -> None:
    """Write rendered files under a project root using deterministic UTF-8 output."""
    for rendered in files:
        path = project_root / rendered.path
        path.parent.mkdir(parents=True, exist_ok=True)
        content = rendered.content
        if content and not content.endswith("\n"):
            content += "\n"
        path.write_text(content, encoding="utf-8")
