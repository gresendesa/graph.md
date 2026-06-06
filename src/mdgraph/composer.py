"""
Materializacao semantica: motor de composicao documental (spec section 8.3).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import FrozenSet, List, Optional, Set

from mdgraph.cycle import enter_node, would_cycle
from mdgraph.directives import _resolve_uri
from mdgraph.models import SectionGraph

_PLACEHOLDER_TPL = "<!-- mdgraph:unresolved uri=\"{uri}\" -->"
_INCLUDE_RE = re.compile(r"^\[@include(?::[^\]]*)?\]\(([^)]+)\)\s*$")


def compose(
    root_uri: str,
    graph: SectionGraph,
    *,
    strict: bool = False,
    deduplicate: bool = False,
    warnings: Optional[List[str]] = None,
) -> str:
    if warnings is None:
        warnings = []

    seen: Set[str] = set()
    lines = _compose_node(
        root_uri, graph,
        heading_offset=0,
        execution_path=frozenset(),
        seen=seen,
        strict=strict,
        deduplicate=deduplicate,
        warnings=warnings,
    )
    return "\n".join(lines)


def _compose_node(
    uri: str,
    graph: SectionGraph,
    heading_offset: int,
    execution_path: FrozenSet[str],
    seen: Set[str],
    strict: bool,
    deduplicate: bool,
    warnings: List[str],
) -> List[str]:
    section = graph.index.get(uri)
    if section is None:
        msg = f"URI nao encontrada: '{uri}'"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        return [_PLACEHOLDER_TPL.format(uri=uri)]

    if deduplicate and uri in seen:
        return [f"@ref({uri})"]

    seen.add(uri)
    execution_path = enter_node(uri, execution_path)

    raw_lines = _raw_lines(section)
    result: List[str] = []

    for line in raw_lines:
        adjusted = _adjust_heading(line, heading_offset)
        m = _INCLUDE_RE.match(adjusted.strip())
        if m:
            # Resolver URI relativa ao arquivo de origem da secao
            raw_target = m.group(1).strip()
            resolved_target = _resolve_uri(raw_target, section.file_path)

            if would_cycle(resolved_target, execution_path):
                warnings.append(
                    f"Ciclo detectado: '{resolved_target}' ja esta no caminho "
                    f"de execucao. Aresta rompida."
                )
                continue  # rompe silenciosamente

            child_offset = heading_offset + section.raw.heading_level
            child_lines = _compose_node(
                resolved_target, graph,
                heading_offset=child_offset,
                execution_path=execution_path,
                seen=seen,
                strict=strict,
                deduplicate=deduplicate,
                warnings=warnings,
            )
            result.extend(child_lines)
        else:
            result.append(adjusted)

    return result


def _raw_lines(section) -> List[str]:
    path = Path(section.file_path)
    all_lines = path.read_text(encoding="utf-8").splitlines()
    start = section.raw.source_start_line - 1
    end = section.raw.source_end_line
    return all_lines[start:end]


def _adjust_heading(line: str, offset: int) -> str:
    if offset == 0:
        return line
    if line.startswith("#"):
        return "#" * offset + line
    return line

