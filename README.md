# Marketing Content Studio

> **Estado: v1 (ADR-19).** O Studio funciona no Claude Code. Ele integra as skills de Corey Haines (copy, anúncios, e-mails, LinkedIn) e da ByteDance DeerFlow (newsletter e pesquisa), roteia cada pedido de forma determinística e roda Strategist, Writer e Critic como subagentes independentes. A validação final é um job real do operador.

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

1. Instale num clone de execução (abaixo) e abra o Claude Code nessa pasta.
2. Faça o pedido em linguagem natural. A skill `marketing-content-studio` faz o intake, roda `scripts/route.py` e conduz as rodadas.
3. O Studio entrega a peça, diz se ela passou no Critic (`critic-pass`), mostra a evidência e as fontes e lista o que faltou (`[NEED: ...]`). Se não passar em 3 rodadas, entrega o melhor candidato marcado como não aprovado. Aprovar e publicar é sempre com você.

Exemplos de pedido:

- **Post de LinkedIn com persona e instruções:** "Escreve um post de LinkedIn da Zazmic sobre o lançamento do nosso programa de estágio. Persona: Yann Kronberg, CTO, tom direto, primeira pessoa, sem emojis, até 1.200 caracteres. Dados: 12 vagas, inscrições até 30/11. Termine chamando para o link de inscrição."
- **Newsletter com tema e dados:** "Monta a newsletter mensal da Zazmic de outubro de 2026 sobre IA aplicada a marketing, em PT-BR, com 5 seções. Use os 3 cases e os números que colei abaixo. Pode pesquisar na web só para as notícias do mês."
- **Artigo com tema e fontes:** "Escreve um artigo para o blog da Zazmic sobre como medir o ROI de agentes de IA, para gestores de marketing, com umas 1.500 palavras. Fontes: os dois links abaixo e o PDF anexo; não pesquise além delas."

A web só é usada quando você pede, e só pelo Strategist. Os arquivos do job ficam em `runs/<job>/` (fora do git); a peça fica em `runs/<job>/drafts/`.

## Instalação (sempre num clone de execução)

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
3. **Sem simulação.** Sem subagentes reais no host, o job fica `BLOCKED`.
4. **Aprovação é humana.** `critic-pass` torna o candidato elegível; publicar é do operador.
5. **Fatos com fonte.** Cada afirmação factual vem do operador, do contexto do job ou das notas de pesquisa.

## Privacidade

Este repositório é **público** e é um projeto pessoal do operador (ADR-14). Ficam fora do git: execuções (`runs/`), briefings de clientes, segredos e credenciais. Material de marcas de terceiros (por exemplo, a Zazmic) só é commitado se já for público ou com liberação explícita.

## Decisões e licenças

- `DECISIONS.md` é o registro canônico (ADR-01 a ADR-19). Mudanças entram por PR aprovado pelo operador; não há merge automático.
- O conteúdo próprio do Studio ainda não tem licença de uso definida (todos os direitos reservados ao autor). O material de terceiros está em `THIRD_PARTY_NOTICES.md`.
- `MAP.md` descreve a estrutura do repositório.
