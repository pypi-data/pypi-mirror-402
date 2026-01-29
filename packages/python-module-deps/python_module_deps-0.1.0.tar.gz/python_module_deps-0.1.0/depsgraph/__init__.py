"""Project-local dependency graph for a single Python file.

Given a project directory and a target Python file, this module prints the
project-internal import dependency graph (files only) as an ASCII tree and
optionally renders it as a Mermaid mindmap.

It only reports dependencies that resolve to Python files within the given
project directory. Stdlib and third-party imports are ignored by default.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


DEFAULT_IGNORED_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "site-packages",
    }
)


def _parse_args(argv:list[str]|None=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=("Show project-internal Python import dependencies for a file, as an ASCII graph and optionally a Mermaid mindmap."),)
    parser.add_argument("target", help="Target Python file path (absolute or relative to project dir).")
    parser.add_argument("--project-dir", default=".", help="Project directory to scan (default: current directory).")
    parser.add_argument("--max-depth", type=int, default=50, help="Maximum recursion depth (default: 50).")
    parser.add_argument("--show-missing", action="store_true", help="Also list imports that could not be resolved to project files.",)
    parser.add_argument("--no-mermaid", action="store_true", help="Do not generate Mermaid mindmap files.")
    parser.add_argument("--mermaid-mmd", default=None, help="Output path for Mermaid .mmd (default: <project-dir>/deps_graph.mmd).")
    parser.add_argument("--mermaid-html", default=None, help="Output path for Mermaid HTML (default: <project-dir>/deps_graph.html).")
    parser.add_argument("--ignored-dir", action="append", default=[], help=("Directory name to ignore (can be repeated). " "Defaults include .venv, .git, __pycache__, dist, build."),)
    return parser.parse_args(argv)


def _is_ignored_dir_name(dir_name: str, extra_ignored: frozenset[str]) -> bool:
    return dir_name in DEFAULT_IGNORED_DIR_NAMES or dir_name in extra_ignored


def _iter_python_files(project_dir: Path, extra_ignored: frozenset[str]) -> list[Path]:
    files: list[Path] = []
    for path in project_dir.rglob("*.py"):
        if not path.is_file():
            continue
        rel = path.relative_to(project_dir)
        if any(_is_ignored_dir_name(part, extra_ignored) for part in rel.parts[:-1]):
            continue
        files.append(path)
    files.sort()
    return files


def _has_init_file(directory: Path) -> bool:
    return (directory / "__init__.py").is_file()


def _compute_module_name(project_dir: Path, file_path: Path) -> str | None:
    """Best-effort module name for a file based on __init__.py packages.

    Returns None if the file isn't under any importable package structure.
    For top-level modules (project_dir/foo.py) it returns "foo".
    """
    rel = file_path.relative_to(project_dir)
    if rel.suffix != ".py":
        return None
    if len(rel.parts) == 1:
        return rel.stem
    parts = list(rel.parts)
    filename = parts.pop()
    if filename == "__init__.py":
        module_parts = parts
    else:
        module_parts = parts + [Path(filename).stem]
    current = project_dir
    package_parts: list[str] = []
    for part in module_parts[:-1]:
        current = current / part
        if not _has_init_file(current):
            return None
        package_parts.append(part)
    return ".".join(package_parts + [module_parts[-1]])


def _compute_parent_package(project_dir: Path, file_path: Path) -> list[str]:
    """Return the dotted package parts for the file's parent package."""
    rel = file_path.relative_to(project_dir)
    if len(rel.parts) == 1:
        return []
    directory_parts = list(rel.parts[:-1])
    current = project_dir
    package_parts: list[str] = []
    for part in directory_parts:
        current = current / part
        if not _has_init_file(current):
            break
        package_parts.append(part)
    return package_parts


def _build_module_index(project_dir: Path, python_files: list[Path]) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for file_path in python_files:
        module_name = _compute_module_name(project_dir, file_path)
        if module_name is None:
            continue
        index.setdefault(module_name, file_path)
    return index


def _parse_imports(file_path: Path) -> tuple[list[ast.AST], str | None]:
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [], f"read error: {exc}"
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        return [], f"syntax error: {exc.msg} (line {exc.lineno})"
    nodes: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            nodes.append(node)
    return nodes, None


