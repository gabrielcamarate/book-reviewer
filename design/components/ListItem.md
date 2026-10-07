# ListItem

Linha clicável de uma lista: um trecho do livro, com número, título e uma informação à direita.

**Quem usa fornece:** o número do trecho, o título, a informação da direita ("14 correções", "Sem correções") e, se houver, uma nota embaixo do título ("Aberto agora", "1 observação para você").

**Estrutura:** um `<a class="rv-item">` com `rv-item__index`, `rv-item__body` (título e nota) e `rv-item__meta`. O trecho aberto leva `aria-current="true"` e ganha borda `primary`.

**Regras**
- A linha inteira é o link; não ponha botões dentro dela.
- No computador a lista tem duas colunas; no celular, uma, com a informação da direita descendo para baixo do título.
- Mostre de 8 a 12 linhas e um botão "Mostrar mais trechos", com a contagem ao lado ("Mostrando 12 de 86"). Nunca rolagem infinita.
- Acima da lista, um `SegmentedControl` filtra: "Todos os 86", "Com observações (3)".
- O livro, na lista de livros, usa `Card` (com `rv-card--current` no que está em andamento), não este componente.
