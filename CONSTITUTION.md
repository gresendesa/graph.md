# CONSTITUION - Graph.md

Versao: 1.0
Status: Ativa
Owner: gresendesa
Idioma oficial: pt-BR

## 1. Proposito

Criar uma ferramenta cli conforme specification.md.

## 2. Regras Nao Negociaveis

1. Nenhuma entrega e concluida sem teste manual documentado.
2. Nenhuma entrega e concluida sem checklist de regressao executado.
3. Testes sao obrigatorios no processo de desenvolvimento.
4. Commit de sprint so ocorre apos aceite explicito do PO.
5. Encerramento tecnico deve seguir um commit por sprint em cada repositorio envolvido.

## 3. Prioridade Estrategica

Ordem de prioridade atual:
1. Implementação e documentação

## 4. Politica de Branch e Mudanca

Modelo de branch:
- Git Flow simplificado.

Aprovacao de mudancas:
- Apenas o owner aprova mudancas na constituicao e diretrizes de memoria.

Risco de release aceito:
- Medio (ajustes pos-release sao aceitos quando necessarios).

## 4.1 Convencao de nomenclatura

Padrao oficial de IDs:

1. Itens de backlog
- Formato: B-XXX
- Exemplo: B-001

2. Sprints
- Formato: SPR-YYYY-NN
- Exemplo: SPR-2026-01

3. Tarefas internas da sprint
- Formato: S{N}-TXX
- Exemplo: S1-T03

Regras:
- IDs nao podem ser reutilizados.
- IDs descontinuados devem ser marcados como obsolete.
- Qualquer novo item deve nascer com ID antes de entrar em doing.

## 5. Definition of Done (DoD)

Para marcar qualquer item como concluido, e obrigatorio:
1. Teste manual documentado.
2. Checklist de regressao executado.
3. Registro atualizado em arquivos de memoria do projeto em scrum/.
4. Validacao manual executada sobre containers rebuildados/reinstanciados no fechamento da sprint.
5. Commit final apenas apos aceite explicito do PO com sistema em execucao.
6. Testes automatizados em `tests/` executados com sucesso (sem falhas).

## 5.2 Gate de encerramento de sprint (obrigatorio)

No encerramento da sprint, e obrigatorio:
1. rebuildar imagens locais com tag estavel (sem criar imagem por sprint)
2. derrubar instancia anterior e subir nova instancia para validacao
3. obter aceite explicito do PO em ambiente em execucao
4. executar um commit por sprint em cada repositorio envolvido no recorte

## 5.1 Sprint planning (obrigatorio)

Toda sprint deve passar por planning formal, conduzido pelo agente com participacao do owner.

No planning, e obrigatorio:
1. perguntar ao PO a prioridade dos itens elegiveis do backlog
2. registrar/atualizar o campo Prioridade PO no backlog
3. recortar itens do backlog para sprint respeitando a prioridade do PO
4. decompor itens em tarefas tecnicas
5. calcular risco por tarefa e risco agregado da sprint
6. definir ordem de execucao
7. registrar bloqueios previstos e mitigacoes

Escala de Prioridade PO:
- 1 = critica
- 2 = alta
- 3 = media
- 4 = baixa

Regra:
- Nenhum item entra em sprint sem Prioridade PO definida.

Escala de risco por tarefa:
- baixo = 1
- medio = 2
- alto = 3

Calculo do risco da sprint:
- media ponderada simples dos riscos das tarefas selecionadas
- classificacao final:
	- <= 1.4: baixo
	- > 1.4 e <= 2.3: medio
	- > 2.3: alto

## 6. Gestao de Memoria do Agente

A pasta scrum/ e a memoria operacional do projeto e deve seguir estas regras:

1. backlog.md
- Deve atuar como consolidador sintetico do backlog.
- Deve conter apenas ID, titulo, status, prioridade PO, risco e ponteiro para arquivo detalhado.

2. backlog/B-XXX.md
- Cada item de backlog deve ter um arquivo proprio em scrum/backlog/.
- O arquivo detalhado deve conter escopo, criterios de aceite, dependencias, owner e historico de atualizacao.

3. sprint.md
- Deve atuar como consolidador sintetico das sprints.
- Deve conter apenas status resumido, foco, risco e ponteiro para arquivo detalhado.

4. sprint/SPR-YYYY-NN.md
- Cada sprint deve ter um arquivo proprio em scrum/sprint/.
- O arquivo detalhado deve conter planning, tarefas, risco, execucao, bloqueios e encerramento.

6. experience.md
- Deve ser atualizado em toda retrospectiva ou incidente relevante.
- Deve registrar problema, causa raiz, acao corretiva e prevencao.

7. decisions.md
- Deve manter historico de decisoes sobre a arquitetura da memoria e governanca do processo.
- Cada decisao deve registrar contexto, escolha, impacto e data.

8. Historico
- O historico nao deve ser apagado.
- Conteudos antigos devem ser marcados como obsoletos, com data e motivo.

## 7. Padrao de Registro

Todo registro em scrum/ deve incluir:
- status
- owner
- data de criacao
- data de ultima atualizacao

Status padrao:
- todo
- doing
- blocked
- done
- obsolete

## 8. Vigencia e Alteracoes

Esta constituicao entra em vigor imediatamente.
Qualquer alteracao exige aprovacao explicita do owner.