def _resolve_from_import(*, current_package: list[str], module: str | None, level: int, imported_names: list[str],) -> list[str]:
    if level < 0:
        level = 0
    if level == 0:
        base_parts = []
    else:
        up = level - 1
        if up >= len(current_package):
            base_parts = []
        else:
            base_parts = current_package[: len(current_package) - up]
    module_parts = module.split(".") if module else []
    base_module_parts = base_parts + module_parts
    base_module = ".".join(base_module_parts)
    candidates: list[str] = []
    if base_module:
        candidates.append(base_module)
    for name in imported_names:
        if not name or name == "*":
            continue
        if base_module:
            candidates.append(f"{base_module}.{name}")
        else:
            candidates.append(name)
    return candidates


def _resolve_import_candidates(*, project_dir: Path, file_path: Path, import_node: ast.AST,) -> list[str]:
    current_package = _compute_parent_package(project_dir, file_path)
    if isinstance(import_node, ast.Import):
        names: list[str] = []
        for alias in import_node.names:
            if alias.name:
                names.append(alias.name)
        return names
    if isinstance(import_node, ast.ImportFrom):
        imported_names = [alias.name for alias in import_node.names if alias.name]
        return _resolve_from_import(current_package=current_package, module=import_node.module, level=import_node.level, imported_names=imported_names,)
    return []


def _direct_project_deps_for_file(*, project_dir: Path, file_path: Path, module_index: dict[str, Path],) -> tuple[list[Path], list[str], str | None]:
    nodes, error = _parse_imports(file_path)
    if error is not None:
        return [], [], error
    deps: dict[Path, None] = {}
    missing: dict[str, None] = {}
    for node in nodes:
        candidates = _resolve_import_candidates(project_dir=project_dir, file_path=file_path, import_node=node)
        matched_any = False
        for mod in candidates:
            target = module_index.get(mod)
            if target is None:
                continue
            deps[target] = None
            matched_any = True
        if not matched_any:
            for mod in candidates:
                missing[mod] = None
    dep_files = sorted(deps.keys(), key=lambda p: str(p))
    missing_imports = sorted(missing.keys())
    return dep_files, missing_imports, None


def _build_dependency_graph(*, project_dir: Path, root_file: Path, module_index: dict[str, Path], max_depth: int,) -> tuple[dict[Path, list[Path]], dict[Path, list[str]], dict[Path, str]]:
    edges: dict[Path, list[Path]] = {}
    missing_imports: dict[Path, list[str]] = {}
    file_errors: dict[Path, str] = {}
    to_visit: list[tuple[Path, int]] = [(root_file, 0)]
    visited: set[Path] = set()
    while to_visit:
        file_path, depth = to_visit.pop()
        if file_path in visited:
            continue
        visited.add(file_path)
        if depth > max_depth:
            continue
        deps, missing, error = _direct_project_deps_for_file(project_dir=project_dir, file_path=file_path, module_index=module_index,)
        if error is not None:
            file_errors[file_path] = error
            edges[file_path] = []
            continue
        edges[file_path] = deps
        if missing:
            missing_imports[file_path] = missing
        next_depth = depth + 1
        if next_depth <= max_depth:
            for dep in deps:
                if dep not in visited:
                    to_visit.append((dep, next_depth))
    return edges, missing_imports, file_errors


def _format_rel(project_dir: Path, file_path: Path) -> str:
    try:
        return str(file_path.relative_to(project_dir))
    except ValueError:
        return str(file_path)


def _render_ascii_tree(*, project_dir: Path, edges: dict[Path, list[Path]], root_file: Path, max_depth: int,) -> str:
    lines: list[str] = []
    def walk(node: Path, prefix: str, depth: int, stack: set[Path]) -> None:
        if depth > max_depth:
            return
        deps = edges.get(node, [])
        for i, dep in enumerate(deps):
            is_last = i == (len(deps) - 1)
            connector = "+-- "
            line_prefix = prefix + connector
            label = _format_rel(project_dir, dep)
            if dep in stack:
                lines.append(f"{line_prefix}{label} (cycle)")
                continue
            lines.append(f"{line_prefix}{label}")
            child_prefix = prefix + ("|   " if not is_last else "    ")
            stack.add(dep)
            walk(dep, child_prefix, depth + 1, stack)
            stack.remove(dep)
    lines.append(_format_rel(project_dir, root_file))
    walk(root_file, "", 0, {root_file})
    return "\n".join(lines)


