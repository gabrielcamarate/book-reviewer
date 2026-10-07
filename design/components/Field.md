# Field

Campo de texto com rótulo visível: uma linha (`rv-input`) ou várias (`rv-textarea`).

**Quem usa fornece:** o rótulo, o `id` que liga o `<label>` ao campo e, se precisar, uma linha de ajuda. Para campo opcional, acrescente "(opcional)" no rótulo com `rv-label__optional`.

**Estrutura:** `rv-field` envolve `<label class="rv-label">`, o campo e, por último, a ajuda (`rv-help`) ou o erro (`rv-error`).

**Variações**
- `rv-input`: 56px de altura (`control`).
- `rv-textarea`: para orientações e pedidos.
- `rv-textarea rv-textarea--book`: para editar texto do livro, em serif de 21px. Mostre o parágrafo inteiro, sem rolagem dentro do campo.
- Erro: `aria-invalid="true"` no campo e uma frase em `rv-error` com `role="alert"` logo abaixo, dizendo o que falta ("Falta a palavra em espanhol.").

**Regras**
- O rótulo fica sempre visível, acima do campo. O texto de exemplo dentro do campo não substitui o rótulo.
- A ajuda explica a consequência ("Depois de salvar, o Revisor confere este trecho de novo."), não o formato.
- Não peça para o usuário digitar num formato especial. Dois valores são dois campos.
