# Fixtures sintéticas

Todo o conteúdo desta pasta é **sintético**, criado só para os testes do `scripts/vendor.py`. Nada aqui vem de upstream nem de material real de marca ou cliente.

| Fixture | Uso |
|---|---|
| `synthetic-ok/` | mini-repositório com vendor e lock coerentes; o `verify` deve passar. Cobre links que precisam ser ignorados (http, mailto, âncora, blocos e trechos de código). |
| `synthetic-broken-link/` | igual em estrutura, com hashes corretos e um único link relativo quebrado; o `verify` deve falhar só por `[LINK]`. |
| `compile-basic/` | mini-repositório com vendor, lock, overlays e compilado coerentes para o `compile` (PR 2). Inclui as quatro operações, um título falso dentro de bloco de código, um link relativo com âncora e menções de host sintéticas. |
