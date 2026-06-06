import pytest
from pydantic import ValidationError

from mdbind.models import (
    Directive,
    ParsedSection,
    RawSection,
    SectionGraph,
    SectionIndex,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_raw(level: int = 1, text: str = "Titulo") -> RawSection:
    return RawSection(
        heading_level=level,
        heading_text=text,
        token_start=0,
        token_end=10,
        source_start_line=1,
        source_end_line=5,
    )


def make_parsed(uri: str = "doc.md#secao", section_id: str = "secao") -> ParsedSection:
    return ParsedSection(
        raw=make_raw(),
        uri=uri,
        file_path="doc.md",
        metadata={"id": section_id, "title": "Secao de Teste"},
    )


# ---------------------------------------------------------------------------
# RawSection
# ---------------------------------------------------------------------------

class TestRawSection:
    def test_instanciacao_ok(self):
        raw = make_raw()
        assert raw.heading_level == 1
        assert raw.token_start == 0

    def test_campos_obrigatorios(self):
        with pytest.raises(ValidationError):
            RawSection(heading_text="X", token_start=0, token_end=1,
                       source_start_line=1, source_end_line=2)  # falta heading_level


# ---------------------------------------------------------------------------
# Directive
# ---------------------------------------------------------------------------

class TestDirective:
    def test_ref(self):
        d = Directive(type="ref", target_uri="outro.md#id")
        assert d.type == "ref"

    def test_include(self):
        d = Directive(type="include", target_uri="outro.md#id")
        assert d.type == "include"

    def test_query(self):
        d = Directive(type="query", target_uri="outro.md#id")
        assert d.type == "query"

    def test_tipo_invalido(self):
        with pytest.raises(ValidationError):
            Directive(type="embed", target_uri="outro.md#id")


# ---------------------------------------------------------------------------
# ParsedSection
# ---------------------------------------------------------------------------

class TestParsedSection:
    def test_instanciacao_ok(self):
        ps = make_parsed()
        assert ps.uri == "doc.md#secao"
        assert ps.metadata["id"] == "secao"

    def test_sem_id_levanta_erro(self):
        with pytest.raises(ValidationError, match="campo 'id' ausente"):
            ParsedSection(
                raw=make_raw(),
                uri="doc.md#secao",
                file_path="doc.md",
                metadata={"title": "Sem ID"},
            )

    def test_directives_default_vazio(self):
        ps = make_parsed()
        assert ps.directives == []

    def test_com_diretivas(self):
        ps = ParsedSection(
            raw=make_raw(),
            uri="doc.md#secao",
            file_path="doc.md",
            metadata={"id": "secao"},
            directives=[
                Directive(type="ref", target_uri="outro.md#x"),
                Directive(type="include", target_uri="outro.md#y"),
            ],
        )
        assert len(ps.directives) == 2
        assert ps.directives[0].type == "ref"


# ---------------------------------------------------------------------------
# SectionIndex
# ---------------------------------------------------------------------------

class TestSectionIndex:
    def test_add_e_get(self):
        idx = SectionIndex()
        ps = make_parsed()
        idx.add(ps)
        assert idx.get("doc.md#secao") is ps

    def test_uri_inexistente_retorna_none(self):
        idx = SectionIndex()
        assert idx.get("nao-existe.md#id") is None

    def test_uri_duplicada_levanta_erro(self):
        idx = SectionIndex()
        idx.add(make_parsed())
        with pytest.raises(ValueError, match="URI duplicada"):
            idx.add(make_parsed())


# ---------------------------------------------------------------------------
# SectionGraph
# ---------------------------------------------------------------------------

class TestSectionGraph:
    def test_add_edge_outgoing(self):
        g = SectionGraph()
        g.add_edge("a.md#x", "b.md#y")
        assert "b.md#y" in g.outgoing_edges["a.md#x"]

    def test_add_edge_incoming(self):
        g = SectionGraph()
        g.add_edge("a.md#x", "b.md#y")
        assert "a.md#x" in g.incoming_edges["b.md#y"]

    def test_multiplas_arestas(self):
        g = SectionGraph()
        g.add_edge("a.md#x", "b.md#y")
        g.add_edge("a.md#x", "c.md#z")
        assert len(g.outgoing_edges["a.md#x"]) == 2

    def test_backlink_multiplos_origins(self):
        g = SectionGraph()
        g.add_edge("a.md#x", "d.md#w")
        g.add_edge("b.md#y", "d.md#w")
        assert len(g.incoming_edges["d.md#w"]) == 2
