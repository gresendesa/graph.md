"""
Testes do comando CLI 'mdgraph tree' (B-006).
"""
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mdgraph.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
REPO = FIXTURES / "repo"
runner = CliRunner()


def _uri(repo_file: str, section_id: str) -> str:
    return str((REPO / repo_file).resolve()) + "#" + section_id


class TestTreeComando:
    def test_tree_raiz_aparece(self):
        result = runner.invoke(app, ["tree", _uri("intro.md", "intro"), "--root", str(REPO)])
        assert result.exit_code == 0
        assert "intro" in result.output

    def test_tree_mostra_dependencias(self):
        result = runner.invoke(app, ["tree", _uri("intro.md", "intro"), "--root", str(REPO)])
        assert result.exit_code == 0
        # intro referencia conceito-a
        assert "conceito-a" in result.output

    def test_tree_refs_mostra_backlinks(self):
        # conceito-a e referenciado por intro
        result = runner.invoke(
            app,
            ["tree", _uri("conceitos.md", "conceito-a"), "--root", str(REPO), "--refs"],
        )
        assert result.exit_code == 0
        assert "intro" in result.output

    def test_tree_sem_dependencias(self):
        # conceito-b nao tem outgoing edges
        result = runner.invoke(
            app,
            ["tree", _uri("conceitos.md", "conceito-b"), "--root", str(REPO)],
        )
        assert result.exit_code == 0
        assert "conceito-b" in result.output

    def test_tree_uri_inexistente_exit_1(self):
        result = runner.invoke(app, ["tree", _uri("intro.md", "nao-existe"), "--root", str(REPO)])
        assert result.exit_code == 1

    def test_tree_uri_sem_fragmento_exit_1(self):
        result = runner.invoke(app, ["tree", str(REPO / "intro.md"), "--root", str(REPO)])
        assert result.exit_code == 1
