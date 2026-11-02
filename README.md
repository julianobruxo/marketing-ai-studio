# Marketing Content Studio

> **Estado: pré-implementação (PR 3).** Este repositório contém documentação, decisões de arquitetura e as skills do Corey Haines em `vendor/corey/`, com lock e verificação de integridade. Seis delas estão compiladas com os overlays do Studio em `compiled/corey/` (`scripts/vendor.py`). Também traz os prompts dos papéis (`agents/`), o host Claude Code com o guard de permissões (`hosts/claude-code/`) e o instalador (`scripts/install_host.py`). Nenhuma funcionalidade de geração de conteúdo foi implementada. Os arquivos da ByteDance ainda não foram importados.

## O que é

O Marketing Content Studio integra skills existentes de marketing e de newsletter num único ponto de entrada, coordenado por um sistema editorial multiagente. O sistema segue o ciclo **criação → avaliação independente → retorno à etapa causadora → entrega**, inspirado nas lições operacionais do X Content Brain.

As fontes integradas são:

| Fonte | Papel no Studio | Link |
|---|---|---|
| Corey Haines — Marketing Skills (MIT) | copy, anúncios, e-mails, LinkedIn, estratégia de conteúdo, contexto de marca | https://github.com/coreyhaines31/marketingskills |
| ByteDance — DeerFlow (MIT) | newsletter e pesquisa (`newsletter-generation`, `deep-research`) | https://github.com/bytedance/deer-flow · skill: https://github.com/bytedance/deer-flow/tree/main/skills/public/newsletter-generation |
| X Content Brain (privado, do operador) | autoridade exclusiva sobre conteúdo do Yann no X; o Studio só faz handoff | https://github.com/julianobruxo/x-content-brain |

## O que não é

- Não é uma nova biblioteca genérica de copywriting.
- Não é uma reimplementação do X Content Brain. Nenhuma voz, regra, exemplo ou Golden do Brain é copiada para cá.
- Não é um fork das skills do Corey ou da ByteDance. Os originais ficam intactos em `vendor/`, e as adaptações são feitas por overlays (ver `DECISIONS.md`, ADR-02 e ADR-17).

## Fronteira de responsabilidade

| Pedido | Dono |
|---|---|
| Yann no X: reply, quote tweet, post standalone | **X Content Brain** (handoff; o Studio não avalia o resultado) |
| LinkedIn e copy institucional da Zazmic | Studio |
| Copy, anúncios, e-mails de qualquer marca configurada | Studio |
| Newsletters e conteúdo com pesquisa | Studio |
| Tradução e adaptação fiel ao original (EN ↔ PT-BR) | Studio, modo `strict-source` |
| Outra persona no X | Studio, salvo integração configurada explicitamente |

## Princípios

1. **Integração, não reescrita.** As skills upstream são a fonte de capacidade.
2. **Ninguém avalia o próprio trabalho.** Writer, Critic e Reviewer rodam como agentes separados, com contexto isolado. Critic e Reviewer são somente leitura.
3. **Sem simulação.** Se o host não oferece subagentes reais, o job multiagente fica `BLOCKED`. Ele nunca é encenado num contexto só.
4. **Aprovação é humana.** Um `critic-pass` torna o candidato elegível para ser mostrado. Publicação e aprendizados dependem do operador.
5. **Fatos com proveniência.** Cada afirmação material tem origem registrada, conforme o modo de fidelidade do job.
6. **Decisões explícitas.** Toda mudança de comportamento passa por `DECISIONS.md` e por PR aprovado pelo operador.

## Estado e roteiro

Só existe no repositório o que está marcado como concluído ou em revisão; o restante está planejado. Os PRs seguem a ordem aprovada no ADR-15.

| PR | Escopo | Estado |
|---|---|---|
| 0 | Documentação e decisões | concluído |
| 1 | Vendor do Corey, lock e verificação de integridade | concluído |
| 2 | Overlays e compilação das skills roteadas do Corey | concluído |
| 3 | Agentes, configuração do host Claude Code, guard de permissões e instalador | em revisão |
| 4 | Skill de entrada, mapa e catálogo de roteamento | planejado |
| 5 | Schemas, políticas de independência e loop editorial | planejado |
| 6 | Workflows `strict-source` e `copy`, perfis de marca e persona, contexto por job | planejado |
| 7 | Handoff ao X Content Brain e experimento de integração A/B | planejado |
| 8 | Perfil Zazmic, regressões a partir de material do operador, jobs reais | planejado → **marco de copy** |
| 9 | ByteDance: newsletter, pesquisa e agente Researcher | planejado → **MVP funcional** |
| 10 | Campanhas multicanal | posterior |

O Studio só será declarado **funcional** ao fim do PR 9, quando reunir: Corey (copy, anúncios, e-mails, LinkedIn), ByteDance (newsletter e pesquisa), handoff ao Brain, loop multiagente com avaliação independente e marcas/personas configuráveis.

## Host de execução

O primeiro host é o **Claude Code**: a sessão principal faz o papel de orquestrador e os demais papéis rodam como subagentes nomeados. O Claude Code é o primeiro host, não o único; tudo que é específico dele fica em `hosts/claude-code/` (ADR-12). O chat do claude.ai e o ChatGPT servem para planejamento, revisão e debate, não para execução.

**Instalação, sempre num clone de execução:** o instalador grava um `.claude/settings.json` que bloqueia edição em `vendor/`, `compiled/`, `overlays/`, `policies/`, `scripts/`, `.claude/` e outras pastas do Studio. Por isso o Studio roda num clone separado, só para execução. O clone de desenvolvimento nunca recebe instalação, ou o agente de código perderia a permissão de editar o repositório.

```bash
git clone https://github.com/julianobruxo/marketing-ai-studio.git C:\dev\studio-run
```

```bash
python C:\dev\studio-run\scripts\install_host.py --host claude-code --target C:\dev\studio-run
```

O instalador cria os 4 subagentes (`studio-strategist`, `studio-writer`, `studio-critic`, `studio-reviewer`) e as configurações, e termina com um teste de fumaça do hook. A skill de entrada só existe a partir do PR 4. O hook guarda o caminho absoluto do Python usado na instalação, então reinstale depois de cada `git pull` ou troca de Python.

## Privacidade

Este repositório é **público** e é um projeto pessoal do operador (ADR-14). Por isso, ficam fora do git por padrão: briefings de clientes, execuções (`runs/`), segredos e credenciais (ver `.gitignore`). Ledgers de execução permanecem locais. Material de marcas de terceiros (por exemplo, a Zazmic) só é commitado se já for público ou se houver liberação explícita.

## Como as decisões mudam

- O registro canônico é `DECISIONS.md`.
- Qualquer alteração de decisão, política ou aprendizado é feita por PR.
- O operador revisa e autoriza o merge. Não há merge automático.
- Uma decisão só é reaberta se a implementação comprovar uma incompatibilidade.

## Licenças

O conteúdo próprio do Studio ainda não tem licença de uso definida; sem um arquivo de licença, vale o padrão de todos os direitos reservados ao autor. O material de terceiros e suas licenças estão descritos em `THIRD_PARTY_NOTICES.md`.

## Documentos

- `MAP.md`: estrutura do repositório e estado de cada item.
- `DECISIONS.md`: os 18 ADRs e as verificações pendentes.
- `THIRD_PARTY_NOTICES.md`: fontes, licenças e atribuições.
