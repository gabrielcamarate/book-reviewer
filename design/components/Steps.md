# Steps

Lista das quatro etapas do livro, com a situação de cada uma. É o centro da tela de acompanhar.

**Quem usa fornece:** para cada etapa, o nome, o estado e, se estiver em andamento, a porcentagem.

**As etapas, com estes nomes:** "Revisar o português", "Conferir e aplicar as correções", "Traduzir para o espanhol", "Revisar o espanhol". No modo de aprovar à mão são três: "Revisar o português", "Aprovar as correções", "Traduzir para o espanhol".

**Estados de uma etapa (`rv-step`)**
- `rv-step--done`: círculo preenchido em `primary` com o ícone de visto, e a palavra "Concluído" à direita.
- `rv-step--current`: círculo com borda `primary` e o número; nome em negrito; `ProgressBar` embaixo do nome; porcentagem em `primary` à direita.
- Sem modificador: ainda não começou, ou só acompanha a anterior. Círculo com borda `neutral` e o número; barra `rv-progress--neutral` se já tiver algum progresso.

**Regras**
- Acima da lista, diga em que ponto está: "Etapa 3 de 4" em `ui-label` e um título com o que está acontecendo ("Traduzindo para o espanhol").
- O estado não depende só da cor: há o visto, o número e a palavra.
- Numa etapa com ação do usuário (aprovar à mão), o botão fica dentro da etapa, embaixo da linha de situação.
