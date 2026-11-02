# MAP — Marketing Content Studio

Mapa da estrutura aprovada no manifesto R4. Leia este arquivo antes de abrir qualquer outro. Ele diz o que existe, para que serve e em qual PR cada item entra.

**Hoje (PR 2) existem apenas:** `README.md`, `MAP.md`, `DECISIONS.md`, `THIRD_PARTY_NOTICES.md`, `.gitignore`, `.gitattributes`, `vendor/corey/`, `provenance/upstream-lock.json`, `overlays/corey/` (`_common.md` e 6 overlays), `compiled/corey/` (6 compilados), `scripts/vendor.py` (`sync`, `verify` e `compile`) e `tests/` (`test_vendor.py`, `test_compile.py` e fixtures sintéticas). Todos os outros itens estão planejados.

## Legenda

| Marca | Significado |
|---|---|
| **MVP · PR n** | faz parte do MVP funcional; entra no PR indicado |
| **POSTERIOR** | fora do MVP; entra só com decisão própria |
| **REMOVIDO** | proposto no debate e descartado; não deve ser criado |
| **canônico** | fonte da verdade; editado à mão via PR |
| **gerado** | produzido por script; nunca editado à mão |
| **externo** | cópia literal de terceiros; nunca editado |

## Árvore

```text
marketing-ai-studio/                                              [público · repositório do Marketing Content Studio]
├── README.md                                   MVP · PR 0   canônico
├── MAP.md                                      MVP · PR 0   canônico (atualizado a cada PR)
├── DECISIONS.md                                MVP · PR 0   canônico
├── THIRD_PARTY_NOTICES.md                      MVP · PR 0   canônico (atualizado nos PRs 1, 2 e 9)
├── .gitignore                                  MVP · PR 0   canônico
├── .gitattributes                              MVP · PR 1   canônico
│
├── skills/marketing-content-studio/
│   ├── SKILL.md                                MVP · PR 4   canônico — única entrada; roteamento; fail-closed
│   └── references/compatibility.md             MVP · PR 4   canônico — capacidades reais por host
│
├── catalog/
│   ├── skills.yaml                             MVP · PR 4   canônico — skill → tarefas, capacidades, escritas interceptadas, skills ausentes
│   └── routing.yaml                            MVP · PR 4   canônico — identidade × marca × canal × intenção → dono
│
├── vendor/                                                  externo — idêntico ao upstream, somente leitura
│   ├── corey/
│   │   ├── LICENSE                             MVP · PR 1
│   │   └── skills/
│   │       ├── product-marketing/              MVP · PR 1
│   │       ├── copywriting/                    MVP · PR 1
│   │       ├── copy-editing/                   MVP · PR 1
│   │       ├── social/                         MVP · PR 1
│   │       ├── ad-creative/                    MVP · PR 1
│   │       ├── emails/                         MVP · PR 1
│   │       ├── content-strategy/               MVP · PR 1   importada; roteamento posterior
│   │       ├── sales-enablement/               MVP · PR 1   importada; roteamento posterior
│   │       ├── marketing-council/              MVP · PR 1   importada; só como insumo do Strategist
│   │       └── ads/references/
│   │           ├── meta-decision-system.md     MVP · PR 1   dependência transitiva do ad-creative
│   │           └── abm-playbook.md             MVP · PR 1   dependência transitiva do ad-creative
│   └── bytedance/
│       ├── LICENSE                             MVP · PR 9
│       └── skills/public/
│           ├── newsletter-generation/          MVP · PR 9
│           └── deep-research/                  MVP · PR 9
│
├── overlays/                                                canônico — operações declarativas por âncora
│   ├── corey/_common.md                        MVP · PR 2   canônico — snippets comuns (regras de operação, vínculo de contexto)
│   ├── corey/<skill>.md                        MVP · PR 2   só as 6 skills roteadas no MVP
│   └── bytedance/<skill>.md                    MVP · PR 9
│
├── compiled/                                   MVP · PR 2 / PR 9   gerado — vendor + overlay; commitado para revisão de diff
│   └── corey/
│       ├── product-marketing.md                MVP · PR 2   gerado
│       ├── copywriting.md                      MVP · PR 2   gerado
│       ├── copy-editing.md                     MVP · PR 2   gerado
│       ├── social.md                           MVP · PR 2   gerado
│       ├── ad-creative.md                      MVP · PR 2   gerado
│       └── emails.md                           MVP · PR 2   gerado
│
├── profiles/
│   ├── brands/_template.yaml                   MVP · PR 6   canônico — fatos, posicionamento, claims permitidos, proibições
│   └── personas/_template.yaml                 MVP · PR 6   canônico — voz, idioma, registro
│
├── workflows/
│   ├── strict-source.yaml                      MVP · PR 6   canônico
│   ├── copy.yaml                               MVP · PR 6   canônico — LinkedIn, anúncio, e-mail
│   ├── brain-handoff.yaml                      MVP · PR 7   canônico
│   ├── newsletter.yaml                         MVP · PR 9   canônico
│   └── campaign.yaml                           POSTERIOR · PR 10
│
├── agents/                                                  canônico — corpo do prompt de cada papel, neutro em relação ao host
│   ├── orchestrator.md                         MVP · PR 3
│   ├── strategist.md                           MVP · PR 3
│   ├── writer.md                               MVP · PR 3
│   ├── critic.md                               MVP · PR 3
│   ├── reviewer.md                             MVP · PR 3
│   └── researcher.md                           MVP · PR 9
│
├── hosts/claude-code/
│   ├── host.yaml                               MVP · PR 3   canônico — modelo, ferramentas, env e regras de caminho por papel
│   └── guard.py                                MVP · PR 3   canônico — hook PreToolUse: caminho por papel + log de tentativas
│
├── policies/
│   ├── independent-agents.md                   MVP · PR 5   canônico — inclui aprovação humana
│   ├── editorial-loop.md                       MVP · PR 5   canônico — máquina de estados + orçamentos
│   ├── learning-governance.md                  MVP · PR 5   canônico
│   ├── source-fidelity.md                      MVP · PR 6   canônico — 3 modos + proveniência por claim + injeção
│   └── brand-persona-separation.md             MVP · PR 6   canônico — lugar único da precedência (ADR-16)
│
├── integrations/x-content-brain.yaml           MVP · PR 7   canônico — URL, referência de autenticação, política de ref; nenhum conteúdo do Brain
│
├── schemas/
│   ├── job.schema.json                         MVP · PR 5
│   ├── verdict.schema.json                     MVP · PR 5
│   ├── source-ledger.schema.json               MVP · PR 5
│   └── run-ledger.schema.json                  MVP · PR 5
│
├── scripts/
│   ├── vendor.py                               MVP · PR 1 (sync, verify) · PR 2 (compile)
│   └── install_host.py                         MVP · PR 3
│
├── provenance/upstream-lock.json               MVP · PR 1   gerado por vendor.py; commitado
│
├── tests/
│   ├── fixtures/                               MVP · PR 1 em diante — sintéticos, rotulados como tal
│   └── test_*.py                               MVP · PR 1 em diante
│
├── examples/                                   POSTERIOR    nasce com o primeiro item operator-approved
└── runtime/                                    POSTERIOR    só com ADR específico de runtime fino
```

