# Telas de referência

São 35 telas, cada uma em `computador/` (1440px) e em `celular/` (390px), com o mesmo nome de arquivo nas duas pastas. Abra `index.html` para navegar por todas. Dentro de cada tela, os botões que navegam levam à tela correspondente.

O texto do livro, os nomes de capítulo e os números são exemplos inventados.

## Regras de navegação

- Toda tela que não é a principal começa com um link "Voltar…" que diz para onde volta.
- Nada abre em janela, exceto a confirmação de aprovar vários trechos de uma vez.
- No computador, "Meus livros" e "Mais opções" ficam no cabeçalho. No celular, ficam na barra inferior, junto com "Livro".
- Baixar, pausar e trocar de tema agem na própria tela.

## 1. Do primeiro acesso ao livro pronto

| Arquivo | Quando aparece | Para onde leva |
|---|---|---|
| `inicio.html` | Ainda não existe nenhum livro. | "Escolher o arquivo do livro" → `novo-livro` |
| `livros.html` | "Meus livros". O livro em andamento vem destacado. | Um livro → a tela do livro no estado em que ele está; "Novo livro" → `novo-livro` |
| `novo-livro.html` | Importar um livro. | "Importar livro" → `pronto-para-comecar`; "Já tenho um Word em espanhol…" → `novo-livro-com-word-em-espanhol` |
| `novo-livro-com-word-em-espanhol.html` | Arquivo já escolhido e a opção de inserir a tradução num Word espanhol existente marcada. | "Importar livro" → `escolher-capitulos` (neste caso a escolha de capítulos é obrigatória) |
| `pronto-para-comecar.html` | Livro importado, revisão ainda não começou. | "Processar o livro completo" → `acompanhar`; "Mudar" → `escolher-capitulos`; "Escrever" → `orientacoes`; "Ver e mudar" → `glossario` |
| `acompanhar.html` | Processamento rodando. | "Ver o texto e as correções" → `conferir` |
| `acompanhar-claro.html` | A mesma tela no tema claro. | |
| `livro-pronto.html` | As quatro etapas terminaram. | "Ler as observações" → `observacoes`; "Ver o texto e as correções" → `conferir`; "Começar outro livro" → `novo-livro` |

## 2. Antes de começar e opções

| Arquivo | Quando aparece | Para onde leva |
|---|---|---|
| `escolher-capitulos.html` | Escolher entre o livro inteiro e alguns capítulos. Só antes de a revisão começar. | "Salvar e voltar" → `pronto-para-comecar` |
| `orientacoes.html` | Escrever o que o Revisor deve respeitar. Só antes de a revisão começar. | "Salvar orientações" → `pronto-para-comecar` |
| `glossario.html` | Termos em português e em espanhol, um par por linha, com estado de erro. Pode mudar a qualquer momento. | "Salvar glossário" → `mais-opcoes` |
| `mais-opcoes.html` | Aparência, o que revisar, orientações, glossário, aprovar à mão, alertas, sobre. | "Editar glossário" → `glossario`; "Ligar aprovação à mão" → `aprovar-a-mao`; "Ver os alertas" → `alertas` |
| `alertas.html` | Nomes e palavras escritos de mais de um jeito. | "Abrir este trecho" → `conferir` |
| `observacoes.html` | Pontos ambíguos do original, preservados para decisão de quem escreveu. Agrupados por trecho, com "Para ler" e "Lidas"; cada uma pode ser marcada como lida, ou todas de uma vez. | "Abrir este trecho" → `conferir` |

## 3. Quando algo sai do caminho

| Arquivo | Quando aparece | Para onde leva |
|---|---|---|
| `pausado.html` | O usuário pausou. | "Continuar" → `acompanhar` |
| `parou-no-meio.html` | O processamento falhou ou foi interrompido. | "Continuar de onde parou" → `acompanhar` |
| `precisa-de-atencao.html` | Alguns trechos não foram concluídos. | "Tentar esses trechos de novo" → `acompanhar`; "Abrir este trecho" → `conferir` |
| `outro-livro.html` | O livro aberto não pode começar porque outro está em processamento. | "Acompanhar…" → `acompanhar` |
| `erro.html` | O app não conseguiu falar com o servidor local. | "Tentar de novo" recarrega |
| `carregando.html` | Abrindo a lista de livros ou um livro. | |

