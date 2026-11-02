# THIRD_PARTY_NOTICES

> **Estado (v1): o material do Corey Haines e da ByteDance DeerFlow está importado em `vendor/`, com material derivado em `compiled/corey/` (6 skills) e `compiled/bytedance/` (2 skills).** Este documento registra as fontes, suas licenças e as regras de atribuição.

## Fontes

### 1. Marketing Skills — Corey Haines

- **Repositório:** https://github.com/coreyhaines31/marketingskills
- **Licença:** MIT
- **Aviso de copyright do upstream:** `Copyright (c) 2025 Corey Haines`
- **Commit importado:** `88c79f6528a9347420e57ceb1fff9a60de651768`
- **Importado no PR 1 (73 arquivos, em `vendor/corey/`):**
  - `skills/product-marketing/` (2.2.0, 3 arquivos), `skills/copywriting/` (2.3.2, 5), `skills/copy-editing/` (2.2.1, 5), `skills/social/` (2.4.1, 11), `skills/ad-creative/` (2.12.2, 14), `skills/emails/` (2.1.4, 5), `skills/content-strategy/` (2.1.5, 4), `skills/sales-enablement/` (2.4.0, 8), `skills/marketing-council/` (1.0.0, 15), cada diretório na íntegra (SKILL.md, references, assets e evals): 70 arquivos;
  - `skills/ads/references/meta-decision-system.md` e `skills/ads/references/abm-playbook.md` (dependências transitivas do `ad-creative`): 2 arquivos;
  - `LICENSE`: 1 arquivo.
  - A lista por arquivo, com sha256, está em `provenance/upstream-lock.json`.
- **Material derivado (PR 2):** `compiled/corey/` tem 6 compilados (`product-marketing`, `copywriting`, `copy-editing`, `social`, `ad-creative` e `emails`). Cada um combina o `SKILL.md` upstream com os overlays do Studio e traz o comentário de origem com commit, versão, hashes e o aviso `Copyright (c) 2025 Corey Haines. MIT License — see vendor/corey/LICENSE.`
- **Atribuição aninhada, já presente no upstream:** o material do Corey inclui trechos adaptados de skills publicadas sob MIT em [skills-marketing-library](https://github.com/retieedra-profound/skills-marketing-library):
  - `improved-copywriting`, da Profound: em `skills/copywriting/SKILL.md` e `skills/copy-editing/references/checklist.md`, e citada também em `skills/copywriting/references/ai-tells.md`;
  - `humanizer`, da Profound, e `writing`, da Wispr Flow: em `skills/copywriting/references/ai-tells.md`;
  - `copy-editing`, da Wispr Flow: em `skills/copy-editing/references/checklist.md`;
  - `brand-voice`, da Wispr Flow: em `skills/product-marketing/references/brand-voice.md`.

  As linhas de crédito ficam sem alteração em `vendor/corey/`. A do `copywriting/SKILL.md` também está em `compiled/corey/copywriting.md`; nenhum overlay remove crédito.
- **Fora do escopo:** a pasta `tools/` (CLIs e integrações de plataforma) não é importada.
- **Observação:** a skill `marketing-council` simula conselheiros com base em obras publicadas de profissionais reais. A própria skill exige que essa saída seja rotulada como simulação, e o Studio mantém essa exigência.

### 2. DeerFlow — ByteDance

- **Repositório:** https://github.com/bytedance/deer-flow
- **Skill principal:** https://github.com/bytedance/deer-flow/tree/main/skills/public/newsletter-generation
- **Licença:** MIT
- **Avisos de copyright do upstream:** `Copyright (c) 2025 Bytedance Ltd. and/or its affiliates` e `Copyright (c) 2025-2026 DeerFlow Authors`
- **Commit importado:** `12c304f12ce5c0bf66d8927386e5dd18ea84f685` (o upstream não versiona as skills; a versão no lock é o SHA)
- **Importado na v1 (3 arquivos, em `vendor/bytedance/`, no mesmo caminho do upstream):** `skills/public/newsletter-generation/SKILL.md`, `skills/public/deep-research/SKILL.md` e `LICENSE`. Os sha256 estão em `provenance/upstream-lock.json`.
- **Material derivado:** `compiled/bytedance/newsletter-generation.md` e `compiled/bytedance/deep-research.md`, com o comentário de origem e os dois avisos de copyright: `Copyright (c) 2025 Bytedance Ltd. and/or its affiliates; Copyright (c) 2025-2026 DeerFlow Authors. MIT License — see vendor/bytedance/LICENSE.`
- **Fora do escopo:** a plataforma DeerFlow (aplicação, backend e demais skills) não é importada.

### 3. X Content Brain — não é material de terceiros

- **Repositório:** https://github.com/julianobruxo/x-content-brain (privado, do operador)
- **Relação com o Studio:** dependência externa acionada por handoff (`DECISIONS.md`, ADR-04).
- **Nenhum conteúdo do Brain é copiado para este repositório:** voz, políticas, exemplos, Golden, corpus e estado ficam lá.

## Regras de atribuição a partir da importação

1. **Cópia literal (`vendor/<fonte>/`):** os arquivos ficam idênticos ao upstream, sem edição. O `LICENSE` original de cada fonte é copiado na íntegra para `vendor/<fonte>/LICENSE`.
2. **Material derivado (`compiled/<fonte>/`):** cada arquivo compilado combina o texto upstream com overlays do Studio e traz um cabeçalho com repositório de origem, commit, versão da skill, hash do overlay, aviso de copyright do upstream e a indicação "MIT License — see `vendor/<fonte>/LICENSE`".
3. **Rastreabilidade:** `provenance/upstream-lock.json` registra, por arquivo importado, origem, commit e sha256. Este documento é atualizado a cada importação com a lista efetiva do que foi importado.
4. **Sem remoção de avisos:** nenhum overlay ou compilação remove avisos de copyright, licença ou atribuição presentes no upstream.

## Texto da licença MIT

A licença MIT de cada fonte é reproduzida integralmente, como publicada no upstream: `vendor/corey/LICENSE` e `vendor/bytedance/LICENSE`.