**Skills sem compilado:** `content-strategy`, `sales-enablement` e `marketing-council` estão em `vendor/corey/`, mas não têm overlay nem compilado. Por isso não são carregáveis pelo Studio até ganharem overlay.

### Gerados localmente, fora do git

| Caminho | Produzido por | Observação |
|---|---|---|
| `.claude/skills/marketing-content-studio/` | `install_host.py` (PR 3) | cópia de `skills/marketing-content-studio/` |
| `.claude/agents/<papel>.md` | `install_host.py` (PR 3) | frontmatter de `host.yaml` + corpo de `agents/` |
| `.claude/settings.json` | `install_host.py` (PR 3) | env, regras de permissão e hooks |
| `runs/<job>/` | execução | drafts, eval-pack, vereditos, ledgers, tool-log, contexto de marca do job |

Tudo em `.claude/` precisa poder ser reconstruído a partir de um clone limpo (T-INSTALL). Se algum item não puder, ele passa a ser fonte canônica versionada.

### Itens removidos (não criar)

`catalog/capabilities.yaml` · `adapters/` (todos os arquivos) · `workflows/social.yaml` · `policies/human-approval.md` · `policies/prompt-injection.md` · `policies/privacy.md` · `schemas/agent-output.schema.json`

O conteúdo de cada um foi absorvido por outro arquivo da árvore, conforme a R4.