## 4. Conferir o texto

| Arquivo | Quando aparece | Para onde leva |
|---|---|---|
| `conferir.html` | Um trecho, com as palavras corrigidas marcadas e as correções junto de cada parágrafo. Exemplo com 14 correções em 6 parágrafos. | "Texto original" → `conferir-original`; "Em espanhol" → `conferir-espanhol`; "Escolher outro trecho" → `trechos` |
| `conferir-claro.html` | A mesma tela no tema claro. | |
| `conferir-original.html` | O texto como foi escrito, com as palavras que mudaram sublinhadas. | |
| `conferir-espanhol.html` | Português revisado e espanhol, parágrafo a parágrafo. | "Ajustar o espanhol" → `ajustar-espanhol` |
| `conferir-sem-traducao.html` | A aba "Em espanhol" de um trecho ainda não traduzido. | "Ver o que mudou" → `conferir` |
| `ajustar-espanhol.html` | Editar a tradução, um campo por parágrafo. | "Salvar ajustes" → `conferir-espanhol` |
| (sem arquivo próprio) Ajustar o português | Mesmo layout de `ajustar-espanhol`: à esquerda o texto como foi escrito, à direita o revisado em campos. Aberto por "Ajustar o português" em `conferir` (trecho aprovado) e em cada trecho de `observacoes`. Ao salvar, `conferir` mostra um aviso para voltar ao livro e continuar, e só a tradução desse trecho é refeita. | "Salvar ajustes" → `conferir` |
| `trechos.html` | Lista paginada dos trechos, com filtro. | Um trecho → `conferir` |

## 5. Aprovar à mão (opção avançada)

Desligado por padrão. Ligado em "Mais opções", troca a tela do livro por esta sequência.

| Arquivo | Quando aparece | Para onde leva |
|---|---|---|
| `aprovar-a-mao.html` | A tela do livro neste modo: revisar, aprovar, traduzir. | "Conferir o próximo trecho" → `aprovar-a-mao-conferir`; "Aprovar os 12 de uma vez" → `aprovar-a-mao-confirmar` |
| `aprovar-a-mao-conferir.html` | Trecho com correções esperando aprovação. | "Aprovar este trecho" → `aprovar-a-mao-aprovado`; "Ajustar o texto" → `aprovar-a-mao-ajustar`; "Recusar…" → `aprovar-a-mao-recusar` |
| `aprovar-a-mao-ajustar.html` | Editar o texto revisado antes de aprovar. | "Aprovar com meus ajustes" → `aprovar-a-mao-aprovado` |
| `aprovar-a-mao-recusar.html` | Dizer o que precisa mudar. | "Registrar e pedir outra revisão" → `aprovar-a-mao-recusado` |
| `aprovar-a-mao-recusado.html` | Trecho com a revisão recusada. | "Pedir nova revisão deste trecho" refaz a revisão |
| `aprovar-a-mao-nao-revisado.html` | Trecho que ainda não passou pela revisão. | "Revisar este trecho agora" inicia a revisão |
| `aprovar-a-mao-aprovado.html` | Trecho já aprovado. | "Próximo trecho esperando você" → `aprovar-a-mao-conferir`; "Reabrir a revisão deste trecho" reabre |
| `aprovar-a-mao-confirmar.html` | A caixa de confirmação de aprovar todos. | Os dois botões voltam a `aprovar-a-mao` |

## O que não está desenhado

- O tema claro só está desenhado em `acompanhar` e `conferir`. As demais telas seguem a mesma troca de tokens.
- A "Revisão anterior" (interface antiga, de um trecho por vez) foi retirada do app em 0.3.0. O fluxo dela é coberto por "Aprovar à mão".
