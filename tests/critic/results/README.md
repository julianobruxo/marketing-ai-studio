# Resultados da avaliação do Critic

Comparação entre o Critic do PR #6 e o Critic do ADR-21, nos mesmos casos cegos. A pontuação é de `scripts/eval_critic.py`, sem modelo. Os vereditos públicos estão nesta pasta. Dos casos reais, só os totais ficam aqui.

| Conjunto | Métrica | Antes | Depois |
|---|---|---|---|
| Público, 18 casos fictícios, 2 execuções | Veredito certo | 16/18 | 18/18 |
| | Trecho certo apontado | 10/13 e 9/13 | 13/13 |
| | Falso FAIL | 1/5 | 0/5 |
| | `keep` certo | 0/2 | 2/2 |
| Real usado no ajuste, 16 casos, 1 execução | Problemas reprovados | 9/14 | 11/14 |
| | Problemas notados | 9/14 | 12/14 |
| | Falso FAIL | 1/2 | 1/2 |
| Real de controle, 11 casos, 1 execução | Problemas reprovados | 3/9 | 2/9 |
| | Problemas notados | 3/9 | 6/9 |
| | Falso FAIL | 1/2 | 1/2 |

**Como ler**

- O conjunto de controle é a medida mais honesta, porque ele não foi usado para ajustar o contrato. Nele, o Critic novo não reprovou mais que o anterior.
- "Notados" inclui achados `material`, que aparecem para o operador, mas não abrem rodada. Essa métrica foi criada depois de ver o resultado do controle.
- Os casos fictícios têm um defeito óbvio cada, então são mais fáceis que os reais.
- Os casos reais são trechos sem o documento em volta, e a revisora viu o texto inteiro. O falso FAIL do conjunto de ajuste vem de um CTA cortado antes do botão.
- Os positivos do controle vêm de uma aprovação relatada pelo operador, que não está nos comentários do documento.
- Amostras pequenas: isso mostra direção, não uma taxa de erro.

**Reproduzir**

```bash
python scripts/eval_critic.py pack --cases tests/critic/cases.json --out <pasta>
python scripts/eval_critic.py score --cases tests/critic/cases.json --verdicts <arquivo>
python scripts/eval_critic.py compare --cases tests/critic/cases.json --before tests/critic/results/before-1.json --after tests/critic/results/after-1.json
```

O `pack` cria o pacote cego, e um subagente com o papel de Critic gera os vereditos.
