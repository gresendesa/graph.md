# Especificação Técnica: Motor de Composição em Grafos Markdown (`mdgraph`)

## 1. Definições e Visão Geral Arquitetural

A ferramenta (`mdgraph`) é um motor CLI de *parsing* e composição documental. Ela trata repositórios de arquivos Markdown como um banco de dados em grafo, onde seções atuam como registros independentes que podem se referenciar e ser compostos dinamicamente.

A arquitetura baseia-se na separação estrita entre a **Física do Documento** (onde os elementos estão escritos) e a **Semântica do Documento** (o que eles significam e como se conectam).

* **Nó Primário (Seção):** O documento é composto primordialmente por seções. Uma seção é delimitada exclusivamente pela hierarquia de títulos (*headings*), independentemente de seu conteúdo.
* **URI de Seção:** O identificador global do nó no formato `caminho/do/arquivo.md#id-da-secao`. O caminho é sempre resolvido de forma relativa ao arquivo que faz a chamada.
* **Dificuldade de Representação:** O motor mantém duas representações simultâneas das seções:
* **Representação Documental:** Baseada em *offsets* exatos (linha/caractere) do arquivo original. Usada para extrações com 100% de fidelidade (preservando espaços, formatação e comentários).
* **Representação Semântica:** Baseada na Árvore de Sintaxe Abstrata (AST) e *Tokens*. Usada para análise estrutural, validação de grafos e composição de artefatos.



---

## 2. Pipeline de Processamento e Descoberta

Para evitar dependências frágeis e permitir validações ricas, o ciclo de vida do *parsing* obedece a um fluxo unidirecional rigoroso de cinco etapas:

**`Markdown ➔ AST ➔ RawSection ➔ ParsedSection ➔ Index ➔ Graph`**

1. **AST Generation:** O motor lê o texto Markdown e gera a lista plana de *tokens*.
2. **Section Discovery (`RawSection`):** O motor varre a AST buscando `heading_open`. Ao encontrar, marca o `token_start`. Ele continua varrendo até o final do documento ou até interceptar o primeiro `heading_open` subsequente de nível menor ou igual, marcando o `token_end`. Os *offsets* do arquivo fonte (linhas) também são capturados aqui.
3. **Metadata Binding (`ParsedSection`):** Com os limites da seção isolados, o motor analisa os *tokens* internos buscando o bloco de código marcado como `section`. O conteúdo é validado e extraído.
4. **Tokenization de Diretivas:** Dentro da seção recém-delimitada, as marcações semânticas (como `@include`) são convertidas de texto bruto para objetos tipados no motor.
5. **Grafo e Composição:** Os nós validados vão para o Índice e, em seguida, as arestas formam o Grafo para materialização.

---

## 3. Sintaxe e Validação do Payload

O bloco de metadados não define a seção; ele apenas confere identidade a uma seção já descoberta hierarquicamente.

* **Posição Estrita:** O bloco `section` deve ser obrigatoriamente o **primeiro bloco textual** logo após o *heading* que originou a seção. Se houver texto normal antes do bloco, o motor acusa erro de validação (*"payload não é o primeiro bloco"*).
* **Unicidade Interna:** O motor acusa erro se detectar mais de um bloco `section` dentro dos limites da mesma `RawSection`.
* **Esquema Obrigatório:** O campo `id` é estritamente obrigatório. O motor emite um erro (*"seção sem payload obrigatório"*) caso o bloco não possua esse campo, pois ele garante a unicidade do par `(arquivo, id)` no repositório.
* **Campos Livres:** Campos como `title` e `description` são reservados. Quaisquer outras chaves (ex: `owner`, `tags`) são preservadas no dicionário dinâmico da seção.

---

## 4. Semântica de Diretivas e Composição

O motor transcende a busca textual (Regex). As marcações não são apenas "substituídas", elas existem na árvore semântica da seção (`ParsedSection`) como nós próprios (ex: `IncludeDirective`).

### 4.1. Tipos de Arestas (DSL)

* **Dependência (`@ref`):** Sintaxe `@ref(uri)`. Cria uma aresta direcional apontando dependência contextual, mas **não** embute o conteúdo na composição final.
* **Inclusão/Transclusão (`@include`):** Sintaxe `@include(uri)`. Cria uma aresta direcional e instrui o motor a substituir o *token* da diretiva pela árvore (AST) completa do nó de destino durante a composição.
* **Consulta Dinâmica (`@query` - *Reserved for Future Use*):** Sintaxe `@query(key=value)`. Uma aresta polimórfica projetada para resolver múltiplos nós em tempo de execução baseando-se no *payload* YAML (GraphQL Documental).

### 4.2. Regras de Composição

* **Ordem Espacial:** A expansão de nós via `@include` segue estritamente a ordem de ocorrência dos *tokens* diretivos na AST do documento pai.
* **Deduplicação de Nós:** Se A inclui D e B também inclui D. No comportamento padrão (`deduplicate: false`), D é materializado duas vezes, refletindo a intenção textual exata. Sob a *flag* `--deduplicate`, o motor materializa a primeira ocorrência e substitui a segunda por um `@ref` (link simples).
* **Tratamento de Falhas (`--strict`):** Se uma URI referenciada não existir no índice:
* **Padrão:** O motor emite um *Warning* no terminal, injeta um *placeholder* em HTML no documento (``) e prossegue.
* **Strict:** O motor lança um Erro fatal e aborta o processo, garantindo integridade para pipelines de CI/CD.



