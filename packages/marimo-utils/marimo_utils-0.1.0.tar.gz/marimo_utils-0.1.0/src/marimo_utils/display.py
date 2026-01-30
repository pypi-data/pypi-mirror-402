from __future__ import annotations

import inspect
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import marimo as mo
from marimo._plugins.ui._core.ui_element import UIElement
from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)

__all__ = [
    "add_marimo_display",
    "defining_path",
    "relative_to_safe",
    "render_model",
    "resolve_repo_root",
]


def defining_path(obj: Any) -> Path | None:
    """Best-effort path to the file that defined `obj`."""
    src = inspect.getsourcefile(obj)
    if not src:
        try:
            src = inspect.getfile(obj)
        except TypeError:
            src = None
    if src:
        return Path(src).resolve()
    mod_name = getattr(obj, "__module__", None)
    mod = sys.modules.get(mod_name) if mod_name else None
    mod_file = getattr(mod, "__file__", None) if mod else None
    return Path(mod_file).resolve() if mod_file else None


def resolve_repo_root(model: BaseModel) -> Path:
    if hasattr(model, "repo_root"):
        repo_root = getattr(model, "repo_root")
        if repo_root:
            return Path(str(repo_root))
    if hasattr(model, "paths"):
        paths = getattr(model, "paths")
        if paths and hasattr(paths, "repo_root"):
            repo_root = getattr(paths, "repo_root")
            if repo_root:
                return Path(str(repo_root))
    return Path(__file__).resolve().parent.parent.parent


def relative_to_safe(path: Path, base: Path) -> Path:
    try:
        return path.relative_to(base)
    except ValueError:
        return path


def render_model(
    model: BaseModel, class_path: Path | str | None
) -> UIElement | mo.Html:
    class_path = class_path or "Unknown"
    rel_path = (
        class_path
        if isinstance(class_path, str)
        else relative_to_safe(class_path, resolve_repo_root(model))
    )
    rel_path_str = f"<small>`{rel_path}`</small>"
    return mo.vstack(
        [
            mo.md(f"**{model.__class__.__name__}** | {rel_path_str}"),
            model.model_dump(),
        ]
    )


def add_marimo_display() -> Callable[[type[TModel]], type[TModel]]:
    """Add a `_display_` method to Pydantic models for marimo rendering."""

    def decorator(cls: type[TModel]) -> type[TModel]:
        class_path = defining_path(cls)

        def _display_(self: BaseModel) -> UIElement | mo.Html:
            return render_model(self, class_path)

        setattr(cls, "_display_", _display_)
        return cls

    return decorator
