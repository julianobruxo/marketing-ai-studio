# MAP — Marketing Content Studio

Mapa do repositório (ADR-21/23). Para rodar um job, leia só o `AGENTS.md`. Este mapa é para quem vai mudar o repositório.

## Legenda

| Marca | Significado |
|---|---|
| **canônico** | fonte da verdade; editado à mão via PR |
| **gerado** | produzido por script; nunca editado à mão |
| **externo** | cópia literal de terceiros; nunca editado |
| **POSTERIOR** | fora da v1; entra só com decisão própria |

## Árvore

```text
marketing-ai-studio/
├── AGENTS.md                                                 gerado — arquivo central: boot, roteamento, loop e papéis; lido uma vez por sessão
├── CLAUDE.md, GEMINI.md                                      canônico — apontam para o AGENTS.md
├── README.md, MAP.md, DECISIONS.md, THIRD_PARTY_NOTICES.md   canônico
├── CRITIC.md                                                 canônico — parâmetros do Critic explicados ao operador
├── .gitignore, .gitattributes                                 canônico
│
├── skills/marketing-content-studio/
│   ├── SKILL.md                                canônico — única entrada; intake, roteamento, entrega
│   └── references/compatibility.md             canônico — capacidades exigidas e os dois modos
│
├── catalog/                                                 canônico — sintaxe JSON (YAML válido), lido com json
│   ├── routing.yaml                            dono por persona × marca × canal; intents com skills por papel, Strategist, pesquisa, fidelidade; max_rounds
│   └── skills.yaml                             skill → compilado, papéis, foco de leitura por papel
│
├── agents/                                                  canônico — prompt de cada papel, neutro em relação ao host; fonte do AGENTS.md
│   ├── boot.md                                 início do AGENTS.md: boot, intake, entrega
│   ├── orchestrator.md                         sessão principal: registro do job, loop de rodadas, regras duras
│   ├── strategist.md                           abordagem e pesquisa (só quando pedida)
│   ├── writer.md                               escreve em drafts/
│   └── critic.md                               avalia brief, voz, qualidade, fatos e fidelidade
│
├── hosts/claude-code/
│   ├── host.yaml                               canônico — modelo, ferramentas, env e regras de caminho por papel; sintaxe JSON
│   └── guard.py                                canônico — hook PreToolUse fail-closed: caminho e ferramentas por papel + log de toda chamada
│
├── vendor/                                                  externo — idêntico ao upstream, somente leitura
│   ├── corey/                                  LICENSE + 9 skills + 2 transitivos (73 arquivos)
│   └── bytedance/                              LICENSE + skills/public/newsletter-generation e deep-research (3 arquivos)
│
├── overlays/                                                canônico — operações declarativas por âncora, em inglês
│   ├── corey/_common.md + 6 overlays           copywriting, copy-editing, social, ad-creative, emails, product-marketing
│   └── bytedance/_common.md + 2 overlays       newsletter-generation, deep-research
│
├── compiled/                                                gerado — vendor + overlay; commitado para revisão de diff
│   ├── corey/                                  6 compilados
│   └── bytedance/                              2 compilados
│
├── provenance/upstream-lock.json                            gerado por vendor.py — commit, versão e sha256 de cada arquivo importado
│
├── scripts/
│   ├── vendor.py                               sync, verify, compile
│   ├── build_agents.py                         gera o AGENTS.md; --check confere
│   ├── eval_critic.py                          avaliação do Critic: pacote cego, pontuação e comparação
│   ├── route.py                                roteador determinístico + manifest de skill/hashes/seções (sem LLM)
│   ├── audit_skill_use.py                      audita pedidos Read autorizados por agente/rodada, sem alegar conclusão
│   └── install_host.py                         modo reforçado: instala agentes, skill de entrada e settings no clone de execução
│
├── tests/
│   ├── test_*.py                               unitários (unittest, só biblioteca padrão)
│   ├── fixtures/                               sintéticos, rotulados como tal
│   ├── critic/                                 casos sintéticos do Critic e resultados públicos
│   └── host/live_host_checks.py                testes ao vivo (claude -p); fora do unittest discover; não rodam a cada mudança
│
├── profiles/README.md                         canônico — contrato para perfis locais privados (arquivos reais ignorados)
├── policies/, integrations/                    POSTERIOR
└── examples/README.md                         canônico — goldens aprovados apenas com proveniência; conteúdo real ignorado
```

Fora da v1 (ADR-19): `workflows/` (a intent no `routing.yaml` faz esse papel), `schemas/`, o papel Reviewer (o Critic absorve fatos e fidelidade), campanha multicanal e o golden dataset da Zazmic.

