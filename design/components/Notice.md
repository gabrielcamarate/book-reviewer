# Notice

Aviso sobre a situação do livro: uma faixa com frase e ação, ou um ícone grande que abre o cartão principal.

**Quem usa fornece:** uma frase curta em negrito com o fato, uma segunda frase com o que fazer e, se houver, um botão ou link.

**Partes**
- `rv-notice`: faixa com borda `primary`. Informa algo que muda o que o usuário pode fazer agora ("O Revisor está trabalhando em “A casa das marés”. Ele faz um livro por vez.") e oferece o caminho ("Acompanhar A casa das marés").
- `rv-notice rv-notice--plain`: faixa sem destaque, para situar ("Este trecho ainda não foi revisado") com a ação ao lado.
- `rv-status-icon`: círculo de 56px (48 no celular) em `primary` com o visto. Abre o cartão de "Seu livro está pronto".
- `rv-status-icon rv-status-icon--alert`: círculo com borda `destructive` e o ponto de exclamação. Abre o cartão de problema, junto com `rv-card--alert`.

**Regras**
- Use `role="status"` no elemento que traz a frase.
- Diante de um problema, a primeira coisa dita é o que está a salvo; a ação principal é tentar de novo.
- Nunca aviso só com cor: sempre o ícone e a frase.
- Não use aviso para confirmar sucesso de algo trivial. Reserve para o que muda o próximo passo.
