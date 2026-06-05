"""
Etapa 5 do pipeline: indexacao do repositorio e construcao do SectionGraph.

index_repository(root_path) -> SectionGraph
  - Descobre recursivamente todos os .md no diretorio raiz
  - Executa o pipeline parser.parse_file em cada arquivo (com cache incremental)
  - Registra secoes no SectionIndex
  - Constroi arestas bidirecionais no SectionGraph
"""
from __future__ import annotations

from pathlib import Path

from mdgraph.cache import build_index_with_cache, save_cache, serialize_section
from mdgraph.models import SectionGraph, SectionIndex
from mdgraph.parser import ParseError


def index_repository(
    root_path: str | Path,
    *,
    no_cache: bool = False,
    persist_cache: bool = False,
) -> SectionGraph:
    """
    Varre recursivamente root_path buscando arquivos .md,
    parseia cada um e monta o SectionGraph completo em memoria.

    Parametros:
      no_cache: ignorar cache existente e reprocessar tudo
      persist_cache: gravar cache em .mdgraph/index.json apos indexar

    Raises ParseError se houver URIs duplicadas.
    """
    root = Path(root_path).resolve()
    md_files = sorted(root.rglob("*.md"))

    sections, file_hashes = build_index_with_cache(root, md_files, no_cache=no_cache)

    index = SectionIndex()
    graph = SectionGraph(index=index)

    for section in sections:
        try:
            index.add(section)
        except ValueError as exc:
            raise ParseError(str(exc)) from exc

        for directive in section.directives:
            if directive.type in ("ref", "include"):
                graph.add_edge(section.uri, directive.target_uri)

    if persist_cache:
        sections_data = [serialize_section(s) for s in index.sections.values()]
        save_cache(root, file_hashes, sections_data)

    return graph
