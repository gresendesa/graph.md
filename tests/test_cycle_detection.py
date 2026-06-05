"""
Testes de deteccao e resolucao de ciclos (B-008).
"""
from pathlib import Path

import pytest

from mdgraph.composer import compose
from mdgraph.cycle import enter_node, would_cycle
from mdgraph.index import index_repository

FIXTURES = Path(__file__).parent / "fixtures"
CYCLES = FIXTURES / "cycles"


# ---------------------------------------------------------------------------
# Utilitarios de cycle.py
# ---------------------------------------------------------------------------

class TestCycleUtils:
    def test_would_cycle_false_quando_ausente(self):
        path = frozenset({"a", "b"})
        assert would_cycle("c", path) is False

    def test_would_cycle_true_quando_presente(self):
        path = frozenset({"a", "b", "c"})
        assert would_cycle("c", path) is True

    def test_enter_node_adiciona_uri(self):
        path = frozenset({"a"})
        new_path = enter_node("b", path)
        assert "b" in new_path
        assert "a" in new_path

    def test_enter_node_nao_muta_original(self):
        path = frozenset({"a"})
        enter_node("b", path)
        assert "b" not in path


# ---------------------------------------------------------------------------
# Ciclo A <-> B
# ---------------------------------------------------------------------------

class TestCicloAB:
    def _graph(self):
        return index_repository(CYCLES)

    def test_compose_nao_lanca_erro(self):
        graph = self._graph()
        a_uri = str((CYCLES / "cycle_a.md").resolve()) + "#no-a"
        warnings: list[str] = []
        result = compose(a_uri, graph, warnings=warnings)
        assert isinstance(result, str)

    def test_compose_termina_sem_loop(self):
        graph = self._graph()
        a_uri = str((CYCLES / "cycle_a.md").resolve()) + "#no-a"
        # Se houver loop infinito, o teste vai timeout; chegando aqui, passou
        result = compose(a_uri, graph)
        assert "Conteudo de A" in result

    def test_ciclo_detectado_emite_warning(self):
        graph = self._graph()
        a_uri = str((CYCLES / "cycle_a.md").resolve()) + "#no-a"
        warnings: list[str] = []
        compose(a_uri, graph, warnings=warnings)
        assert any("Ciclo" in w for w in warnings)

    def test_grafo_original_nao_mutado(self):
        graph = self._graph()
        a_uri = str((CYCLES / "cycle_a.md").resolve()) + "#no-a"
        b_uri = str((CYCLES / "cycle_b.md").resolve()) + "#no-b"
        edges_antes = set(graph.outgoing_edges.get(a_uri, set()))
        compose(a_uri, graph)
        assert graph.outgoing_edges.get(a_uri, set()) == edges_antes


# ---------------------------------------------------------------------------
# Auto-referencia A -> A
# ---------------------------------------------------------------------------

class TestAutoReferencia:
    def test_auto_ref_nao_loop(self):
        graph = index_repository(CYCLES)
        uri = str((CYCLES / "cycle_self.md").resolve()) + "#auto"
        warnings: list[str] = []
        result = compose(uri, graph, warnings=warnings)
        assert "Conteudo" in result
        assert any("Ciclo" in w for w in warnings)


# ---------------------------------------------------------------------------
# Ciclo longo D -> E -> F -> D
# ---------------------------------------------------------------------------

class TestCicloLongo:
    def test_ciclo_longo_nao_loop(self):
        graph = index_repository(CYCLES)
        d_uri = str((CYCLES / "cycle_d.md").resolve()) + "#no-d"
        warnings: list[str] = []
        result = compose(d_uri, graph, warnings=warnings)
        assert isinstance(result, str)
        assert any("Ciclo" in w for w in warnings)
