# Button

Botão de ação, sempre com texto. Use a classe `rv-btn` num `<button>` (ação na própria tela) ou num `<a>` (leva a outra tela).

**Quem usa fornece:** o texto, que começa com verbo e diz o resultado ("Baixar o livro em espanhol"); opcionalmente um ícone Lucide de 20px antes do texto.

**Variações**
- `rv-btn` sozinho: secundário, com borda `border-control`.
- `rv-btn--primary`: a ação principal. No máximo um por tela.
- `rv-btn--lg`: 68px de altura (`control-lg`), para a ação que resolve a tela ("Processar o livro completo", "Continuar").
- `rv-btn--block`: largura total. No celular, todo botão é assim.
- `disabled`: fundo `track`. Explique logo abaixo, em `ui-small`, quando ele fica disponível.
- Em curso (`aria-busy="true"`): o arco do `Spinner` entra no lugar do ícone e o botão fica desativado até a ação terminar. Toda ação que fala com o servidor mostra esse estado, inclusive trocar de trecho.

**Regras**
- Nunca só ícone. Nunca dois botões principais lado a lado.
- Em vez de mostrar um botão desativado para algo que ainda não existe (um arquivo que não ficou pronto), mostre uma linha de texto.
- Botões lado a lado ficam a `space-3`; no celular, empilhados com o principal em cima.
