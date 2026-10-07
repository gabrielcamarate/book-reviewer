# SummaryRow

Linhas de "o quê — valor", separadas por traços finos, com um link opcional para mudar o valor.

**Quem usa fornece:** para cada linha, o termo, o valor atual e, se der para mudar, o link com o verbo ("Mudar", "Escrever", "Ver e mudar").

**Onde aparece**
- Antes de começar: "O que será revisado — O livro inteiro · Mudar".
- Em "Seus arquivos": o nome do arquivo e, embaixo, "Ainda não está pronto".
- Em "Sobre este livro": arquivo e modelo.

**Estrutura:** uma `<dl class="rv-summary">`; cada linha é um `<div class="rv-summary__row">` com `<dt class="rv-summary__term">` e `<dd class="rv-summary__value">`.

**Regras**
- O termo vai em `muted-foreground`; o valor, em negrito.
- Sem valor ainda, escreva a palavra ("Nenhuma", "Nenhum termo"), não deixe em branco.
- Valor que não pode mais mudar perde o link e ganha, embaixo, uma frase dizendo por quê.
- No celular, o termo fica em cima e o valor embaixo, com o link à direita.