## Fluxo de carregamento (planejado)

1. A skill de entrada lê este `MAP.md`.
2. O roteamento (`catalog/routing.yaml`) define o dono: Brain ou Studio.
3. Se o dono é o Studio, carrega só o workflow do formato, o compilado das skills necessárias (`compiled/`) e o contexto do job.
4. Os papéis recebem apenas o pacote do seu papel. Critic e Reviewer recebem `runs/<job>/eval-pack/`, nunca os rascunhos do Writer.

## Testes de aceitação previstos

**Implementados e executados: T14 (PR 1, `tests/test_vendor.py`) e T-COMPILE (PR 2, `tests/test_compile.py`).** Os demais testes da tabela estão planejados.

| ID | O que verifica | PR |
|---|---|---|
| T14 | integridade upstream: arquivos batem com o lock; alteração de 1 byte falha; 0 links quebrados; licenças presentes | 1 |
| T-COMPILE | compilação reproduzível; frontmatter válido; âncoras resolvem; cabeçalho com SHA e copyright | 2 |
| T-HOOK | o hook dispara dentro de subagentes e nega escrita do Writer fora de `drafts/`, com tentativa registrada | 3 |
| T-PATH | guard resiste a caminhos relativos, `../`, symlinks e qualquer fuga do diretório autorizado | 3 |
| T-ISO-W | histórico privado do Writer ausente no Critic | 3 |
| T-ISO-O | histórico privado do orquestrador ausente nos subagentes (detecta fork) | 3 |
| T-SCOPE | Critic lê só o material autorizado; tentativas fora do escopo negadas e registradas | 3 |
| T-RO | Critic e Reviewer sem ferramenta de escrita (prova estática + ausência de efeito) | 3 |
| T-WRITE | Writer escreve em `drafts/`; permitido e registrado | 3 |
| T-INSTALL | etapa 1: clone limpo → instalação → só a skill do Studio aparece no host | 3 |
| T-INSTALL | etapa 2: a skill executa um job de fixture e gera o run ledger | 6 |
| T01 | roteamento por dono (Yann × X → Brain; Zazmic LinkedIn → Studio) | 4 |
| T03 | autor e avaliador com o mesmo ID ou contexto → hard FAIL | 5 |
| T04 | host sem subagentes → nenhum `critic-pass` multiagente | 5 |
| T12 | não-progresso detectado; plano muda; orçamento respeitado | 5 |
| T13 | `critic-pass` nunca vira `operator-approved` nem publica sozinho | 5 |
| T05 | tradução `strict-source` com claim, benchmark ou CTA novo → FAIL com evidência | 6 |
| T06 | dois jobs de marcas diferentes sem vazamento; contexto de marca sem escrita | 6 |
| T09 | claim só de snippet → UNVERIFIED; claim do briefing → `user-provided` | 6 |
| T11 | ângulo ruim leva a estratégia estruturalmente diferente, não a SKIP automático | 6 |
| T02 | Brain indisponível → BLOCKED, sem fallback ao Corey | 7 |
| T15 | baseline de falso PASS e falso FAIL do Critic por modalidade | 8 |
| T16 | troca do modelo do Reviewer não altera contrato nem status | 8 |
| T07 | newsletter respeita a janela de datas pedida | 9 |
| T08 | capacidades do DeerFlow mapeadas; referências upstream resolvem | 9 |
| T10 | instrução injetada em fonte não altera o comportamento | 9 |
