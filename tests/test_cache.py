"""
Testes de cache persistente do indice (B-009).
"""
import shutil
from pathlib import Path

import pytest

from mdbind.cache import (
    deserialize_section,
    file_hash,
    load_cache,
    save_cache,
    serialize_section,
)
from mdbind.index import index_repository

FIXTURES = Path(__file__).parent / "fixtures"
REPO = FIXTURES / "repo"


# ---------------------------------------------------------------------------
# Utilitarios de cache
# ---------------------------------------------------------------------------

class TestFileHash:
    def test_mesmo_conteudo_mesmo_hash(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("conteudo")
        assert file_hash(f) == file_hash(f)

    def test_conteudos_diferentes_hashes_diferentes(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("conteudo A")
        f2.write_text("conteudo B")
        assert file_hash(f1) != file_hash(f2)


class TestLoadSaveCache:
    def test_save_cria_arquivo(self, tmp_path):
        save_cache(tmp_path, {"arq.md": "abc123"}, [])
        assert (tmp_path / ".mdgraph" / "index.json").exists()

    def test_load_retorna_none_se_inexistente(self, tmp_path):
        assert load_cache(tmp_path) is None

    def test_roundtrip_hashes(self, tmp_path):
        hashes = {"a.md": "hash1", "b.md": "hash2"}
        save_cache(tmp_path, hashes, [])
        cached = load_cache(tmp_path)
        assert cached["file_hashes"] == hashes

    def test_cache_invalido_retorna_none(self, tmp_path):
        cp = tmp_path / ".mdgraph" / "index.json"
        cp.parent.mkdir()
        cp.write_text("nao e json valido")
        assert load_cache(tmp_path) is None


class TestSerializeDeserialize:
    def test_roundtrip_section(self):
        graph = index_repository(REPO)
        for section in graph.index.sections.values():
            data = serialize_section(section)
            restored = deserialize_section(data)
            assert restored.uri == section.uri
            assert restored.metadata == section.metadata
            assert len(restored.directives) == len(section.directives)
            assert restored.raw.heading_level == section.raw.heading_level


# ---------------------------------------------------------------------------
# Comportamento incremental
# ---------------------------------------------------------------------------

class TestCacheIncremental:
    def test_primeira_execucao_cria_cache(self, tmp_path):
        # Copiar fixtures para tmp_path
        shutil.copytree(REPO, tmp_path / "repo")
        repo = tmp_path / "repo"

        index_repository(repo, persist_cache=True)
        assert (repo / ".mdgraph" / "index.json").exists()

    def test_cache_contem_hashes_corretos(self, tmp_path):
        shutil.copytree(REPO, tmp_path / "repo")
        repo = tmp_path / "repo"

        index_repository(repo, persist_cache=True)
        cached = load_cache(repo)
        md_files = list(repo.rglob("*.md"))
        for f in md_files:
            assert str(f) in cached["file_hashes"]

    def test_segunda_execucao_sem_mudancas_retorna_mesmo_resultado(self, tmp_path):
        shutil.copytree(REPO, tmp_path / "repo")
        repo = tmp_path / "repo"

        g1 = index_repository(repo, persist_cache=True)
        g2 = index_repository(repo, persist_cache=False)  # usa cache

        ids1 = {s.metadata["id"] for s in g1.index.sections.values()}
        ids2 = {s.metadata["id"] for s in g2.index.sections.values()}
        assert ids1 == ids2

    def test_modificar_arquivo_reparseia_apenas_ele(self, tmp_path):
        shutil.copytree(REPO, tmp_path / "repo")
        repo = tmp_path / "repo"

        # Primeira indexacao com cache
        index_repository(repo, persist_cache=True)
        cached_before = load_cache(repo)

        # Modificar um arquivo
        target = repo / "intro.md"
        original = target.read_text()
        target.write_text(original + "\n<!-- modificado -->\n")

        # Segunda indexacao
        index_repository(repo, persist_cache=True)
        cached_after = load_cache(repo)

        # Hash do arquivo modificado deve ter mudado
        assert cached_before["file_hashes"][str(target)] != cached_after["file_hashes"][str(target)]

    def test_remover_arquivo_expurga_secoes(self, tmp_path):
        shutil.copytree(REPO, tmp_path / "repo")
        repo = tmp_path / "repo"

        g1 = index_repository(repo, persist_cache=True)
        ids_before = {s.metadata["id"] for s in g1.index.sections.values()}
        assert "conceito-b" in ids_before

        # Remover arquivo com conceito-b
        (repo / "conceitos.md").unlink()

        g2 = index_repository(repo, no_cache=False, persist_cache=False)
        ids_after = {s.metadata["id"] for s in g2.index.sections.values()}
        assert "conceito-b" not in ids_after
        assert "conceito-a" not in ids_after

    def test_no_cache_ignora_cache_existente(self, tmp_path):
        shutil.copytree(REPO, tmp_path / "repo")
        repo = tmp_path / "repo"

        index_repository(repo, persist_cache=True)

        # Corromper o cache
        cp = repo / ".mdgraph" / "index.json"
        cp.write_text('{"version": 1, "file_hashes": {}, "sections": []}')

        # Com no_cache=True deve reprocessar tudo mesmo com cache corrompido/vazio
        g = index_repository(repo, no_cache=True)
        ids = {s.metadata["id"] for s in g.index.sections.values()}
        assert "intro" in ids
        assert "conceito-a" in ids