---

## 5. Modelagem Matemática (Teoria dos Grafos)

O ecossistema documental é modelado como um **Grafo Direcionado (Dígrafo) Geral**, definido como $G = (V, E)$. O repositório documentado pode conter ciclos lógicos nativamente.

* Vértices $v \in V$ possuem propriedades estruturais e semânticas.
* Arestas $E$ são classificadas por diretivas ($E_{ref}$, $E_{include}$) e indexadas bidirecionalmente para buscas em $O(1)$.
* **Resolução Acíclica:** Durante a operação de materialização (`compose`), o algoritmo de travessia rastreia o caminho de execução atual ($P$). Se for avaliada uma aresta de inclusão $(x, y)$ onde $y \in P$, o **ciclo é detectado e a aresta é rompida silenciosamente na saída**, prevenindo *loops* de renderização, sem alterar a topologia do Grafo original.

---

## 6. Modelagem em Código (Pydantic & Arquitetura)

O modelo consolida a visão de *Pipeline*, isolando a delimitação bruta do significado de negócios.

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Set, Literal
from collections import defaultdict

# --- Fase 2: Delimitação Física ---
class RawSection(BaseModel):
    """Resolve apenas o escopo espacial da seção na AST e no arquivo fonte."""
    heading_level: int
    heading_text: str
    token_start: int
    token_end: int
    source_start_line: int
    source_end_line: int

# --- Fase 4: Semântica e Diretivas ---
class Directive(BaseModel):
    """Diretivas deixam de ser texto e se tornam nós lógicos."""
    type: Literal["ref", "include", "query"]
    target_uri: str

class ParsedSection(BaseModel):
    """Resolve o significado. Amarra o espaço físico aos metadados e referências."""
    raw: RawSection
    uri: str
    file_path: str
    metadata: Dict[str, Any]
    directives: List[Directive] = Field(default_factory=list)

# --- Fase 5: Indexação e Grafo ---
class SectionIndex(BaseModel):
    """Repositório de acesso em O(1) de seções já parseadas."""
    sections: Dict[str, ParsedSection] = Field(default_factory=dict)

class SectionGraph(BaseModel):
    """Gestão topológica de dependências (Backlinks suportados)."""
    index: SectionIndex
    outgoing_edges: Dict[str, Set[str]] = Field(default_factory=lambda: defaultdict(set))
    incoming_edges: Dict[str, Set[str]] = Field(default_factory=lambda: defaultdict(set))

```

---

## 7. Estratégia de Indexação e Cache

A leitura de repositórios massivos exige que a etapa de *parsing* e validação não ocorra de forma repetitiva durante as consultas.

* **Estado Inicial:** O comando `index_repository()` constrói o `SectionIndex` inteiramente em memória a partir dos arquivos `.md`.
* **Persistência (Evolução):** Após a estabilização do núcleo, o `SectionIndex` tipado será serializado no cache `.mdgraph/index.json`.
* **Otimização:** Execuções subsequentes carregarão o `.json` e reavaliarão a AST apenas para os arquivos cujos *hashes* no sistema operacional apresentarem diferenças em relação ao cache.

---

## 8. Interface da CLI (Casos de Uso)

O motor responde a três comandos principais, alinhados à sua dupla representação (Documental vs Semântica):

### 8.1. `mdgraph get <URI>` (Fidelidade Documental)

Extrai uma seção isolada baseando-se estritamente na representação espacial (`source_start_line` e `source_end_line`).

* **Mecânica:** O motor abre o arquivo fonte, fatia as linhas especificadas no objeto `RawSection` e joga para o `stdout`.
* **Garantia:** Preservação milimétrica de formatação original, comentários e espaços. Nada passa pelo reconstrutor de AST.

### 8.2. `mdgraph tree <URI>` (Visão Estrutural)

Consulta o Grafo em memória e resolve a hierarquia visual baseada na semântica.

* **Saída:** Árvore de dependências ilustrativa no terminal. Suporta `--refs` para exibir conexões que apontam para a URI solicitada (Inversão de Dependência).

### 8.3. `mdgraph compose <URI>` (Materialização Semântica)

O motor entra em modo *transpiler*. Baseando-se na AST da `ParsedSection`, ele navega de *token* em *token*.

* Ao encontrar texto normal: repassa o *token*.
* Ao encontrar um nó `IncludeDirective`: interrompe o fluxo, busca a AST alvo, injeta na cadeia resolvendo o nível matemático dos *headings*, e retoma a varredura.
* **Comportamento:** Retorna um grande documento unificado, suportando as *flags* `--deduplicate` e `--strict`. O resultado da árvore composta pode ser opcionalmente exportado via `--json` para integrações de infraestrutura.