**Handoff verificado em duas camadas:** o roteamento determina as seções e hashes, enquanto o contrato de cada papel exige carregar/aplicar o material e registrar um recibo. Em Claude Code, `audit_skill_use.py` pode identificar pedidos de Read autorizados por ID; **PreToolUse não prova que a leitura foi concluída nem que a skill foi aplicada**. Na maioria dos hosts, os excertos literais são injetados no contexto do subagente (sem abrir outra etapa do workflow). Só se usa leitura nativa sem injeção com evidência confiável de conclusão da ferramenta. O julgamento segue exigindo avaliação humana.\n\n**Skills sem compilado:** `content-strategy`, `sales-enablement` e `marketing-council` estão em `vendor/corey/`, mas não têm overlay. Não são carregáveis até ganharem um.

## Gerados localmente, fora do git

| Caminho | Produzido por | Observação |
|---|---|---|
| `.claude/skills/marketing-content-studio/` | `install_host.py` | cópia byte a byte de `skills/marketing-content-studio/` |
| `.claude/agents/studio-*.md` | `install_host.py` | frontmatter de `host.yaml` + corpo de `agents/`; os que saíram do `host.yaml` são removidos |
| `.claude/settings.json` | `install_host.py` | env, `deny` de edição e hook PreToolUse do guard (Python e guard com caminho absoluto) |
| `runs/.active` | orquestrador | id da tarefa ativa; o guard confina cada papel a essa tarefa |
| `runs/tool-log.jsonl` | `guard.py` | toda chamada de ferramenta; nunca gravável por ferramenta |
| `runs/<job>/` | execução | layout abaixo |

| `runs/<job>/` | Quem grava | Quem lê |
|---|---|---|
| `brief.md` | orquestrador | Strategist, Writer (o Critic recebe a cópia no eval-pack) |
| `inputs/` | orquestrador (material do operador e notas de pesquisa) | Strategist, Writer |
| `.agents/product-marketing.md` | orquestrador (contexto do job) | todos os papéis, só leitura |
| `drafts/` | só o Writer | Writer |
| `eval-pack/<rodada>/` | orquestrador (brief, candidato, insumos) | Critic |
| `verdicts/` | orquestrador (vereditos como retornados) | orquestrador |

## Clone de desenvolvimento e clone de execução

Isto só vale para o modo reforçado do Claude Code. O `settings.json` gerado nega edição em `vendor/`, `compiled/`, `overlays/`, `agents/`, `hosts/`, `scripts/`, `catalog/`, `.claude/` e outras pastas. Por isso:

- **Clone de desenvolvimento** (ex.: `C:\dev\mas`): onde o código muda. Nunca recebe instalação.
- **Clone de execução** (ex.: `C:\dev\studio-run`): só para rodar o Studio. Recebe `install_host.py --target` e é reinstalado depois de cada atualização.

## Fluxo de um job

1. O orquestrador lê o `AGENTS.md`, confere se há subagentes, faz o intake e roteia (`scripts/route.py` com shell; tabelas do `AGENTS.md` sem shell).
2. `owner: brain` → handoff ao X Content Brain; `NEEDS_OPERATOR` ou `BLOCKED` → para e avisa o operador.
3. `ROUTED` → o orquestrador roda até `max_rounds` rodadas de Strategist (quando a intent usa) → Writer → Critic, cada papel só com os compilados do seu papel.
4. Entrega: o candidato com `critic-pass`, ou o melhor candidato marcado como não aprovado, com a evidência do Critic.

## Testes

| Teste | Onde |
|---|---|
| Integridade do vendor contra o lock (T14) | `tests/test_vendor.py` |
| Compilação reproduzível, âncoras, cabeçalho, links (T-COMPILE) | `tests/test_compile.py` |
| Guard: caminhos, papéis, ferramentas, fail-closed (T-PATH) | `tests/test_guard.py` |
| Instalador: agentes, skill, settings, fumaça, idempotência | `tests/test_install.py` |
| Roteamento (T01) | `tests/test_route.py` |
| Coerência do catálogo | `tests/test_catalog.py` |
| `AGENTS.md` em sincronia com `agents/` e `catalog/` | `tests/test_agents_md.py` |
| Pontuação do Critic e sigilo dos casos públicos | `tests/test_eval_critic.py` |
| Host ao vivo: hook em subagente, isolamento, escopo (rodado no PR 3) | `tests/host/live_host_checks.py` |
