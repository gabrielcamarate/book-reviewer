# Spinner

Arco que gira enquanto o app carrega algo, sempre com uma frase ao lado ou embaixo.

**Quem usa fornece:** a frase que diz o que está sendo carregado ("Abrindo seus livros…", "Abrindo o livro…").

**Uso**
- Tela inteira carregando: `rv-loading` com `role="status"`, o arco de 48px e a frase em 22px, centralizados.
- Dentro de um botão em que a ação está em curso: arco de 20px no lugar do ícone, e o texto muda para o gerúndio ("Importando…"). O botão fica desativado enquanto isso.

**Regras**
- Nunca o arco sozinho.
- O giro para quando o sistema pede menos movimento (`prefers-reduced-motion`); a frase continua dizendo o que acontece.
- Para trabalho longo (o processamento do livro), não use o arco: use `Steps` com `ProgressBar`.
