# Choice

Caixa de marcar e opção de escolha única, sempre dentro de um `<label>` grande, para que o clique em qualquer ponto do texto funcione.

**Quem usa fornece:** o texto de cada opção, o `name` do grupo (para opções de escolha única) e quais vêm marcadas.

**Variações**
- `rv-check`: uma caixa de marcar com frase ao lado. Para ligar um filtro ou uma opção extra ("Mostrar só os parágrafos com correção").
- `rv-choice`: cartão de opção com título e descrição. Para decisões entre dois caminhos ("O livro inteiro" ou "Só alguns capítulos"). O marcado ganha `rv-choice--checked` (borda `primary`).
- `rv-choice rv-choice--row`: linha de lista com caixa de marcar, título e uma informação à direita. Para marcar capítulos.

**Regras**
- A caixa tem 24px e usa `primary` quando marcada.
- Listas de marcar longas trazem, acima, a contagem ("3 capítulos escolhidos") e os links "Marcar todos" e "Desmarcar todos".
- Se a escolha não pode ser desfeita depois, diga isso numa linha de ajuda antes do botão de salvar.
