from pathlib import Path

import pytest

from mdgraph.parser import ParseError, parse_file, parse_text

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# parse_text basico
# ---------------------------------------------------------------------------

class TestParseTextSimples:
    def test_secao_simples(self):
        sections = parse_file(FIXTURES / "simple.md")
        assert len(sections) == 1
        s = sections[0]
        assert s.metadata["id"] == "secao-simples"
        assert s.uri == f"{FIXTURES / 'simple.md'}#secao-simples"
        assert s.raw.heading_level == 1
        assert s.raw.heading_text == "Secao Simples"

    def test_source_lines_simples(self):
        sections = parse_file(FIXTURES / "simple.md")
        raw = sections[0].raw
        # heading esta na linha 1
        assert raw.source_start_line == 1
        # fim do arquivo: deve ser >= source_start_line
        assert raw.source_end_line >= raw.source_start_line


# ---------------------------------------------------------------------------
# Arquivo aninhado: 4 secoes
# ---------------------------------------------------------------------------

class TestNestedSections:
    def setup_method(self):
        self.sections = parse_file(FIXTURES / "nested.md")

    def test_quantidade(self):
        assert len(self.sections) == 4

    def test_ids(self):
        ids = [s.metadata["id"] for s in self.sections]
        assert ids == ["capitulo-um", "subsecao-a", "subsecao-b", "capitulo-dois"]

    def test_niveis(self):
        levels = [s.raw.heading_level for s in self.sections]
        assert levels == [1, 2, 2, 1]

    def test_capitulo_um_encerra_antes_de_capitulo_dois(self):
        cap_um = next(s for s in self.sections if s.metadata["id"] == "capitulo-um")
        cap_dois = next(s for s in self.sections if s.metadata["id"] == "capitulo-dois")
        assert cap_um.raw.source_end_line < cap_dois.raw.source_start_line

    def test_subsecao_dentro_de_capitulo(self):
        cap_um = next(s for s in self.sections if s.metadata["id"] == "capitulo-um")
        sub_a = next(s for s in self.sections if s.metadata["id"] == "subsecao-a")
        # subsecao comeca depois do inicio do capitulo
        assert sub_a.raw.source_start_line > cap_um.raw.source_start_line


# ---------------------------------------------------------------------------
# Secao sem payload: ignorada silenciosamente
# ---------------------------------------------------------------------------

class TestSemPayload:
    def test_retorna_lista_vazia(self):
        sections = parse_file(FIXTURES / "no_payload.md")
        assert sections == []


# ---------------------------------------------------------------------------
# Validacoes de erro
# ---------------------------------------------------------------------------

class TestValidacoes:
    def test_id_ausente_levanta_parse_error(self):
        with pytest.raises(ParseError, match="campo 'id' ausente"):
            parse_file(FIXTURES / "missing_id.md")

    def test_payload_nao_primeiro_bloco(self):
        with pytest.raises(ParseError, match="payload nao e o primeiro bloco"):
            parse_file(FIXTURES / "payload_not_first.md")

    def test_payload_duplicado(self):
        with pytest.raises(ParseError, match="bloco section duplicado"):
            parse_file(FIXTURES / "duplicate_payload.md")

    def test_id_duplicado_no_arquivo(self):
        with pytest.raises(ParseError, match="id duplicado"):
            parse_file(FIXTURES / "duplicate_id.md")


# ---------------------------------------------------------------------------
# parse_text inline
# ---------------------------------------------------------------------------

class TestParseTextInline:
    def test_campos_livres_preservados(self):
        md = """# Secao

```section
id: minha-secao
owner: gresendesa
tags: [a, b]
```
"""
        sections = parse_text(md, file_path="mem.md")
        assert len(sections) == 1
        meta = sections[0].metadata
        assert meta["owner"] == "gresendesa"
        assert meta["tags"] == ["a", "b"]

    def test_uri_formato_correto(self):
        md = """# X\n\n```section\nid: x\n```\n"""
        sections = parse_text(md, file_path="pasta/arq.md")
        assert sections[0].uri == "pasta/arq.md#x"
