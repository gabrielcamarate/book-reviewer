# Card

Caixa que agrupa um assunto da tela. O cartão preenchido carrega a ação principal; o vazado, as informações de apoio.

**Quem usa fornece:** um título (`title-card` no cartão principal, `title-section` nos demais) e o conteúdo.

**Variações**
- `rv-card`: fundo `card`. Um por tela costuma bastar; é onde fica o botão principal.
- `rv-card--outline`: sem fundo, borda `border-strong`. Para a coluna da direita: "Seus arquivos", "As quatro etapas", "O que o Revisor faz".
- `rv-card--alert`: borda `destructive`. Só quando há um problema que pede ação do usuário, sempre com o ícone de alerta e uma frase.
- `rv-card--current`: borda `primary`. O livro em andamento na lista de livros.
- `rv-card--mobile`: padding `space-6` e raio `radius-card-mobile`. Use em todos os cartões no celular.

**Regras**
- Não coloque cartão dentro de cartão. Dentro dele, separe com linhas `border`.
- Sem sombra e sem borda colorida só de um lado.
- No computador, cartões lado a lado seguem a proporção 3 para 2 e ficam a `space-6` um do outro.
