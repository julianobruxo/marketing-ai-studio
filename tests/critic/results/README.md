# Resultados da avaliação do Critic

Comparação entre o Critic do PR #6 e o Critic do ADR-21, nos mesmos casos cegos. A pontuação é de `scripts/eval_critic.py`, sem modelo, a partir dos vereditos e do alinhamento adjudicado. Os vereditos públicos estão nesta pasta. Dos casos reais, só os totais ficam aqui.

| Conjunto | Métrica | Antes | Depois |
|---|---|---|---|
| Público, 18 casos fictícios, 2 execuções | Veredito certo | 16/18 | 18/18 |
| | Trecho certo apontado | 10/13 e 9/13 | 13/13 |
| | Falso FAIL | 1/5 | 0/5 |
| | `keep` certo | 0/2 | 2/2 |
| Real usado no ajuste, 16 casos, 1 execução | Veredito certo | 10/16 | 12/16 |
| | Categoria do problema certa | 5/14 | 9/14 |
| | Diagnóstico alinhado | 4/14 | 9/14 |
| | Severidade adequada | 7/14 | 10/14 |
| | Falso FAIL | 1/2 | 1/2 |
| Real de controle, 11 casos, 1 execução | Veredito certo | 4/11 | 3/11 |
| | Categoria do problema certa | 2/9 | 3/9 |
| | **Diagnóstico alinhado** | **0/9** | **0/9** |
| | Diagnóstico parcial | 3/9 | 4/9 |
| | Severidade adequada | 3/9 | 3/9 |
| | Falso FAIL | 1/2 | 1/2 |

**Como ler**

- O conjunto de controle é a medida mais honesta, porque não foi usado no ajuste. Nele, nenhuma versão reproduziu o diagnóstico da revisora em nenhum caso. O ganho do conjunto de ajuste não se generalizou.
- Veredito certo não basta. Rodando alguns desses casos isoladamente, o Critic passou a reprovar por falta de fonte ou de link no pacote de teste, não pelo problema que a revisora apontou.
- Os casos fictícios têm um defeito óbvio cada, são mais fáceis que os reais e não passaram pela adjudicação.
- Sete dos 23 casos negativos reais exigem contexto fora do trecho. A avaliação os relata à parte.
- Os rótulos de categoria e severidade vieram de um modelo que leu só os comentários humanos. O alinhamento veio de um modelo cego à versão. Ambos ainda precisam de revisão humana.
- Amostras pequenas: isso mostra direção, não uma taxa de erro.

**Limites do método anterior, já corrigidos**

- O alvo real era o texto inteiro, e citação curta contava como acerto.
- "Notou" contava qualquer achado, mesmo sobre outro problema.
- Objeção factual a texto aprovado contava como falso FAIL.

**Ainda por corrigir**

- As execuções reais rodaram em lote, com a instrução de julgar só o trecho e aceitar os dados como corretos. Isso pode ter reduzido a detecção nas duas versões.
- A próxima medição precisa de casos novos, com o documento inteiro, e sem mudar o contrato com base neste controle.

**Reproduzir**

```bash
python scripts/eval_critic.py pack --cases tests/critic/cases.json --out <pasta>
python scripts/eval_critic.py score --cases tests/critic/cases.json --verdicts <arquivo>
python scripts/eval_critic.py compare --cases tests/critic/cases.json --before tests/critic/results/before-1.json --after tests/critic/results/after-1.json
```

O `pack` cria o pacote cego, e um subagente com o papel de Critic gera os vereditos.

## Continuação: avaliação por documento inteiro

O estudo histórico acima permanece **congelado** e não deve ser apresentado como
validação de desempenho. O avaliador recebeu um protocolo de avaliação com documentos
completos e anotações humanas adjudicadas, descrito em
[`tests/critic/EVALUATION.md`](../EVALUATION.md). A montagem dos pacotes cegos agora
usa uma allowlist; comentários e rótulos humanos não são repassados ao Critic.

Os exemplos em `tests/critic/fixtures/doc-*.json` são **sintéticos e manualmente
construídos para testar o código de pontuação**. Seus resultados não medem qualidade
do modelo. Um teste real exige execuções isoladas, inputs completos, adjudicação
independente e material privado fora do Git.

