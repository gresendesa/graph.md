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

from mdbind.models import Directive, ParsedSection

# Regex que captura [@tipo: label](uri) ou [@tipo](uri)
# Grupo 1: tipo (ref|include|query)
# Grupo 2: label opcional (pode ser vazio ou ausente)
# Grupo 3: uri de destino
_DIRECTIVE_RE = re.compile(r"\[@(ref|include|query)(?::\s*([^\]]*))?\]\(([^)]+)\)")


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


# Regex para o texto do link: @tipo ou @tipo: label
_LINK_TEXT_RE = re.compile(r"^@(ref|include|query)(?::\s*(.*))?$")


def extract_directives(tokens: list, source_file_path: str) -> List[Directive]:
    """
    Varre tokens buscando diretivas na sintaxe de link Markdown:
      [@tipo: label](uri)  ou  [@tipo](uri)

    Em markdown-it-py, esse padrao e tokenizado como:
      link_open (attrs: [["href", uri]])
      text      (content: "@tipo: label")
      link_close

    A extracao examina cada link_open dentro de tokens `inline` e verifica
    se o texto filho corresponde ao padrao de diretiva.
    """
    directives: List[Directive] = []

    for tok in tokens:
        if tok.type != "inline" or not tok.children:
            continue
        children = tok.children
        i = 0
        while i < len(children):
            child = children[i]
            if child.type == "link_open":
                attrs = child.attrs or {}
                href = attrs.get("href", "") if isinstance(attrs, dict) else ""
                # Proximo filho deve ser o texto do link
                if i + 1 < len(children) and children[i + 1].type == "text":
                    link_text = children[i + 1].content.strip()
                    m = _LINK_TEXT_RE.match(link_text)
                    if m and href:
                        dtype = m.group(1)
                        raw_label = m.group(2)
                        label = raw_label.strip() if raw_label else None
                        resolved = _resolve_uri(href.strip(), source_file_path)
                        directives.append(
                            Directive(type=dtype, target_uri=resolved, label=label)  # type: ignore[arg-type]
                        )
            i += 1

    return directives


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
