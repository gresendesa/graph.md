# mdb examples

```yaml
section: examples-readme
title: mdb examples
```

This directory contains a functional Markdown repository demonstrating all engine features.

## Structure

```
examples/
  wiki/
    intro.md               # root page — uses @include and @ref
    conceitos/
      basico.md            # leaf section with no external dependencies
      avancado.md          # uses @ref to basico
    guia/
      instalacao.md        # uses @include of avancado
```

## How to run

```bash
# From the project root (with .venv active):

# Extract a section
mdb get examples/wiki/intro.md#intro

# View dependency tree
mdb tree examples/wiki/guia/instalacao.md#instalacao --root examples/wiki

# View backlinks (who depends on basico)
mdb tree examples/wiki/conceitos/basico.md#basico --root examples/wiki --refs

# Compose a unified document from the root
mdb compose examples/wiki/intro.md#intro --root examples/wiki

# Compose and export as JSON
mdb compose examples/wiki/intro.md#intro --root examples/wiki --json

# Validate repository integrity
mdb validate --root examples/wiki

# Search by metadata
mdb search owner=example --root examples/wiki --json

# Get context of a node
mdb context examples/wiki/intro.md#intro --root examples/wiki --json

# Find impact of a change to basico
mdb impact examples/wiki/conceitos/basico.md#basico --root examples/wiki --json
```
