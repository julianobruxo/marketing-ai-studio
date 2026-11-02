# Parâmetros do Critic

O que o Critic avalia, com base em quê e até onde isso vale. O texto que o modelo lê é `agents/critic.md`, que entra no `AGENTS.md`; este arquivo é a explicação para o operador.

## Como ele decide

O Critic devolve um status por gate: `PASS`, `FAIL`, `UNVERIFIED` ou `N/A`. O candidato só vira `critic-pass` com todos em `PASS` ou `N/A`. Qualquer `FAIL` ou `UNVERIFIED` começa uma nova rodada, até 3. Um `FAIL` precisa da linha citada e do critério violado; preferência sem critério nomeado vira observação.

| Gate | Pergunta | Base |
|---|---|---|
| `brief` | Cumpre objetivo, público, canal, formato, tamanho e suas instruções? | O seu pedido |
| `voice` | Soa como a persona e a marca pedem? | Só o que estiver escrito no contexto do job. Sem instrução de voz, fica `N/A` |
| `quality` | Passa nos critérios de escrita? | Skills do Corey Haines e da DeerFlow (abaixo) |
| `facts` | Cada fato tem fonte, e a fonte diz isso mesmo? | Seus dados, o contexto do job e as notas de pesquisa. Sem trecho citado, ou só de snippet, fica `UNVERIFIED` |
| `fidelity` | Na tradução, nada foi acrescentado? | O texto original. Fora do modo `strict-source`, fica `N/A` |

## De onde vêm os critérios de `quality`

| Critério | Vale para | Fonte |
|---|---|---|
| Marcas de IA: contraste revelador, lista de negações, frase arrastada, pergunta autorrespondida, revelação com dois-pontos, frases prontas, travessão em texto curto | Tudo | `copy-editing` (AI-Tell Check) e `copywriting` (No AI Tells), do Corey |
| Limites: um fragmento e uma lista de três por seção; palavras vazias como *seamless* e *robust* | Tudo | `copy-editing` e `copywriting` |
| Sete varreduras: clareza, voz, "e daí?", prova, especificidade, emoção, risco zero | Tudo | `copy-editing` (Seven Sweeps) |
| *Broetry*, isca de engajamento, vulnerabilidade fabricada, emoji como bullet; LinkedIn com até 3.000 caracteres e cerca de 210 antes do "ver mais" | `social-post` | `social` e `references/platform-limits.md` |
| Teste de cada linha: dá para imaginar, dá para provar, um concorrente não escreveria igual | `copy-page`, `article` | `copywriting` (Drafting Protocol) |
| Especificações da plataforma, nome exato do produto, hipótese que pode perder | `ad` | `ad-creative` |
| Um e-mail, um trabalho; valor antes do pedido; assunto que se sustenta sozinho | `email` | `emails` |
| Checklist de fontes, datas, duplicatas, equilíbrio e fechamento | `newsletter` | `newsletter-generation`, da DeerFlow |

## O que o Studio acrescentou

Estas regras não vêm das skills; são decisões do Studio (ADR-20):

- `voice` fica `N/A` quando não há instrução de voz, para não gastar rodadas sem chance de passar.
- Preferência sem critério nomeado não reprova.
- Em outro idioma, cada marca de IA é aplicada pela forma, não pelas palavras.
- Uma varredura só reprova se o problema impede a peça de cumprir o brief.
- Na tradução, um padrão que já estava no original não reprova.
- O painel de especialistas só roda se o brief pedir, e as notas dele nunca aprovam nada sozinhas.

## Limites conhecidos

- **Não há régua calibrada.** Os critérios são regras de escrita, não uma medida contra textos aprovados por você. A taxa de falso PASS e de falso FAIL nunca foi medida (V-08).
- **A voz é tão boa quanto o seu pedido.** Sem exemplos ou perfil, o Critic não sabe como a Zazmic soa e não avalia isso.
- **As listas foram escritas para inglês.** Para PT-BR, o Critic adapta a forma; não existe uma lista própria de marcas de IA em português.
- **O Critic não abre a web.** Ele confere fatos pelo trecho citado nas notas, então não detecta um trecho inventado pelo Strategist.
