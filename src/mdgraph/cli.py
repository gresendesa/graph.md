"""
CLI do mdgraph — entrypoint principal.

Comandos:
  get <URI>     Extrai uma secao com fidelidade documental (linhas brutas)
  tree <URI>    Exibe hierarquia visual de dependencias
  compose <URI> Materializa documento unificado (B-007)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from mdgraph.parser import ParseError, parse_file

app = typer.Typer(
    name="mdgraph",
    help="Motor CLI de parsing e composicao documental em grafos Markdown.",
    add_completion=False,
)

def _split_uri(uri: str) -> tuple[str, str]:
    """Divide 'arquivo.md#id' em ('arquivo.md', 'id'). Erro se sem fragmento."""
    if "#" not in uri:
        typer.echo(f"Erro: URI deve conter fragmento '#id'. Recebido: '{uri}'", err=True)
        raise typer.Exit(code=1)
    path_part, fragment = uri.split("#", 1)
    if not path_part:
        typer.echo(f"Erro: URI sem caminho de arquivo: '{uri}'", err=True)
        raise typer.Exit(code=1)
    if not fragment:
        typer.echo(f"Erro: URI sem id de secao: '{uri}'", err=True)
        raise typer.Exit(code=1)
    return path_part, fragment


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

@app.command()
def get(
    uri: str = typer.Argument(..., help="URI da secao no formato arquivo.md#id"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """
    Extrai uma secao com 100%% de fidelidade documental (linhas brutas do arquivo fonte).
    """
    file_path_str, section_id = _split_uri(uri)
    file_path = Path(file_path_str).resolve()

    if not file_path.exists():
        typer.echo(f"Erro: arquivo nao encontrado: '{file_path}'", err=True)
        raise typer.Exit(code=1)

    try:
        sections = parse_file(file_path)
    except ParseError as exc:
        typer.echo(f"Erro de parsing: {exc}", err=True)
        raise typer.Exit(code=1)

    matched = next(
        (s for s in sections if str(s.metadata.get("id", "")) == section_id),
        None,
    )

    if matched is None:
        typer.echo(
            f"Erro: secao '{section_id}' nao encontrada em '{file_path}'",
            err=True,
        )
        raise typer.Exit(code=1)

    # Fatiamento documental: preserva o texto exato do arquivo fonte
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    start = matched.raw.source_start_line - 1  # base-0
    end = matched.raw.source_end_line          # slice exclusivo = ultima linha inclusiva

    output = "".join(lines[start:end])
    # Garantir newline final sem adicionar extra
    if output and not output.endswith("\n"):
        output += "\n"

    if json_output:
        import json as json_mod
        typer.echo(json_mod.dumps({
            "uri": uri,
            "file_path": str(file_path),
            "source_start_line": matched.raw.source_start_line,
            "source_end_line": matched.raw.source_end_line,
            "content": output,
        }, ensure_ascii=False))
    else:
        typer.echo(output, nl=False)


# ---------------------------------------------------------------------------
# tree
# ---------------------------------------------------------------------------

@app.command()
def tree(
    uri: str = typer.Argument(..., help="URI da secao no formato arquivo.md#id"),
    root: Optional[Path] = typer.Option(
        None, "--root", "-r",
        help="Diretorio raiz do repositorio (padrao: diretorio do arquivo).",
    ),
    refs: bool = typer.Option(
        False, "--refs",
        help="Exibir backlinks (quem depende desta secao).",
    ),
    depth: Optional[int] = typer.Option(
        None, "--depth", "-d",
        help="Profundidade maxima da arvore (padrao: ilimitada).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """
    Exibe a hierarquia visual de dependencias de uma secao.
    """
    from mdgraph.index import index_repository

    file_path_str, section_id = _split_uri(uri)
    file_path = Path(file_path_str).resolve()

    repo_root = root.resolve() if root else file_path.parent

    try:
        graph = index_repository(repo_root)
    except ParseError as exc:
        typer.echo(f"Erro de parsing: {exc}", err=True)
        raise typer.Exit(code=1)

    # Montar URI absoluta para lookup
    abs_uri = str(file_path) + "#" + section_id

    if abs_uri not in graph.index.sections:
        typer.echo(f"Erro: URI '{abs_uri}' nao encontrada no indice.", err=True)
        raise typer.Exit(code=1)

    if json_output:
        import json as json_mod
        tree_data = _build_tree_outgoing(abs_uri, graph, visited=set(), depth=depth) if not refs else _build_tree_incoming(abs_uri, graph, visited=set(), depth=depth)
        typer.echo(json_mod.dumps({"uri": abs_uri, "tree": tree_data}, ensure_ascii=False))
    elif refs:
        _print_tree_incoming(abs_uri, graph, prefix="", visited=set(), depth=depth)
    else:
        _print_tree_outgoing(abs_uri, graph, prefix="", visited=set(), depth=depth)


def _label(uri: str, graph) -> str:
    section = graph.index.sections.get(uri)
    if section:
        title = section.metadata.get("title", section.metadata.get("id", uri))
        return f"{title}  [{uri}]"
    return uri


def _print_tree_outgoing(uri: str, graph, prefix: str, visited: set, depth: Optional[int] = None) -> None:
    marker = "(ciclo)" if uri in visited else ""
    typer.echo(f"{prefix}{_label(uri, graph)} {marker}".rstrip())
    if uri in visited:
        return
    if depth is not None and depth <= 0:
        return
    visited = visited | {uri}
    children = sorted(graph.outgoing_edges.get(uri, set()))
    next_depth = None if depth is None else depth - 1
    for i, child in enumerate(children):
        connector = "└── " if i == len(children) - 1 else "├── "
        _print_tree_outgoing(child, graph, prefix + connector, visited, next_depth)


def _print_tree_incoming(uri: str, graph, prefix: str, visited: set, depth: Optional[int] = None) -> None:
    marker = "(ciclo)" if uri in visited else ""
    typer.echo(f"{prefix}{_label(uri, graph)} {marker}".rstrip())
    if uri in visited:
        return
    if depth is not None and depth <= 0:
        return
    visited = visited | {uri}
    parents = sorted(graph.incoming_edges.get(uri, set()))
    next_depth = None if depth is None else depth - 1
    for i, parent in enumerate(parents):
        connector = "└── " if i == len(parents) - 1 else "├── "
        _print_tree_incoming(parent, graph, prefix + connector, visited, next_depth)


def _build_tree_outgoing(uri: str, graph, visited: set, depth: Optional[int] = None) -> list:
    if uri in visited or (depth is not None and depth <= 0):
        return []
    visited = visited | {uri}
    children = sorted(graph.outgoing_edges.get(uri, set()))
    next_depth = None if depth is None else depth - 1
    section = graph.index.sections.get(uri)
    edge_type = "include"  # default; edges are not typed in current model
    result = []
    for child in children:
        node = {
            "uri": child,
            "type": edge_type,
            "depth": (None if depth is None else depth - 1),
            "children": _build_tree_outgoing(child, graph, visited, next_depth),
        }
        result.append(node)
    return result


def _build_tree_incoming(uri: str, graph, visited: set, depth: Optional[int] = None) -> list:
    if uri in visited or (depth is not None and depth <= 0):
        return []
    visited = visited | {uri}
    parents = sorted(graph.incoming_edges.get(uri, set()))
    next_depth = None if depth is None else depth - 1
    result = []
    for parent in parents:
        node = {
            "uri": parent,
            "type": "incoming",
            "depth": (None if depth is None else depth - 1),
            "children": _build_tree_incoming(parent, graph, visited, next_depth),
        }
        result.append(node)
    return result


# ---------------------------------------------------------------------------
# compose
# ---------------------------------------------------------------------------

@app.command()
def compose(
    uri: str = typer.Argument(..., help="URI da secao raiz no formato arquivo.md#id"),
    root: Optional[Path] = typer.Option(
        None, "--root", "-r",
        help="Diretorio raiz do repositorio (padrao: diretorio do arquivo).",
    ),
    strict: bool = typer.Option(False, "--strict", help="Abortar em URI nao resolvida."),
    deduplicate: bool = typer.Option(False, "--deduplicate", help="Deduplicar nos repetidos."),
    json_output: bool = typer.Option(False, "--json", help="Exportar como JSON estruturado."),
    depth: Optional[int] = typer.Option(
        None, "--depth", "-d",
        help="Profundidade maxima de expansao de @include (padrao: ilimitada).",
    ),
) -> None:
    """
    Materializa um documento Markdown unificado expandindo @include recursivamente.
    """
    import json as json_mod
    from mdgraph.composer import compose as do_compose
    from mdgraph.index import index_repository

    file_path_str, section_id = _split_uri(uri)
    file_path = Path(file_path_str).resolve()

    if not file_path.exists():
        typer.echo(f"Erro: arquivo nao encontrado: '{file_path}'", err=True)
        raise typer.Exit(code=1)

    repo_root = root.resolve() if root else file_path.parent

    try:
        graph = index_repository(repo_root)
    except ParseError as exc:
        typer.echo(f"Erro de parsing: {exc}", err=True)
        raise typer.Exit(code=1)

    abs_uri = str(file_path) + "#" + section_id

    if abs_uri not in graph.index.sections:
        typer.echo(f"Erro: URI '{abs_uri}' nao encontrada no indice.", err=True)
        raise typer.Exit(code=1)

    collected_warnings: list[str] = []
    try:
        result = do_compose(
            abs_uri,
            graph,
            strict=strict,
            deduplicate=deduplicate,
            warnings=collected_warnings,
            depth=depth,
        )
    except ValueError as exc:
        typer.echo(f"Erro: {exc}", err=True)
        raise typer.Exit(code=1)

    for w in collected_warnings:
        typer.echo(f"Aviso: {w}", err=True)

    if json_output:
        typer.echo(json_mod.dumps({"uri": abs_uri, "content": result}, ensure_ascii=False))
    else:
        typer.echo(result, nl=False)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

@app.command()
def validate(
    root: Optional[Path] = typer.Option(
        None, "--root", "-r",
        help="Diretorio raiz do repositorio (padrao: diretorio atual).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Exportar resultado como JSON."),
) -> None:
    """
    Verifica a integridade estrutural do repositorio de grafos Markdown.

    Checks: broken refs/includes, duplicate section IDs, include cycles,
    sections without required payload.

    Exit code 0 = clean, 1 = errors found.
    """
    import json as json_mod
    from mdgraph.index import index_repository

    repo_root = (root.resolve() if root else Path.cwd())

    try:
        graph = index_repository(repo_root)
    except ParseError as exc:
        errors = [{"type": "parse_error", "uri": "", "detail": str(exc)}]
        summary = {"total_sections": 0, "total_edges": 0, "errors": 1, "warnings": 0}
        if json_output:
            typer.echo(json_mod.dumps({"errors": errors, "warnings": [], "summary": summary}, ensure_ascii=False))
        else:
            typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    errors: list[dict] = []
    warnings: list[dict] = []

    all_uris = set(graph.index.sections.keys())
    total_edges = sum(len(targets) for targets in graph.outgoing_edges.values())

    # 1. Broken refs and includes
    for src_uri, section in graph.index.sections.items():
        for directive in section.directives:
            if directive.type in ("ref", "include"):
                if directive.target_uri not in all_uris:
                    error_type = "broken_ref" if directive.type == "ref" else "broken_include"
                    errors.append({
                        "type": error_type,
                        "uri": src_uri,
                        "detail": f"target '{directive.target_uri}' not found in index",
                    })

    # 2. Include cycles (DFS execution-path tracking)
    def _dfs_cycle(uri: str, path: frozenset[str], visited_global: set[str]) -> None:
        if uri in path:
            errors.append({
                "type": "cycle",
                "uri": uri,
                "detail": f"include cycle detected involving '{uri}'",
            })
            return
        if uri in visited_global:
            return
        visited_global.add(uri)
        section = graph.index.sections.get(uri)
        if section is None:
            return
        new_path = path | {uri}
        for directive in section.directives:
            if directive.type == "include" and directive.target_uri in all_uris:
                _dfs_cycle(directive.target_uri, new_path, visited_global)

    visited_global: set[str] = set()
    for uri in all_uris:
        _dfs_cycle(uri, frozenset(), visited_global)

    summary = {
        "total_sections": len(all_uris),
        "total_edges": total_edges,
        "errors": len(errors),
        "warnings": len(warnings),
    }

    if json_output:
        typer.echo(json_mod.dumps(
            {"errors": errors, "warnings": warnings, "summary": summary},
            ensure_ascii=False,
            indent=2,
        ))
    else:
        if errors:
            for e in errors:
                typer.echo(f"ERROR [{e['type']}] {e['uri']}: {e['detail']}")
        if warnings:
            for w in warnings:
                typer.echo(f"WARNING [{w['type']}] {w['uri']}: {w['detail']}")
        if not errors and not warnings:
            typer.echo(f"OK — {summary['total_sections']} sections, {summary['total_edges']} edges, no issues found.")
        else:
            typer.echo(
                f"\nSummary: {summary['total_sections']} sections, "
                f"{summary['errors']} errors, {summary['warnings']} warnings.",
                err=True,
            )

    if errors:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# context (B-016)
# ---------------------------------------------------------------------------

@app.command()
def context(
    uri: str = typer.Argument(..., help="Section URI in the format file.md#id"),
    root: Optional[Path] = typer.Option(
        None, "--root", "-r",
        help="Repository root directory (default: file directory).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """
    Returns structured context of a section: metadata, outgoing edges, incoming edges.
    """
    import json as json_mod
    from mdgraph.index import index_repository

    file_path_str, section_id = _split_uri(uri)
    file_path = Path(file_path_str).resolve()
    repo_root = root.resolve() if root else file_path.parent

    try:
        graph = index_repository(repo_root)
    except ParseError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    abs_uri = str(file_path) + "#" + section_id

    if abs_uri not in graph.index.sections:
        typer.echo(f"Error: URI '{abs_uri}' not found in index.", err=True)
        raise typer.Exit(code=1)

    section = graph.index.sections[abs_uri]

    outgoing = [
        {"uri": t, "type": _edge_type(abs_uri, t, section)}
        for t in sorted(graph.outgoing_edges.get(abs_uri, set()))
    ]
    incoming = [
        {"uri": s, "type": "incoming"}
        for s in sorted(graph.incoming_edges.get(abs_uri, set()))
    ]

    if json_output:
        typer.echo(json_mod.dumps({
            "uri": abs_uri,
            "metadata": section.metadata,
            "outgoing": outgoing,
            "incoming": incoming,
        }, ensure_ascii=False, indent=2))
    else:
        typer.echo(f"URI: {abs_uri}")
        typer.echo(f"Metadata: {section.metadata}")
        if outgoing:
            typer.echo("Outgoing:")
            for e in outgoing:
                typer.echo(f"  [{e['type']}] {e['uri']}")
        if incoming:
            typer.echo("Incoming:")
            for e in incoming:
                typer.echo(f"  [ref] {e['uri']}")


def _edge_type(src_uri: str, target_uri: str, section) -> str:
    for d in section.directives:
        if d.target_uri == target_uri:
            return d.type
    return "ref"


# ---------------------------------------------------------------------------
# backlinks (B-017)
# ---------------------------------------------------------------------------

@app.command()
def backlinks(
    uri: str = typer.Argument(..., help="Section URI in the format file.md#id"),
    root: Optional[Path] = typer.Option(
        None, "--root", "-r",
        help="Repository root directory (default: file directory).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """
    Lists all sections that reference this URI (incoming edges).
    """
    import json as json_mod
    from mdgraph.index import index_repository

    file_path_str, section_id = _split_uri(uri)
    file_path = Path(file_path_str).resolve()
    repo_root = root.resolve() if root else file_path.parent

    try:
        graph = index_repository(repo_root)
    except ParseError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    abs_uri = str(file_path) + "#" + section_id

    if abs_uri not in graph.index.sections:
        typer.echo(f"Error: URI '{abs_uri}' not found in index.", err=True)
        raise typer.Exit(code=1)

    bl = sorted(graph.incoming_edges.get(abs_uri, set()))
    result = [{"uri": s, "type": _edge_type(s, abs_uri, graph.index.sections.get(s))} for s in bl]

    if json_output:
        typer.echo(json_mod.dumps({"uri": abs_uri, "backlinks": result}, ensure_ascii=False, indent=2))
    else:
        if not result:
            typer.echo(f"No backlinks found for '{abs_uri}'.")
        else:
            typer.echo(f"Backlinks for '{abs_uri}':")
            for e in result:
                typer.echo(f"  [{e['type']}] {e['uri']}")


# ---------------------------------------------------------------------------
# search (B-018)
# ---------------------------------------------------------------------------

@app.command()
def search(
    predicate: str = typer.Argument(..., help="Predicate: key=value, key~=value, or tag:value"),
    root: Path = typer.Option(
        ..., "--root", "-r",
        help="Repository root directory.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """
    Searches sections by metadata predicate. Supports key=value, key~=value, tag:value.
    """
    import json as json_mod
    import re
    from mdgraph.index import index_repository

    try:
        graph = index_repository(root.resolve())
    except ParseError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    # Parse predicate
    tag_match = re.match(r"^tag:(.+)$", predicate)
    exact_match = re.match(r"^([^~=]+)=(.+)$", predicate)
    substring_match = re.match(r"^([^~=]+)~=(.+)$", predicate)

    def _matches(metadata: dict) -> bool:
        if tag_match:
            tag_val = tag_match.group(1)
            tags = metadata.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            return tag_val in tags
        if substring_match:
            key, val = substring_match.group(1), substring_match.group(2)
            return val.lower() in str(metadata.get(key, "")).lower()
        if exact_match:
            key, val = exact_match.group(1), exact_match.group(2)
            return str(metadata.get(key, "")) == val
        return False

    results = [
        {"uri": uri, "metadata": section.metadata}
        for uri, section in graph.index.sections.items()
        if _matches(section.metadata)
    ]
    results.sort(key=lambda r: r["uri"])

    if json_output:
        typer.echo(json_mod.dumps({"predicate": predicate, "results": results}, ensure_ascii=False, indent=2))
    else:
        if not results:
            typer.echo(f"No sections found matching '{predicate}'.")
        else:
            typer.echo(f"Found {len(results)} section(s) matching '{predicate}':")
            for r in results:
                typer.echo(f"  {r['uri']}")


# ---------------------------------------------------------------------------
# impact (B-019)
# ---------------------------------------------------------------------------

@app.command()
def impact(
    uri: str = typer.Argument(..., help="Section URI in the format file.md#id"),
    root: Optional[Path] = typer.Option(
        None, "--root", "-r",
        help="Repository root directory (default: file directory).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """
    Returns all sections that depend (directly or indirectly) on this URI via reverse BFS.
    """
    import json as json_mod
    from collections import deque
    from mdgraph.index import index_repository

    file_path_str, section_id = _split_uri(uri)
    file_path = Path(file_path_str).resolve()
    repo_root = root.resolve() if root else file_path.parent

    try:
        graph = index_repository(repo_root)
    except ParseError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    abs_uri = str(file_path) + "#" + section_id

    if abs_uri not in graph.index.sections:
        typer.echo(f"Error: URI '{abs_uri}' not found in index.", err=True)
        raise typer.Exit(code=1)

    # BFS on reverse graph (incoming edges)
    direct = sorted(graph.incoming_edges.get(abs_uri, set()))
    visited = set(direct) | {abs_uri}
    queue = deque(direct)
    indirect: list[str] = []

    while queue:
        current = queue.popleft()
        for parent in graph.incoming_edges.get(current, set()):
            if parent not in visited:
                visited.add(parent)
                indirect.append(parent)
                queue.append(parent)

    indirect.sort()

    direct_out = [{"uri": u} for u in direct]
    indirect_out = [{"uri": u} for u in indirect]

    if json_output:
        typer.echo(json_mod.dumps({
            "uri": abs_uri,
            "direct": direct_out,
            "indirect": indirect_out,
        }, ensure_ascii=False, indent=2))
    else:
        if not direct and not indirect:
            typer.echo(f"No sections depend on '{abs_uri}'.")
        else:
            if direct:
                typer.echo(f"Direct dependents of '{abs_uri}':")
                for e in direct_out:
                    typer.echo(f"  {e['uri']}")
            if indirect:
                typer.echo(f"Indirect dependents:")
                for e in indirect_out:
                    typer.echo(f"  {e['uri']}")
