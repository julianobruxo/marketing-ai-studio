# DECISIONS — Marketing Content Studio

Registro canônico das decisões de arquitetura. As decisões foram fechadas no debate entre Claude e GPT-6, conduzido pelo operador, encerrado com a aprovação do manifesto R4 em 2026-11-02.

**Regras deste arquivo**
- Cada assunto tem uma decisão só. Uma decisão nova substitui a anterior no mesmo PR, marcando o texto superado como `Substituído por ADR-nn`.
- Uma decisão só é reaberta se a implementação comprovar uma incompatibilidade.
- Alterações entram por PR; o merge depende de aprovação do operador.

**Estados usados:** `Aceito` · `Aceito, com verificação pendente` (a decisão vale, mas um teste previsto pode exigir ajuste de implementação) · `Substituído`.

**Nada neste arquivo descreve recurso implementado.** Todos os testes citados estão planejados e não foram executados.

---

## ADR-01 — Objetivo: integração, não reescrita

- **Contexto:** o operador quer um único ponto de entrada para qualquer formato de conteúdo, combinando o melhor das skills públicas de Corey Haines (https://github.com/coreyhaines31/marketingskills) e da ByteDance DeerFlow (https://github.com/bytedance/deer-flow), com o chassi editorial do X Content Brain (https://github.com/julianobruxo/x-content-brain).
- **Decisão:** o Studio integra e coordena skills existentes. Ele não cria uma biblioteca nova de copywriting e não reimplementa o Brain.
- **Consequências:** o trabalho próprio do Studio se limita a roteamento, orquestração, overlays, contratos, políticas, perfis e testes. O conteúdo de ofício vem dos upstreams.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-02 — Vendor intacto com lock

- **Contexto:** as skills upstream mudam com frequência (no Corey, 50 de 53 skills foram atualizadas em outubro de 2026) e dependem de references, assets, evals e arquivos de outras skills. Submodules não entram no "Download ZIP" do GitHub, e subtree traria o repositório inteiro.
- **Decisão:**
  - Os diretórios selecionados são copiados **integralmente e sem edição** para `vendor/`, mais as dependências transitivas.
  - `provenance/upstream-lock.json` registra, por fonte: repo, commit, sha256 do `LICENSE` e data. Por skill: caminho upstream, versão (o `metadata.version` do Corey; na ByteDance, apenas o SHA), sha256 de cada arquivo e o motivo (`selecionada` ou `transitiva`).
  - `scripts/vendor.py sync` importa uma ref, atualiza vendor, lock e compilados, e gera um relatório com arquivos alterados, versões, descrições alteradas, âncoras quebradas e capacidades de host novas. O resultado vai para PR. **Nunca há merge automático.**
  - `scripts/vendor.py verify` falha se algum hash diverge do lock, se um link relativo não resolve, se uma âncora de overlay sumiu, se o compilado não é reproduzível ou se aparece uma ferramenta de host sem mapeamento.
- **Conjunto a importar:**
  - **Corey**, commit previsto `88c79f6`, 73 arquivos:
    - `product-marketing` (2.2.0)
    - `copywriting` (2.3.2)
    - `copy-editing` (2.2.1)
    - `social` (2.4.1)
    - `ad-creative` (2.12.2)
    - `emails` (2.1.4)
    - `content-strategy` (2.1.5)
    - `sales-enablement` (2.4.0)
    - `marketing-council` (1.0.0)
    - os dois arquivos transitivos `skills/ads/references/meta-decision-system.md` e `skills/ads/references/abm-playbook.md`
    - `LICENSE`
  - **ByteDance**, commit previsto `12c304f`, PR 9: `skills/public/newsletter-generation/SKILL.md`, `skills/public/deep-research/SKILL.md` e `LICENSE`.
  - **Fora do escopo:** a pasta `tools/` do Corey (CLIs e integrações de plataforma). Links absolutos para ela permanecem como URL externa.
- **Consequências:** atualizar o upstream é uma operação auditável e reversível. Os commits previstos são reconfirmados no momento do PR 1 (V-10).
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-03 — Uma única skill registrada no host

- **Contexto:** as descrições das skills upstream disputam ativação. Exemplos: `copywriting` dispara com "AI slop"; `social` com "LinkedIn post" e "Twitter thread"; `deep-research` se declara de uso geral para qualquer pesquisa web. Se fossem registradas como skills do host, pulariam o roteamento, os gates e o Brain.
- **Decisão:** só `skills/marketing-content-studio/SKILL.md` é registrada. O instalador a coloca em `.claude/skills/marketing-content-studio/`. Os `SKILL.md` em `vendor/` e `compiled/` são conteúdo carregado pelo Studio, não skills descobríveis.
- **Consequências:** o T-INSTALL (PR 3) confirma que só a skill do Studio aparece no host. Se o host descobrir `SKILL.md` aninhados, o sync aplica uma transformação declarada no lock para impedir a descoberta (V-04).
- **Estado:** Aceito, com verificação pendente (V-04)
- **Data:** 2026-11-02

## ADR-04 — X Content Brain: autoridade exclusiva sobre Yann no X

- **Contexto:** o Brain é o sistema do operador para conteúdo do Yann no X. Ele tem checkpoints humanos obrigatórios (escolha de ângulo e de estilo) e uma regra própria: o orquestrador dele é a sessão que conversa com o operador. Na leitura do `main` (commit `5cfa4b6`), há divergência entre o `main` e pacotes portáteis do Brain.
- **Decisão:**
  - **Rota:** Yann no X (reply, quote tweet, standalone) vai sempre ao Brain. Outras personas no X ficam com o Studio, salvo integração configurada.
  - **Fonte do handoff:** o `main` autenticado, com o SHA observado no início da execução.
  - **Registro:** `{job_id, route: brain, brain_ref: main@<SHA>, host, entrada, idioma}` e, na volta, o status no vocabulário do Brain e o texto final se houver `operator-approved`.
  - **Pacote portátil:** só por escolha explícita do operador, registrado como `brain_ref: portable@<hash>` com flag de divergência não verificada.
  - **Sem acesso ao `main`:** `BLOCKED` e diagnóstico. **Nunca** há fallback para a skill `social` do Corey.
  - O Studio não avalia o que o Brain produz e não copia conteúdo, voz, regras ou exemplos do Brain.
  - **Forma de integração**, decidida por teste no PR 7:
    - **A:** sessão independente do Brain;
    - **B:** Brain como subagente aninhado.

    B só é adotada se cumprir os três critérios: os papéis do Brain rodam como subagentes separados, os checkpoints chegam ao operador no meio da execução e o orquestrador do Brain fala com o operador sem intermediação do Studio. Caso contrário, A.
- **Consequências:** `integrations/x-content-brain.yaml` guarda apenas URL, referência de autenticação e política de ref. O resultado do experimento entra neste arquivo no PR 7.
- **Estado:** Aceito, com verificação pendente (V-07)
- **Data:** 2026-11-02

## ADR-05 — Marca, persona, job e fontes são objetos separados

- **Contexto:** as skills do Corey leem um arquivo global de contexto (`.agents/product-marketing.md`, inclusive a seção Learnings), e a skill `product-marketing` grava nele. Isso vazaria persona entre jobs e geraria aprendizado fora da governança.
- **Decisão:**
  - A **marca** define fatos, posicionamento, claims permitidos e proibições.
  - A **persona** define voz, idioma e registro.
  - O **job** define trabalho, escopo, canal e entregáveis.
  - As **fontes** sustentam fatos.
  - Por job, o Studio compila marca + persona + job no formato do `product-marketing` do Corey em `runs/<job>/.agents/product-marketing.md`, **somente leitura**.
  - Escritas upstream são interceptadas e redirecionadas para `runs/<job>/learning-candidates.md`, que alimenta PR: Learnings no contexto, `.agents/advisors/` (marketing-council) e `outputs/AAAA-MM-DD/` (lotes do ad-creative).
- **Consequências:**
  - Em hosts sem sistema de arquivos, o fallback é contexto virtual marcado no run ledger (POSTERIOR).
  - O perfil Zazmic é construído só a partir de material fornecido pelo operador (PR 8).
  - Golden ou voz do Yann nunca entram no Studio.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-06 — Três modos de fidelidade

- **Contexto:** formatos diferentes têm exigências factuais diferentes. Uma tradução não pode ganhar fato novo; uma newsletter precisa de fonte datada.
- **Decisão:**
  - **`strict-source`:** adaptação ou tradução. Não adiciona claim, exemplo, estatística, promessa ou implicação ausente do original. Caminho: intake → original → writer → verificação de fidelidade + reviewer → entrega. Sem brainstorm e sem pesquisa externa, salvo pedido explícito.
  - **`grounded-creative`:** ângulo e redação livres, sem fabricar fatos. Caminho: intake → estratégia → writer → critic ∥ reviewer → entrega. Pesquisa só para claims materiais novos.
  - **`research-backed`:** afirmações com fonte, autoria, data e nível de leitura registrados. Caminho: intake → pesquisa + ledger + verificação → estratégia → writer → critic ∥ reviewer → entrega. Se a pesquisa muda a premissa, volta à estratégia.
- **Consequências:** o modo é campo obrigatório do briefing (`schemas/job.schema.json`, PR 5). Os gates variam por modo (ADR-11).
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-07 — Agentes independentes e sem autoavaliação

- **Contexto:** no Brain, mais de dez candidatos aprovados pela autocrítica do mesmo contexto foram rejeitados pelo operador entre 16 e 22/10/2026, e várias regressões registram PASS do Critic seguido de rejeição humana.
- **Decisão:**
  - Cada papel roda como execução separada, com contexto isolado e IDs rastreáveis de autoria e avaliação.
  - O Writer não aprova o próprio texto.
  - Critic e Reviewer são **somente leitura** e devolvem veredito com evidência, nunca texto substituto.
  - O Strategist não aprova o próprio ângulo: a checagem de estratégia é feita pelo Critic numa chamada separada com rubrica de estratégia.
  - O Researcher não certifica a própria fonte: a checagem de evidência é feita pelo Reviewer.
  - Sem subagentes reais no host, o job multiagente fica `BLOCKED`; a separação nunca é simulada num contexto só.
- **Vocabulário de status:**
  - **andamento do job:** `ROUTED`, `IN_PROGRESS`, `BLOCKED`, `ELIGIBLE`, `CLOSED`;
  - **decisão editorial:** `candidate`, `critic-pass`, `operator-approved`, `published-confirmed`, `unknown`.
- **Consequências:** nenhum PASS com avaliador igual ao autor (T03) e nenhum `critic-pass` em host sem subagentes (T04).
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-08 — Orquestrador no modelo mais forte, sem produzir nem avaliar conteúdo

- **Contexto:** o operador exige o modelo mais capaz no topo da orquestração. O orquestrador toma decisões não triviais, mas não pode virar avaliador do próprio fluxo.
- **Decisão:**
  - O orquestrador usa o modelo mais capaz disponível, escolhido pelo operador.
  - **Ficam no código, sem chamada de modelo:** tabela de rota, validação de schema, contagens e limites de canal, contabilidade de orçamento, assinatura de não-progresso e transições inequívocas.
  - **Ficam com o orquestrador:** decomposição de campanha, rota ambígua, escolha da próxima estratégia, divergência processual entre pareceres, decisão de escalar e mensagem final ao operador.
  - Ele recebe vereditos estruturados, não artefatos completos.
  - Não redige copy, não reescreve feedback editorial e **nunca declara PASS com algum hard gate em FAIL ou UNVERIFIED**.
- **Consequências:** a instrução do papel fica em `agents/orchestrator.md` (PR 3) e a máquina de estados em `policies/editorial-loop.md` (PR 5).
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-09 — Critic: execução independente, mesmo modelo permitido

- **Contexto:** isolamento de contexto é o requisito mínimo de independência. Modelos de famílias diferentes podem reduzir erro correlacionado, mas isso não foi medido.
- **Decisão:**
  - Writer e Critic podem usar o mesmo modelo (Sonnet, inicialmente) em execuções independentes.
  - O uso de outra família no Critic é avaliado depois, com base no T15 (falso PASS e falso FAIL por modalidade).
  - Não se presume que isolamento elimina correlação de erro: isso é medido.
- **Consequências:** até haver baseline do T15, as entregas saem com a flag "falso PASS não medido".
- **Estado:** Aceito, com verificação pendente (V-08)
- **Data:** 2026-11-02

## ADR-10 — Loop editorial autônomo dentro de orçamento

- **Contexto:** o operador quer um loop que recomece a partir da etapa causadora em caso de reprovação, sem pedir autorização a cada retry e sem cair em SKIP por falta de criatividade. O Brain registrou um loop de seis rodadas e cerca de 50 minutos, considerado longo demais.
- **Decisão:**
  - **Fluxo:** BRIEF → BRAINSTORM → DECISÃO → CRIAÇÃO → CRITIC ∥ REVIEWER → DECISÃO → ENTREGA.
  - **Retorno pela causa:**
    - problema de texto → Writer;
    - problema de estratégia → Strategist;
    - problema de fonte → Researcher, ou remoção do claim;
    - conflito de briefing → escalonamento;
    - capacidade ausente → `BLOCKED`.
  - **Troca de estratégia:** duas tentativas improdutivas no mesmo ângulo trocam a estratégia; não encerram o trabalho. O ângulo novo precisa ser estruturalmente diferente, o que é verificado pela checagem de estratégia.
  - **Não-progresso:** a mesma assinatura (gate + `issue_code` + conjunto de claims) duas vezes seguidas esgota o ângulo.
  - **Orçamento global obrigatório e configurável:** `max_total_attempts`, `max_wall_time`, `max_cost`.
  - **Escalonamento ao operador só em quatro casos:** bloqueio real, decisão subjetiva relevante, orçamento esgotado, ângulos distintos esgotados. Ao escalar, o sistema mostra diagnóstico, melhor candidato marcado e opções.
  - **Nenhum PASS fabricado.** Aprovação para publicação e promoção de aprendizados são do operador.
- **Valores iniciais (hipóteses, não verdades empíricas; calibrados no PR 8):**

  | Perfil | Drafts por ângulo | Ângulos distintos | Tempo máximo |
  |---|---|---|---|
  | Copy curto (LinkedIn, anúncio, e-mail) | 2 | 3 | 15 min |
  | `strict-source` | 3 | 1 | 10 min |
  | Newsletter | 2 por item | 2 por seção | 45 min |

  O teto de custo será fixado em p90 × 1,5 após medir os 10 primeiros jobs de cada perfil.
- **Consequências:** a máquina de estados fica em `policies/editorial-loop.md` (PR 5). Testes T11, T12 e T13.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-11 — Proveniência por claim

- **Contexto:** a regra de "toda fonte lida por inteiro" seria excessiva como gate universal. Uma tradução usa só o texto fornecido; copy de marca pode usar fatos aprovados da marca.
- **Decisão:**
  - A verificação acontece no nível do claim. Categorias de origem: `user-provided`, `brand-approved`, `primary-verified`, `secondary-attributed`, `unverified`.
  - Claim material sem sustentação falha ou é removido. Frase criativa sem afirmação factual não precisa de citação.
  - Em `research-backed`, link, autoria, data e nível de leitura são sempre registrados. Snippet sozinho nunca autoriza benchmark ou promessa.
  - O Writer trabalha a partir do ledger, não de páginas web brutas, e conteúdo externo é sempre tratado como dado, nunca como instrução.
- **Consequências:** schema em `schemas/source-ledger.schema.json` (PR 5); política em `policies/source-fidelity.md` (PR 6). Testes T09 e T10.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-12 — Claude Code como primeiro host, não o único

- **Contexto:** o chat do claude.ai não oferece ferramenta de subagente. O Claude Code oferece subagentes com contexto próprio e modelo por subagente. O operador quer controlar gasto e executar em ambiente com separação real de papéis.
- **Decisão:**
  - O Claude Code é o primeiro host de execução.
  - A sessão principal é o orquestrador, com o modelo mais forte escolhido pelo operador.
  - Strategist, Writer, Critic, Reviewer (e Researcher, no PR 9) são subagentes nomeados, com modelos econômicos definidos em `hosts/claude-code/host.yaml`: Sonnet inicialmente e Haiku onde a medição justificar.
  - O claude.ai e o ChatGPT ficam para planejamento, revisão e debate.
  - O MVP usa apenas modelos Claude. Outros fornecedores dependem de um runtime fino, que exige ADR próprio (POSTERIOR).
- **Consequências:** tudo que é específico do host fica em `hosts/claude-code/`. Os prompts de papel em `agents/` são neutros em relação ao host.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-13 — Aprendizado só por revisão e PR

- **Contexto:** o Brain mostrou que regras acumuladas como patches datados em vários arquivos acabam se contradizendo (por exemplo, "recomendar SKIP" num arquivo e "SKIP é só sugestão" em outro). As skills do Corey tentam gravar aprendizados globais.
- **Decisão:**
  - Correções são classificadas e promovidas só por PR aprovado pelo operador.
  - Cada regra tem um lugar canônico. Promover uma correção edita esse lugar e marca o texto superado no mesmo PR.
  - Nenhum write-back upstream é aceito automaticamente (ver ADR-05).
  - O formato de regressão segue o padrão contrastivo do Brain: candidato, vereditos de Critic e Reviewer, veredito do operador nas palavras dele e teste derivado.
- **Consequências:** política em `policies/learning-governance.md` (PR 5). `examples/` nasce só com o primeiro item `operator-approved`.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-14 — Repositório público, dados de execução fora do git

- **Contexto:** o Studio é um projeto pessoal do operador, não um projeto empresarial. O repositório `julianobruxo/marketing-ai-studio` foi criado público por escolha do operador. O Studio vai lidar com briefings, marcas e materiais de terceiros.
- **Decisão:**
  - O repositório é público.
  - Ficam fora do git por padrão: `runs/`, briefings de clientes, segredos e credenciais.
  - Ledgers de execução são locais; persistir algo exige opt-in do operador.
  - Material de marcas de terceiros (por exemplo, a Zazmic) só é commitado se já for público ou se houver liberação explícita. Versões rejeitadas, documentos internos de marca e materiais não publicados ficam fora do git.
  - O Studio referencia o X Content Brain só pela URL e por decisões de arquitetura; nenhum conteúdo do Brain é copiado (ADR-04).
- **Consequências:**
  - `.gitignore` do PR 0.
  - Exemplos e fixtures commitados são sintéticos ou material público ou liberado.
  - O local do material não público usado no perfil Zazmic e nas regressões é definido no PR 8 (V-11).
  - O conteúdo próprio do Studio fica sem licença de uso até o operador decidir uma.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-15 — Ordem de entrega e definição de MVP funcional

- **Contexto:** o operador quer PRs pequenos e verificáveis, e um produto que combine Corey e ByteDance desde a primeira versão declarada funcional.
- **Decisão:**

  | PR | Conteúdo | Aceite |
  |---|---|---|
  | 0 | documentação e decisões | aprovação do operador |
  | 1 | vendor do Corey + lock + `vendor.py sync/verify` | T14 |
  | 2 | overlays das 6 skills roteadas + `compile` | T-COMPILE |
  | 3 | `agents/`, `hosts/claude-code/`, `install_host.py` | T-HOOK, T-PATH, T-ISO-W, T-ISO-O, T-SCOPE, T-RO, T-WRITE, T-INSTALL etapa 1 |
  | 4 | skill de entrada, `MAP`, `catalog/` | T01 |
  | 5 | `schemas/`, policies de independência, loop e learning | T03, T04, T12, T13 |
  | 6 | `strict-source`, `copy`, perfis, contexto por job, policies de fonte e marca | T05, T06, T09, T11, T-INSTALL etapa 2 |
  | 7 | handoff do Brain + experimento A/B | T02 |
  | 8 | perfil Zazmic, regressões, 10 jobs reais | T15, T16 → **marco de copy** |
  | 9 | ByteDance: vendor, overlays, `researcher`, `newsletter` | T07, T08, T10 → **MVP funcional** |
  | 10 | campanha | coerência entre peças (POSTERIOR) |

  O Studio só é declarado funcional ao fim do PR 9, com Corey, ByteDance, handoff ao Brain, loop multiagente com avaliação independente e marcas/personas configuráveis.
- **Consequências:**
  - O T-INSTALL tem duas etapas. No PR 3 cobre instalação e descoberta. A execução de um job de fixture só é possível a partir do PR 6, quando existem entrada, schemas e o primeiro workflow.
  - Cada PR vira um prompt para o agente de código do operador e só é implementado depois da aprovação dele.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-16 — Precedência canônica de instruções

- **Contexto:** durante o debate surgiram duas ordens de precedência divergentes. O Brain mostrou o custo de manter a mesma regra em mais de um lugar.
- **Decisão:** ordem única, da mais alta para a mais baixa:
  1. Lei, segurança, direitos, autorização e restrições da plataforma.
  2. Hard gates do Studio e contrato de independência.
  3. Briefing explícito do operador (modo de fidelidade, fontes, canal, entregáveis).
  4. Política aprovada da marca. Um pedido vago não a revoga; override só explícito, registrado e onde a política permitir.
  5. Persona e voz.
  6. Convenções do canal e do formato.
  7. Padrões das skills upstream, adaptados por overlays com proveniência.

  Duas proibições valem em qualquer nível: nenhum fato é adicionado para obedecer a um estilo, e a persona não autoriza criar benchmarks, clientes, depoimentos, resultados ou posições institucionais não fornecidos.
- **Consequências:** o lugar canônico passa a ser `policies/brand-persona-separation.md` no PR 6. Até lá, este ADR é a fonte. Nenhum outro arquivo repete a ordem.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-17 — Compilado como único artefato derivado

- **Contexto:** era preciso adaptar as skills upstream sem fork e sem duas estratégias de manutenção (Corey e ByteDance).
- **Decisão:**
  - **Overlays** em `overlays/<fonte>/<skill>.md` contêm só operações declarativas sobre âncoras do original: `substituir-seção`, `acrescentar-após`, `desativar`, `vincular-contexto`.
  - **Compilação:** `scripts/vendor.py compile` aplica o overlay de forma determinística e grava `compiled/<fonte>/<skill>.md`, preservando frontmatter válido e referências, com cabeçalho de origem: repo, SHA, versão, hash do overlay, copyright e "MIT, ver `vendor/<fonte>/LICENSE`".
  - O orquestrador carrega o compilado, nunca vendor e overlay lado a lado.
  - O compilado é **gerado e commitado** para revisão de diff, e nunca é editado à mão.
- **Consequências:** a mesma regra vale para Corey (PR 2) e ByteDance (PR 9). Uma âncora removida upstream faz o `verify` falhar no PR de sync. Teste T-COMPILE.
- **Estado:** Aceito
- **Data:** 2026-11-02

## ADR-18 — Enforcement de permissões no host, em três camadas

- **Contexto:** `tools: Write` não restringe caminho. A documentação do Claude Code indica que hooks recebem `agent_id` e `agent_type` dentro de subagentes, e que uma negação por hook PreToolUse prevalece sobre o modo de permissão. Um relato de bug em versão anterior indicou que hooks da sessão pai não disparavam em chamadas de subagentes, então a eficácia precisa ser demonstrada na versão instalada.
- **Decisão:**
  1. **Allowlist de ferramentas por papel:**
     - Writer: `Read` e `Write`;
     - Critic, Reviewer e Strategist: só `Read`;
     - Researcher (PR 9): `Read`, `WebSearch`, `WebFetch`;
     - nenhum subagente recebe `Bash` nem `Agent`.
  2. **Regras de permissão** no `settings.json` gerado: `deny` com `Edit(...)` para `vendor/**`, `compiled/**`, `provenance/**`, `policies/**` e `profiles/**`.
  3. **Hook PreToolUse** (`hosts/claude-code/guard.py`) sobre `Write|Edit|NotebookEdit|Bash|Read|Agent`:
     - decide por `agent_type`: o Writer só escreve em `runs/<job>/drafts/`; Critic e Reviewer só leem `runs/<job>/eval-pack/`, `compiled/` e o contexto compilado do job; a sessão principal escreve ledger e vereditos em `runs/<job>/` e nunca em `drafts/`;
     - registra **toda tentativa** (`agent_id`, `agent_type`, ferramenta, alvo, decisão) em `runs/<job>/tool-log.jsonl`;
     - **canonicaliza caminhos antes de decidir:** resolve relativos e symlinks, nega `../` que escape do diretório autorizado, nega symlink que aponte para fora e nega caminho absoluto fora do escopo (requisito de implementação do PR 3).
  - **Env do projeto:** `CLAUDE_CODE_FORK_SUBAGENT=0` e `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`. A profundidade é a segunda camada; a primeira é a ausência da ferramenta `Agent`.
  - **Entrada de Critic e Reviewer:** `runs/<job>/eval-pack/`, montado pelo orquestrador com briefing, candidato e ledger. Rascunhos e notas do Writer nunca entram.
- **Consequências:**
  - Testes T-HOOK, T-PATH, T-ISO-W, T-ISO-O, T-SCOPE, T-RO e T-WRITE no PR 3.
  - Recusa por permissão exige a tentativa registrada no log. Recusa por ausência de ferramenta é provada pela configuração gerada mais a ausência de efeito.
  - No T-ISO, os canários ficam só no contexto privado de cada agente. Se um canário aparecer em material compartilhado (briefing, candidato, eval-pack), o teste é inválido, não reprovado.
  - Se o hook não disparar dentro de subagentes na versão instalada, a implementação para no PR 3 até haver alternativa (sandbox ou outra forma de enforcement).
  - **Risco residual aceito:** o `Bash` da sessão principal é registrado no log, mas não é confinado por caminho.
- **Estado:** Aceito, com verificação pendente (V-01, V-02, V-03, V-05)
- **Data:** 2026-11-02

---

## Verificações pendentes

São verificações de implementação, não decisões. Nenhuma foi executada.

| ID | Verificação | Onde | ADR |
|---|---|---|---|
| V-01 | Hooks PreToolUse disparam dentro de subagentes na versão instalada do Claude Code | PR 3 · T-HOOK | 18 |
| V-02 | `CLAUDE_CODE_FORK_SUBAGENT=0` elimina fork; subagentes não veem o histórico do orquestrador | PR 3 · T-ISO-O | 18 |
| V-03 | Sem a ferramenta `Agent`, nenhum subagente consegue criar outro; profundidade 1 efetiva | PR 3 · T-RO | 18 |
| V-04 | A skill é descoberta em `.claude/skills/marketing-content-studio/` e nenhum `SKILL.md` de `vendor/` ou `compiled/` aparece no host | PR 3 · T-INSTALL | 03 |
| V-05 | O guard resiste a caminhos relativos, `../`, symlinks e caminhos absolutos fora do escopo | PR 3 · T-PATH | 18 |
| V-06 | O teto nativo em dólar (`--max-budget-usd`) vale para a forma de cobrança do operador; se não valer, o orçamento fica só nos contadores do Studio | PR 5 | 10 |
| V-07 | Experimento A/B do handoff ao Brain, pelos três critérios do ADR-04 | PR 7 | 04 |
| V-08 | Baseline de falso PASS e falso FAIL do Critic por modalidade | PR 8 · T15 | 09 |
| V-09 | Valores iniciais de orçamento do ADR-10 confirmados ou ajustados com 10 jobs reais por perfil | PR 8 | 10 |
| V-10 | Commits previstos (`88c79f6` no Corey, `12c304f` na ByteDance) reconfirmados ou atualizados no momento da importação | PR 1 · PR 9 | 02 |
| V-11 | Local do material não público de marcas (perfil Zazmic, versões rejeitadas) fora do git, sem prejudicar os testes | PR 8 | 14 |
