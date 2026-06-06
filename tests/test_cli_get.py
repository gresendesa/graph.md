"""
Testes do comando CLI 'mdgraph get' (B-005, B-025).
"""
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mdgraph.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
runner = CliRunner()


class TestGetComando:
    def _uri(self, filename: str, section_id: str) -> str:
        return str((FIXTURES / filename).resolve()) + "#" + section_id

    def test_get_retorna_heading(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha")])
        assert result.exit_code == 0
        assert "# Secao Alpha" in result.output

    def test_get_preserva_formatacao(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha")])
        assert result.exit_code == 0
        assert "    bloco indentado preservado" in result.output

    def test_get_preserva_comentario_html(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha")])
        assert result.exit_code == 0
        assert "<!-- comentario html -->" in result.output

    def test_get_inclui_subsecao_hierarquica(self):
        # get usa linhas brutas do RawSection; h1 engloba todos os h2 internos
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha")])
        assert result.exit_code == 0
        assert "## Sub Alpha" in result.output

    def test_get_subsecao(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "sub-alpha")])
        assert result.exit_code == 0
        assert "## Sub Alpha" in result.output

    def test_get_campos_livres_no_bloco(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha")])
        assert result.exit_code == 0
        assert "owner: gresendesa" in result.output


class TestGetErros:
    def _uri(self, filename: str, section_id: str) -> str:
        return str((FIXTURES / filename).resolve()) + "#" + section_id

    def test_uri_sem_fragmento_retorna_exit_1(self):
        result = runner.invoke(app, ["get", str(FIXTURES / "simple.md")])
        assert result.exit_code == 1

    def test_arquivo_inexistente_retorna_exit_1(self):
        result = runner.invoke(app, ["get", "/nao/existe.md#id"])
        assert result.exit_code == 1

    def test_secao_inexistente_retorna_exit_1(self):
        result = runner.invoke(app, ["get", self._uri("simple.md", "nao-existe")])
        assert result.exit_code == 1

    def test_mensagem_de_erro_no_stderr(self):
        result = runner.invoke(app, ["get", "/nao/existe.md#id"])
        assert "Erro" in result.output or result.exit_code == 1


class TestGetJson:
    def _uri(self, filename: str, section_id: str) -> str:
        return str((FIXTURES / filename).resolve()) + "#" + section_id

    def test_get_json_exits_zero(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha"), "--json"])
        assert result.exit_code == 0

    def test_get_json_contains_uri(self):
        uri = self._uri("get_source.md", "alpha")
        result = runner.invoke(app, ["get", uri, "--json"])
        data = json.loads(result.output)
        assert data["uri"] == uri

    def test_get_json_contains_content(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha"), "--json"])
        data = json.loads(result.output)
        assert "# Secao Alpha" in data["content"]

    def test_get_json_schema_keys(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha"), "--json"])
        data = json.loads(result.output)
        assert "uri" in data
        assert "file_path" in data
        assert "source_start_line" in data
        assert "source_end_line" in data
        assert "content" in data

    def test_get_json_line_numbers_are_integers(self):
        result = runner.invoke(app, ["get", self._uri("get_source.md", "alpha"), "--json"])
        data = json.loads(result.output)
        assert isinstance(data["source_start_line"], int)
        assert isinstance(data["source_end_line"], int)
