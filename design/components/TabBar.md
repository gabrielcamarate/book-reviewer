# TabBar

Barra fixa no pé da tela do celular, com as três áreas do app escritas por extenso.

**Quem usa fornece:** qual aba está ativa (`aria-current="page"`).

**Abas fixas, nesta ordem**
1. "Livro": o livro aberto, em qualquer estado, e as telas que saem dele (conferir, trechos, observações).
2. "Meus livros": a lista e a importação de um livro novo.
3. "Opções": o mesmo conteúdo de "Mais opções" do computador, incluindo o tema.

**Regras**
- Sempre três abas, cada uma com ícone de 22px e rótulo em `ui-label`. Nunca só o ícone.
- A aba ativa usa `primary` e peso 700.
- A barra fica presa ao pé da tela e tem 72px de altura; o conteúdo rola por trás dela com folga no fim.
- Só existe no celular. No computador a navegação é o `AppHeader`.
