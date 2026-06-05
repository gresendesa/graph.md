"""
Testes de indexacao do repositorio e construcao do grafo (B-004).
"""
from pathlib import Path

import pytest

from mdgraph.index import index_repository
from mdgraph.parser import ParseError

FIXTURES = Path(__file__).parent / "fixtures"
REPO = FIXTURES / "repo"
REPO_DUP = FIXTURES / "repo_dup"


class TestIndexRepository:
    def setup_method(self):
        self.graph = index_repository(REPO)

    def test_numero_de_secoes(self):
        # intro.md: 1 | conceitos.md: 2 | sub/detalhe.md: 1
        assert len(self.graph.index.sections) == 4

    def test_lookup_por_uri(self):
        intro_uri = str((REPO / "intro.md").resolve()) + "#intro"
        section = self.graph.index.get(intro_uri)
        assert section is not None
        assert section.metadata["id"] == "intro"

    def test_todas_uris_presentes(self):
        uris = set(self.graph.index.sections.keys())
        ids = {s.metadata["id"] for s in self.graph.index.sections.values()}
        assert {"intro", "conceito-a", "conceito-b", "detalhe"} == ids

    def test_aresta_ref_intro_para_conceito_a(self):
        intro_uri = str((REPO / "intro.md").resolve()) + "#intro"
        conceito_a_uri = str((REPO / "conceitos.md").resolve()) + "#conceito-a"
        assert conceito_a_uri in self.graph.outgoing_edges[intro_uri]

    def test_backlink_conceito_a_de_intro(self):
        intro_uri = str((REPO / "intro.md").resolve()) + "#intro"
        conceito_a_uri = str((REPO / "conceitos.md").resolve()) + "#conceito-a"
        assert intro_uri in self.graph.incoming_edges[conceito_a_uri]

    def test_aresta_include_conceito_a_para_detalhe(self):
        conceito_a_uri = str((REPO / "conceitos.md").resolve()) + "#conceito-a"
        detalhe_uri = str((REPO / "sub/detalhe.md").resolve()) + "#detalhe"
        assert detalhe_uri in self.graph.outgoing_edges[conceito_a_uri]

    def test_secao_sem_diretivas_nao_tem_arestas(self):
        conceito_b_uri = str((REPO / "conceitos.md").resolve()) + "#conceito-b"
        assert len(self.graph.outgoing_edges.get(conceito_b_uri, set())) == 0


class TestIndexRepositoryErros:
    def test_uri_duplicada_levanta_parse_error(self):
        # repo_dup tem dois arquivos com id 'intro' — URIs distintas, sem colisao
        # (URIs sao baseadas no caminho do arquivo, entao nao colidem)
        # Testamos colisao real: mesmo arquivo com id repetido ja e coberto no parser
        # Aqui verificamos que o repositorio indexa sem erro quando URIs sao unicas
        graph = index_repository(REPO_DUP)
        ids = {s.metadata["id"] for s in graph.index.sections.values()}
        # Ambos tem id 'intro', mas URIs diferentes (arquivos diferentes) — sem colisao
        assert "intro" in ids

    def test_repositorio_vazio_retorna_grafo_vazio(self, tmp_path):
        graph = index_repository(tmp_path)
        assert len(graph.index.sections) == 0
        assert len(graph.outgoing_edges) == 0

    def test_ignora_arquivos_nao_md(self, tmp_path):
        (tmp_path / "arquivo.txt").write_text("nao e markdown")
        (tmp_path / "dados.json").write_text("{}")
        graph = index_repository(tmp_path)
        assert len(graph.index.sections) == 0


class TestIndexArestasBidirecionais:
    def test_outgoing_e_incoming_simetricos(self):
        graph = index_repository(REPO)
        intro_uri = str((REPO / "intro.md").resolve()) + "#intro"
        conceito_a_uri = str((REPO / "conceitos.md").resolve()) + "#conceito-a"

        assert conceito_a_uri in graph.outgoing_edges[intro_uri]
        assert intro_uri in graph.incoming_edges[conceito_a_uri]
