"""
Cache persistente do SectionIndex (spec section 7).

Serializa o indice em <root>/.mdgraph/index.json e, em execucoes subsequentes,
reprocessa apenas os arquivos cujo hash SHA-256 tenha mudado.
Arquivos removidos tem suas secoes expurgadas automaticamente.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

# Versao do esquema do cache; mudar quando o formato mudar de forma incompativel
_CACHE_VERSION = 1
_CACHE_DIR = ".mdgraph"
_CACHE_FILE = "index.json"


# ---------------------------------------------------------------------------
# Hash de arquivo
# ---------------------------------------------------------------------------

def file_hash(path: Path) -> str:
    """Retorna o SHA-256 do conteudo do arquivo."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Leitura e escrita do cache
# ---------------------------------------------------------------------------

def _cache_path(root: Path) -> Path:
    return root / _CACHE_DIR / _CACHE_FILE


def load_cache(root: Path) -> Optional[dict]:
    """
    Carrega o cache do disco. Retorna None se nao existir ou for invalido.
    """
    cp = _cache_path(root)
    if not cp.exists():
        return None
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
        if data.get("version") != _CACHE_VERSION:
            return None
        return data
    except (json.JSONDecodeError, KeyError):
        return None


def save_cache(root: Path, file_hashes: Dict[str, str], sections_data: list) -> None:
    """
    Persiste o cache no disco.

    file_hashes: {str(abs_path): sha256}
    sections_data: lista de dicts serializaveis das ParsedSections
    """
    cp = _cache_path(root)
    cp.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _CACHE_VERSION,
        "file_hashes": file_hashes,
        "sections": sections_data,
    }
    cp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Serializacao / desserializacao de ParsedSection
# ---------------------------------------------------------------------------

def serialize_section(section) -> dict:
    """Converte ParsedSection em dict JSON-serializavel."""
    return {
        "uri": section.uri,
        "file_path": section.file_path,
        "metadata": section.metadata,
        "directives": [{"type": d.type, "target_uri": d.target_uri}
                       for d in section.directives],
        "raw": {
            "heading_level": section.raw.heading_level,
            "heading_text": section.raw.heading_text,
            "token_start": section.raw.token_start,
            "token_end": section.raw.token_end,
            "source_start_line": section.raw.source_start_line,
            "source_end_line": section.raw.source_end_line,
        },
    }


def deserialize_section(data: dict):
    """Reconstroi ParsedSection a partir de dict do cache."""
    from mdbind.models import Directive, ParsedSection, RawSection

    raw = RawSection(**data["raw"])
    directives = [Directive(type=d["type"], target_uri=d["target_uri"])
                  for d in data.get("directives", [])]
    return ParsedSection(
        raw=raw,
        uri=data["uri"],
        file_path=data["file_path"],
        metadata=data["metadata"],
        directives=directives,
    )


# ---------------------------------------------------------------------------
# Logica incremental
# ---------------------------------------------------------------------------

def build_index_with_cache(
    root: Path,
    md_files: list[Path],
    no_cache: bool = False,
) -> tuple[list, Dict[str, str]]:
    """
    Retorna (sections_list, file_hashes) usando cache quando possivel.

    sections_list: lista de ParsedSection prontas para popular o SectionIndex
    file_hashes: hashes atuais de todos os arquivos processados
    """
    from mdbind.parser import parse_file

    current_hashes: Dict[str, str] = {str(f): file_hash(f) for f in md_files}

    # Sem cache ou --no-cache: reprocessar tudo
    cached = None if no_cache else load_cache(root)

    if cached is None:
        sections = _parse_all(md_files, parse_file)
        return sections, current_hashes

    cached_hashes: Dict[str, str] = cached.get("file_hashes", {})
    cached_sections_data: list = cached.get("sections", [])

    # Agrupar secoes cacheadas por arquivo
    cached_by_file: Dict[str, list] = {}
    for s_data in cached_sections_data:
        fp = s_data["file_path"]
        cached_by_file.setdefault(fp, []).append(s_data)

    sections: list = []
    current_file_strs = {str(f) for f in md_files}

    for f in md_files:
        fs = str(f)
        if cached_hashes.get(fs) == current_hashes[fs]:
            # Cache hit: restaurar secoes do disco
            for s_data in cached_by_file.get(fs, []):
                sections.append(deserialize_section(s_data))
        else:
            # Cache miss: reparsar arquivo modificado
            sections.extend(parse_file(f))

    # Arquivos removidos: secoes de arquivos que nao existem mais sao ignoradas
    # (nao adicionamos ao sections, portanto nao aparecem no indice)

    return sections, current_hashes


def _parse_all(md_files: list[Path], parse_file) -> list:
    sections = []
    for f in md_files:
        sections.extend(parse_file(f))
    return sections
