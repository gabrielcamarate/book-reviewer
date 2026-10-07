# AppHeader

Cabeçalho das telas no computador: a marca à esquerda e, à direita, os dois destinos fixos e o tema.

**Quem usa fornece:** qual item está ativo (`aria-current="page"`) e o tema marcado.

**Conteúdo fixo, nesta ordem**
1. Marca: ícone de livro aberto em `primary` e a palavra "Revisor" (`rv-brand`).
2. "Meus livros" (`rv-nav__link`).
3. "Mais opções" (`rv-nav__link`).
4. Tema: `SegmentedControl` pequeno com "Escuro" e "Claro".

**Regras**
- Não acrescente itens. O que não cabe aqui vai para "Mais opções".
- O item ativo ganha fundo `card`, texto `primary` e peso 700.
- Em telas estreitas os itens quebram para a linha de baixo; no celular o cabeçalho traz só a marca, e a navegação passa para a `TabBar`.
- Abaixo do cabeçalho, toda tela que não é a principal começa com um `Link` de voltar.