def _render_mermaid_mindmap(*, project_dir: Path, edges: dict[Path, list[Path]], root_file: Path, max_depth: int,) -> str:
    lines: list[str] = ["mindmap"]
    root_label = _format_rel(project_dir, root_file)
    lines.append(f"  root(({root_label}))")
    def walk(node: Path, indent: str, depth: int, stack: set[Path]) -> None:
        if depth > max_depth:
            return
        deps = edges.get(node, [])
        for dep in deps:
            label = _format_rel(project_dir, dep)
            if dep in stack:
                lines.append(f"{indent}{label} (cycle)")
                continue
            lines.append(f"{indent}{label}")
            stack.add(dep)
            walk(dep, indent + "  ", depth + 1, stack)
            stack.remove(dep)
    walk(root_file, "    ", 0, {root_file})
    return "\n".join(lines)


def _write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _render_mermaid_html(mermaid_text: str) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "  <head>\n"
        "    <meta charset=\"utf-8\">\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "    <title>Dependency Mindmap</title>\n"
        "    <style>\n"
        "      body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 0; }\n"
        "      .wrap { padding: 24px; }\n"
        "    </style>\n"
        "  </head>\n"
        "  <body>\n"
        "    <div class=\"wrap\">\n"
        "      <div class=\"mermaid\">\n"
        f"{mermaid_text}\n"
        "      </div>\n"
        "    </div>\n"
        "    <script type=\"module\">\n"
        "      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';\n"
        "      mermaid.initialize({ startOnLoad: true });\n"
        "    </script>\n"
        "  </body>\n"
        "</html>\n"
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    project_dir = Path(args.project_dir).resolve()
    extra_ignored = frozenset(args.ignored_dir)
    target = Path(args.target)
    if not target.is_absolute():
        target = (project_dir / target).resolve()
    if not project_dir.is_dir():
        raise SystemExit(f"project dir not found: {project_dir}")
    if not target.is_file():
        raise SystemExit(f"target file not found: {target}")
    if target.suffix != ".py":
        raise SystemExit(f"target must be a .py file: {target}")
    python_files = _iter_python_files(project_dir, extra_ignored)
    module_index = _build_module_index(project_dir, python_files)
    edges, missing_imports, file_errors = _build_dependency_graph(project_dir=project_dir, root_file=target, module_index=module_index, max_depth=max(0, int(args.max_depth)))
    print(_render_ascii_tree(project_dir=project_dir, edges=edges, root_file=target, max_depth=args.max_depth))
    if not args.no_mermaid:
        mermaid_text = _render_mermaid_mindmap(project_dir=project_dir, edges=edges, root_file=target, max_depth=args.max_depth)
        mmd_path = Path(args.mermaid_mmd) if args.mermaid_mmd else project_dir / "deps_graph.mmd"
        html_path = Path(args.mermaid_html) if args.mermaid_html else project_dir / "deps_graph.html"
        _write_text_file(mmd_path, mermaid_text)
        _write_text_file(html_path, _render_mermaid_html(mermaid_text))
        print(f"\nMermaid mindmap saved: {mmd_path}")
        print(f"Open in browser: {html_path}")
    if file_errors:
        print("\nErrors:")
        for file_path in sorted(file_errors, key=lambda p: str(p)):
            print(f"- {_format_rel(project_dir, file_path)}: {file_errors[file_path]}")
    if args.show_missing and missing_imports:
        print("\nUnresolved imports (not in project):")
        for file_path in sorted(missing_imports, key=lambda p: str(p)):
            imports = missing_imports[file_path]
            if not imports:
                continue
            joined = ", ".join(imports)
            print(f"- {_format_rel(project_dir, file_path)}: {joined}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
