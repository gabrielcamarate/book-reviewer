# ProgressBar

Barra de 10px que mostra quanto de uma etapa já foi feito.

**Quem usa fornece:** a porcentagem (largura de `rv-progress__bar`) e, ao lado ou acima, o mesmo valor escrito ("71%" ou "52 de 86 trechos"). A barra nunca aparece sozinha.

**Variações**
- `rv-progress`: barra em `primary`. O trabalho está rodando agora.
- `rv-progress rv-progress--neutral`: barra em `neutral`. O valor é real, mas nada está rodando: livro pausado, ou uma etapa que só acompanha a anterior.

**Regras**
- Não invente um total geral. Mostre o progresso de cada etapa, com o número dela.
- Não mostre tempo restante: o app não sabe calcular.
- Etapa concluída não tem barra; tem a palavra "Concluído".
