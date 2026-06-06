from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Literal, Set

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Fase 2: Delimitacao Fisica
# ---------------------------------------------------------------------------

class RawSection(BaseModel):
    """Resolve apenas o escopo espacial da secao na AST e no arquivo fonte."""

    heading_level: int
    heading_text: str
    token_start: int
    token_end: int
    source_start_line: int
    source_end_line: int


# ---------------------------------------------------------------------------
# Fase 4: Semantica e Diretivas
# ---------------------------------------------------------------------------

class Directive(BaseModel):
    """Diretivas deixam de ser texto e se tornam nos logicos."""

    type: Literal["ref", "include", "query"]
    target_uri: str
    label: str | None = None


class ParsedSection(BaseModel):
    """Resolve o significado. Amarra o espaco fisico aos metadados e referencias."""

    raw: RawSection
    uri: str
    file_path: str
    # metadata deve conter obrigatoriamente a chave 'id'
    metadata: Dict[str, Any]
    directives: List[Directive] = Field(default_factory=list)

    @model_validator(mode="after")
    def _require_id_in_metadata(self) -> "ParsedSection":
        if "id" not in self.metadata:
            raise ValueError("secao sem payload obrigatorio: campo 'id' ausente em metadata")
        return self


# ---------------------------------------------------------------------------
# Fase 5: Indexacao e Grafo
# ---------------------------------------------------------------------------

class SectionIndex(BaseModel):
    """Repositorio de acesso em O(1) de secoes ja parseadas."""

    sections: Dict[str, ParsedSection] = Field(default_factory=dict)

    def add(self, section: ParsedSection) -> None:
        if section.uri in self.sections:
            raise ValueError(f"URI duplicada no indice: '{section.uri}'")
        self.sections[section.uri] = section

    def get(self, uri: str) -> ParsedSection | None:
        return self.sections.get(uri)


class SectionGraph(BaseModel):
    """Gestao topologica de dependencias (Backlinks suportados)."""

    index: SectionIndex = Field(default_factory=SectionIndex)
    outgoing_edges: Dict[str, Set[str]] = Field(
        default_factory=lambda: defaultdict(set)
    )
    incoming_edges: Dict[str, Set[str]] = Field(
        default_factory=lambda: defaultdict(set)
    )

    model_config = {"arbitrary_types_allowed": True}

    def add_edge(self, source_uri: str, target_uri: str) -> None:
        self.outgoing_edges[source_uri].add(target_uri)
        self.incoming_edges[target_uri].add(source_uri)
