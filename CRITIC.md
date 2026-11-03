# Parâmetros do Critic

O que o Critic avalia, com base em quê e até onde isso vale. O texto que o modelo lê é `agents/critic.md`, que entra no `AGENTS.md`; este arquivo é a explicação para o operador.

## Como ele decide

Primeiro ele identifica formato, público, canal e objetivo. Depois avalia sete gates, com o raciocínio antes do estilo.

| Gate | Pergunta | Base |
|---|---|---|
| `brief` | Cumpre objetivo, público, canal, formato, tamanho e suas instruções? | O seu pedido |
| `editorial` | O leitor tem motivo para se importar, e o raciocínio se sustenta? | Padrões extraídos de revisões editoriais humanas |
| `facts` | Cada fato tem fonte, número tem universo, dados são consistentes? | Seus dados e as notas de pesquisa |
| `voice` | Soa como a persona e a marca pedem? | Só o que estiver escrito no contexto do job |
| `quality` | A linguagem é natural e segue as regras do canal? | Skills do Corey Haines e da DeerFlow, como sinais |
| `revision` | A revisão perdeu clareza, personalidade, especificidade ou força comercial? | A versão anterior e a lista `keep` |
| `fidelity` | Na tradução, nada foi acrescentado? | O texto original |

`editorial` cobre relevância, valor de negócio, gancho, foco, lógica, referências, uma ideia por frase, resolução, posicionamento, CTA e contenção. **Também decide se o conteúdo merece a atenção do público no canal escolhido:** uma lista de conselhos corretos e úteis não basta quando falta uma tese, um diferencial ou uma razão concreta para continuar lendo. Checklists específicos e explicitamente pedidos podem passar; não há exigência universal de polêmica, dramatização ou clickbait.

## O que o resultado significa

| Decisão | Significado | O que acontece |
|---|---|---|
| `KEEP AS IS` | Nada relevante a mudar | Vai para você |
| `IMPROVE` | Só achados `material` | Passa e vai para você com as observações |
| `REVISE` | Há achado `blocking`, inclusive falha editorial fundamental, ou fato sem verificação | Reinicia todo o fluxo configurado em nova rodada, até 3 |

- **Severidade:** só `blocking` reprova. `material` melhora de forma clara. `polish` é preferência.
- **Correção:** o Critic diz o que precisa mudar, nunca a redação nova. Cortar é uma correção válida.
- **`keep`:** ele lista os trechos que já funcionam. O Writer os mantém, salvo correção factual, achado bloqueante ou incompatibilidade concreta com a nova abordagem. Quando remover ou reescrever uma linha protegida, devolve `keep_exceptions` com o trecho original, a ação, a causa e uma justificativa curta. O orquestrador passa ao Critic somente essa anotação e o resumo da abordagem escolhida. O Critic valida a necessidade da exceção **de forma independente**; justificativa vaga não libera a mudança.
- **Marcas de IA:** são sinais a investigar, não proibições. Só bloqueiam quando substituem conteúdo, se acumulam ou tiram a confiança do leitor.

## Quem decide se há nova rodada

O Critic é o gate de passagem. Com todos os gates em `PASS` ou `N/A`, libera um `critic-pass` **e a aprovação final continua humana**. Com qualquer `FAIL` ou `UNVERIFIED`, o orquestrador recomeça a **rodada inteira configurada**, lançando novos subagentes: Strategist (quando a intent o utiliza), Writer e Critic. A causa `approach | writing | facts` orienta a solução, mas **não pula o Strategist**. Falta de dado obrigatório do operador pausa o fluxo sem gastar uma rodada.

A própria avaliação de interesse editorial é contextual: um post para LinkedIn deve conquistar atenção, defender uma ideia e ter payoff; um tutorial ou checklist pedido explicitamente pode priorizar clareza e utilidade. Não basta passar em gramática, briefing e fatos.

## Como medir

`scripts/eval_critic.py` monta um pacote cego, pontua os vereditos sem usar modelo e compara duas versões do Critic sobre os mesmos casos. Veredito, categoria, diagnóstico, severidade e preservação são medidos separadamente. Os casos públicos ficam em `tests/critic/` e são fictícios. Casos reais ficam fora do repositório.

## Limites conhecidos

- **Ainda não reproduz uma revisão humana.** Em casos reais fora do ajuste, ele não chegou ao mesmo diagnóstico da revisora. Veja `tests/critic/results/README.md`.
- **Calibração pequena.** A medição mostra direção, não uma taxa de erro. Há poucos exemplos positivos explícitos.
- **Fatos em excesso.** Com dados de entrada escassos, ele pode marcar `UNVERIFIED` em vários trechos, o que consome rodadas.
- **A voz é tão boa quanto o seu pedido.** Sem exemplos ou perfil, o Critic não sabe como a marca soa.
- **Sinais escritos para inglês.** Em PT-BR, ele adapta a forma; não há uma lista própria em português.
- **O Critic não abre a web.** Ele confere fatos pelo trecho citado e só compara o CTA com a página de destino se o conteúdo dela vier no pedido.
