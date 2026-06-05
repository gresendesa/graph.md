"""
Etapa 4 do pipeline: tokenizacao de diretivas.

Varre os tokens de conteudo de uma ParsedSection ja delimitada e converte
marcacoes semanticas (@ref, @include, @query) em objetos Directive tipados,
resolvendo URIs relativas ao arquivo de origem.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from mdgraph.models import Directive, ParsedSection

# Regex que captura @tipo(uri) — uri pode conter qualquer char exceto ')'
_DIRECTIVE_RE = re.compile(r"@(ref|include|query)\(([^)]+)\)")


def _resolve_uri(target: str, source_file_path: str) -> str:
    """
    Resolve um target URI relativo ao diretorio do arquivo de origem.

    Se o target nao tiver componente de caminho (ex: apenas "#id"), retorna
    como esta. Se for absoluto ou ja normalizado, retorna normalizado.
    Fragmentos (#id) sao preservados.
    """
    if not target:
        return target

    # Separar caminho e fragmento
    if "#" in target:
        path_part, fragment = target.split("#", 1)
        fragment = "#" + fragment
    else:
        path_part, fragment = target, ""

    if not path_part:
        # Referencia ao proprio arquivo: "#id"
        return source_file_path + fragment

    p = Path(path_part)
    if p.is_absolute():
        return str(p) + fragment

    # Resolver relativo ao diretorio do arquivo de origem
    source_dir = Path(source_file_path).parent
    resolved = (source_dir / p).resolve()
    return str(resolved) + fragment


def extract_directives(tokens: list, source_file_path: str) -> List[Directive]:
    """
    Varre tokens buscando texto inline que contenha diretivas @tipo(uri).
    Retorna a lista de Directive na ordem de ocorrencia.

    Em markdown-it-py, tokens `inline` possuem tanto `content` (texto bruto)
    quanto `children` (sub-tokens ja parseados). Varrer ambos duplicaria os
    resultados; por isso priorizamos `children` quando presentes.
    """
    directives: List[Directive] = []

    for tok in tokens:
        if tok.type != "inline":
            continue
        if tok.children:
            for child in tok.children:
                if child.type in ("text", "code_inline") and child.content:
                    _scan_text(child.content, source_file_path, directives)
        elif tok.content:
            _scan_text(tok.content, source_file_path, directives)

    return directives


def _scan_text(text: str, source_file_path: str, out: List[Directive]) -> None:
    for match in _DIRECTIVE_RE.finditer(text):
        dtype = match.group(1)  # "ref" | "include" | "query"
        raw_uri = match.group(2).strip()
        resolved = _resolve_uri(raw_uri, source_file_path)
        out.append(Directive(type=dtype, target_uri=resolved))  # type: ignore[arg-type]


def bind_directives(section: ParsedSection, tokens: list) -> ParsedSection:
    """
    Retorna uma nova ParsedSection com o campo directives populado.
    Varre apenas os tokens internos da secao (excluindo sub-secoes).
    """
    # Tokens internos: apos heading_open, inline, heading_close; para antes do proximo heading
    all_inner = tokens[section.raw.token_start + 3: section.raw.token_end + 1]
    inner: list = []
    for tok in all_inner:
        if tok.type == "heading_open":
            break
        inner.append(tok)

    directives = extract_directives(inner, section.file_path)

    return section.model_copy(update={"directives": directives})
