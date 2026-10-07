# Correction

Um parágrafo do livro com as palavras corrigidas marcadas e, junto dele, cada correção com o motivo. É o que impede uma lista sem fim de correções: elas ficam presas ao parágrafo a que pertencem.

**Quem usa fornece:** o texto revisado do parágrafo com os trechos alterados identificados, e, para cada correção, o que estava escrito, o que ficou e o motivo em uma linha.

**Partes**
- `rv-mark`: a palavra corrigida dentro do texto revisado (fundo `highlight`).
- `rv-mark rv-mark--original`: a mesma palavra no texto original, com sublinhado ondulado em `primary`, sem fundo.
- `rv-correction`: o par antes → depois (`<del>` em `muted-foreground`, seta, `<ins>` em `primary` e peso 600) e o motivo em `rv-correction__why`.
- `rv-para`: a linha que junta o texto (`rv-para__text`, em `book-text`) e as correções (`rv-para__notes`).
- `rv-disclosure`: no celular, o botão que abre e fecha as correções do parágrafo.

**Comportamento**
- Computador: texto à esquerda, correções à direita, alinhadas ao topo do parágrafo. A página cresce com o texto, não com o número de correções.
- Celular: as correções ficam fechadas embaixo do parágrafo, num botão que diz quantas são ("Ver as 4 correções"). Aberto, o botão vira "2 correções neste parágrafo" com a seta para cima (`aria-expanded="true"`).
- Parágrafo sem correção: no computador, a frase "Sem correções neste parágrafo." à direita; no celular, nada.
- Acima da lista, o total do trecho ("14 correções neste trecho") e a opção "Mostrar só os parágrafos com correção".

**Regras**
- O motivo cabe em uma linha e não usa nome de regra: "Tempo que já passou se escreve com “há”."
- Quando todas as correções de um parágrafo têm o mesmo motivo (o caso comum na revisão automática), a lista mostra só os pares antes → depois e o motivo aparece uma vez, embaixo. Nunca repita o mesmo motivo em cada correção.
- O "antes" é sempre riscado e o "depois" em negrito, para a diferença não depender da cor.
- Não mostre nota de confiança nem categoria gramatical ao usuário.
