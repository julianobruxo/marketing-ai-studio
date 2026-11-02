# THIRD_PARTY_NOTICES

> **Estado (PR 0): nenhum arquivo de terceiros foi importado ainda.** Este documento registra as fontes previstas, suas licenças e as regras de atribuição que valerão a partir dos PRs 1 e 9.

## Fontes previstas

### 1. Marketing Skills — Corey Haines

- **Repositório:** https://github.com/coreyhaines31/marketingskills
- **Licença:** MIT
- **Aviso de copyright do upstream:** `Copyright (c) 2025 Corey Haines`
- **Commit previsto:** `88c79f6` (reconfirmado no PR 1)
- **Importação prevista (PR 1):**
  - `skills/product-marketing/`, `skills/copywriting/`, `skills/copy-editing/`, `skills/social/`, `skills/ad-creative/`, `skills/emails/`, `skills/content-strategy/`, `skills/sales-enablement/`, `skills/marketing-council/`, cada diretório na íntegra (SKILL.md, references, assets e evals);
  - `skills/ads/references/meta-decision-system.md` e `skills/ads/references/abm-playbook.md` (dependências transitivas do `ad-creative`);
  - `LICENSE`.
- **Fora do escopo:** a pasta `tools/` (CLIs e integrações de plataforma) não é importada.
- **Observação:** a skill `marketing-council` simula conselheiros com base em obras publicadas de profissionais reais. A própria skill exige que essa saída seja rotulada como simulação, e o Studio mantém essa exigência.

### 2. DeerFlow — ByteDance

- **Repositório:** https://github.com/bytedance/deer-flow
- **Skill principal:** https://github.com/bytedance/deer-flow/tree/main/skills/public/newsletter-generation
- **Licença:** MIT
- **Aviso de copyright do upstream:** `Copyright (c) 2025 Bytedance Ltd. and/or its affiliates`
- **Commit previsto:** `12c304f` (reconfirmado no PR 9)
- **Importação prevista (PR 9):** `skills/public/newsletter-generation/SKILL.md`, `skills/public/deep-research/SKILL.md` e `LICENSE`.
- **Fora do escopo:** a plataforma DeerFlow (aplicação, backend e demais skills) não é importada.

### 3. X Content Brain — não é material de terceiros

- **Repositório:** https://github.com/julianobruxo/x-content-brain (privado, do operador)
- **Relação com o Studio:** dependência externa acionada por handoff (`DECISIONS.md`, ADR-04).
- **Nenhum conteúdo do Brain é copiado para este repositório:** voz, políticas, exemplos, Golden, corpus e estado ficam lá.

## Regras de atribuição a partir da importação

1. **Cópia literal (`vendor/<fonte>/`):** os arquivos ficam idênticos ao upstream, sem edição. O `LICENSE` original de cada fonte é copiado na íntegra para `vendor/<fonte>/LICENSE`.
2. **Material derivado (`compiled/<fonte>/`):** cada arquivo compilado combina o texto upstream com overlays do Studio e traz um cabeçalho com repositório de origem, commit, versão da skill, hash do overlay, aviso de copyright do upstream e a indicação "Licença MIT — ver `vendor/<fonte>/LICENSE`".
3. **Rastreabilidade:** `provenance/upstream-lock.json` registra, por arquivo importado, origem, commit e sha256. Este documento é atualizado no PR 1 (Corey) e no PR 9 (ByteDance) com a lista efetiva do que foi importado.
4. **Sem remoção de avisos:** nenhum overlay ou compilação remove avisos de copyright, licença ou atribuição presentes no upstream.

## Texto da licença MIT

A licença MIT de cada fonte será reproduzida integralmente, como publicada no upstream, em `vendor/corey/LICENSE` (PR 1) e `vendor/bytedance/LICENSE` (PR 9).
