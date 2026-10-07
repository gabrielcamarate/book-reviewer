# Link

Link de texto sublinhado, para ações secundárias e para voltar. Use `rv-link` num `<a>` ou num `<button>`.

**Quem usa fornece:** o texto e o destino. O link de voltar leva também o ícone de seta para a esquerda.

**Variações**
- `rv-link`: cor `primary`. Para "Abrir este trecho", "Mudar", "Escolher outro trecho".
- `rv-link--quiet`: cor `foreground`. Para ações que não devem chamar atenção ("Reabrir a revisão deste trecho", "Trocar arquivo").
- `rv-link--back`: o link "Voltar…" no topo de toda tela que não é a principal. O texto diz para onde volta: "Voltar ao livro", "Voltar às opções", "Voltar sem salvar".

**Regras**
- Mesmo sendo texto, ocupa pelo menos `control-min` (44px) de altura.
- Quando a ação leva tempo, o arco do `Spinner` aparece depois do texto até ela terminar.
- O sublinhado nunca sai: é ele que mostra que dá para clicar.
- Não use link para a ação principal da tela; isso é do `Button`.
