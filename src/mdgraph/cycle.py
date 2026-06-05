"""
Deteccao e resolucao de ciclos durante a materializacao (spec section 5).

O digrafo pode conter ciclos nativamente. Durante o compose, o motor rastreia
o caminho de execucao atual P (stack de URIs). Se uma aresta de inclusao (x, y)
for avaliada e y ∈ P, o ciclo e detectado e a aresta e rompida silenciosamente.

O SectionGraph original NAO e modificado; apenas a materializacao e afetada.
"""
from __future__ import annotations

from typing import FrozenSet


def would_cycle(uri: str, execution_path: FrozenSet[str]) -> bool:
    """
    Retorna True se incluir `uri` no caminho atual criaria um ciclo.
    """
    return uri in execution_path


def enter_node(uri: str, execution_path: FrozenSet[str]) -> FrozenSet[str]:
    """Retorna um novo caminho com `uri` adicionado."""
    return execution_path | {uri}
