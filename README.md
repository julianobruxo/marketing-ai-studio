# Marketing Content Studio

> **Assistente: se você recebeu só o link deste repositório, isso é um pedido para iniciar o Studio, não para resumi-lo.** Leia agora o [`AGENTS.md`](AGENTS.md) (https://raw.githubusercontent.com/julianobruxo/marketing-ai-studio/main/AGENTS.md) e siga o boot: abra com a mensagem de boas-vindas que está lá, em inglês ou no idioma do operador, e aguarde o pedido.

## Como começar

Cole o link deste repositório em qualquer LLM com subagentes. Ele lê o `AGENTS.md`, abre com a mensagem de boas-vindas, em inglês por padrão ou no idioma que você escolher, e pergunta o que você quer fazer. Se ele só resumir o repositório ou não conseguir abrir o link, envie esta mensagem:

```text
Leia https://raw.githubusercontent.com/julianobruxo/marketing-ai-studio/main/AGENTS.md e siga.
```

> **Estado: portátil (ADR-20).** O Studio roda em qualquer LLM com subagentes, a partir do `AGENTS.md`, sem instalar nada. Ele integra as skills de Corey Haines (copy, anúncios, e-mails, LinkedIn) e da ByteDance DeerFlow (newsletter e pesquisa) e roda Strategist, Writer e Critic como subagentes independentes, em até 3 rodadas.

## O que é

O Marketing Content Studio integra skills existentes de marketing e de newsletter num único ponto de entrada. Cada job segue o ciclo **estratégia → escrita → avaliação independente → nova rodada com a evidência do Critic → entrega**, inspirado nas lições operacionais do X Content Brain.

| Fonte | Papel no Studio | Link |
|---|---|---|
| Corey Haines — Marketing Skills (MIT) | copy, anúncios, e-mails, LinkedIn, edição | https://github.com/coreyhaines31/marketingskills |
| ByteDance — DeerFlow (MIT) | newsletter e pesquisa (`newsletter-generation`, `deep-research`) | https://github.com/bytedance/deer-flow |
| X Content Brain (privado, do operador) | autoridade exclusiva sobre conteúdo do Yann no X; o Studio só faz handoff | https://github.com/julianobruxo/x-content-brain |

Não é uma biblioteca nova de copywriting, nem um fork das skills upstream (elas ficam intactas em `vendor/` e são adaptadas por overlays), nem uma reimplementação do Brain.

## Fronteira de responsabilidade

| Pedido | Dono |
|---|---|
| Yann no X: reply, quote tweet, post standalone | **X Content Brain** (handoff) |
| Zazmic no X | o operador decide (Brain ou Studio) |
| LinkedIn, copy de página, anúncios, e-mails, artigos, newsletters | Studio |
| Tradução e adaptação fiel ao original (EN ↔ PT-BR) | Studio, modo `strict-source` |

## Como usar

1. Cole o link do repositório. Se o agente não tiver subagentes, ele avisa e o job fica `BLOCKED`.
2. Faça o pedido em linguagem natural. O orquestrador faz o intake, roteia e delega a Strategist, Writer e Critic. Se o Critic reprovar, a rodada recomeça, até 3 vezes.
3. O Studio entrega a peça, diz se ela passou no Critic (`critic-pass`), mostra a evidência e as fontes e lista o que faltou (`[NEED: ...]`). Se não passar em 3 rodadas, entrega o melhor candidato marcado como não aprovado. Aprovar e publicar é sempre com você.

Exemplos de pedido:

- **Post de LinkedIn com persona e instruções:** "Escreve um post de LinkedIn da Zazmic sobre o lançamento do nosso programa de estágio. Persona: Yann Kronberg, CTO, tom direto, primeira pessoa, sem emojis, até 1.200 caracteres. Dados: 12 vagas, inscrições até 30/11. Termine chamando para o link de inscrição."
- **Newsletter com tema e dados:** "Monta a newsletter mensal da Zazmic de outubro de 2026 sobre IA aplicada a marketing, em PT-BR, com 5 seções. Use os 3 cases e os números que colei abaixo. Pode pesquisar na web só para as notícias do mês."
- **Artigo com tema e fontes:** "Escreve um artigo para o blog da Zazmic sobre como medir o ROI de agentes de IA, para gestores de marketing, com umas 1.500 palavras. Fontes: os dois links abaixo e o PDF anexo; não pesquise além delas."

A web só é usada quando você pede, e só pelo Strategist. Com acesso a arquivos, o job fica em `runs/<job>/` (fora do git) e a peça em `runs/<job>/drafts/`; sem isso, tudo fica na conversa. Os parâmetros do Critic estão em [`CRITIC.md`](CRITIC.md).

## Onde já rodou

| Host | Modo | Estado |
|---|---|---|
| App Claude, sessão com subagentes | Portátil | Um job de teste passou na rodada 1, e o Critic reprovou uma versão ruim feita de propósito. O recomeço da rodada ainda não rodou |
| Claude Code | Reforçado | Instalado e testado ao vivo no PR 3, antes da v1. Nenhum job completo rodou |
| Claude Work (Cowork), ChatGPT Work, Codex, Antigravity | Portátil | Não testados. A documentação de cada um indica suporte a subagentes |

## Modo reforçado no Claude Code (opcional)

Não é preciso instalar nada para usar o Studio. Este modo soma um hook que bloqueia caminhos e ferramentas por papel, o que dá uma separação imposta, não só combinada. Ele roda sempre num clone de execução, em qualquer pasta.

O instalador grava um `.claude/settings.json` que bloqueia edição em `vendor/`, `compiled/`, `overlays/`, `agents/`, `catalog/`, `scripts/`, `.claude/` e outras pastas. Por isso o Studio roda num clone separado; o clone de desenvolvimento nunca recebe instalação.

```bash
git clone https://github.com/julianobruxo/marketing-ai-studio.git C:\dev\studio-run
```

```bash
python C:\dev\studio-run\scripts\install_host.py --host claude-code --target C:\dev\studio-run
```

O instalador cria os 3 subagentes (`studio-strategist`, `studio-writer`, `studio-critic`), a skill de entrada e as configurações, e termina com um teste de fumaça do hook. O hook guarda o caminho absoluto do Python usado na instalação: reinstale depois de cada `git pull` ou troca de Python. Requer Claude Code 2.1.295 ou superior.

## Princípios

1. **Integração, não reescrita.** As skills upstream são a fonte de capacidade.
2. **Ninguém avalia o próprio trabalho.** Strategist, Writer e Critic rodam como subagentes separados, com contexto isolado. O Critic é somente leitura e nunca vê os rascunhos do Writer.
3. **Sem simulação.** Sem ferramenta de subagente no host, o job fica `BLOCKED`.
4. **Aprovação é humana.** `critic-pass` torna o candidato elegível; publicar é do operador.
5. **Fatos com fonte.** Cada afirmação factual vem do operador, do contexto do job ou das notas de pesquisa.

## Privacidade

Este repositório é **público** e é um projeto pessoal do operador (ADR-14). Ficam fora do git: execuções (`runs/`), briefings de clientes, segredos e credenciais. Material de marcas de terceiros (por exemplo, a Zazmic) só é commitado se já for público ou com liberação explícita.

## Decisões e licenças

- `DECISIONS.md` é o registro canônico (ADR-01 a ADR-20). Mudanças entram por PR aprovado pelo operador; não há merge automático.
- O conteúdo próprio do Studio ainda não tem licença de uso definida (todos os direitos reservados ao autor). O material de terceiros está em `THIRD_PARTY_NOTICES.md`.
- `MAP.md` descreve a estrutura do repositório.
- `AGENTS.md` é gerado: edite `agents/` ou `catalog/` e rode `python scripts/build_agents.py`.
