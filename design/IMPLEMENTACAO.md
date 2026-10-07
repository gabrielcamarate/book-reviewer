# Do design ao código

Roteiro para aplicar o design desta pasta no frontend. Vale enquanto a migração estiver em curso; depois dela, pode ser arquivado.

## Alcance

- Muda só o frontend (`frontend/`). A API e as regras editoriais ficam como estão, com uma exceção listada em "Lacunas".
- A interface passa a seguir `design/screens/`. O que as telas não mostram sai da tela principal: ou vai para "Mais opções", ou deixa de aparecer. Nenhuma capacidade do servidor é removida.
- O resultado tem de funcionar no computador e no celular, nos temas escuro e claro.

## Ordem sugerida

1. **Tokens e temas.** Trocar as variáveis de `frontend/src/index.css` pelas de `design/tokens.css`. O tema vem de `data-theme` no `html`: segue o sistema por padrão e guarda a escolha do usuário no navegador. Trocar a fonte Fraunces por Newsreader e manter Manrope. Pôr o favicon de `design/assets/brand/` em `frontend/index.html`.
2. **Componentes base.** Levar para `frontend/src/components/ui/` os componentes de `design/components/`, aproveitando os que já existem (`button`, `progress`, `dialog`, `label`, `spinner`).
3. **Estrutura.** Cabeçalho no computador, barra inferior no celular, e a troca de tela por estado do livro (tabela abaixo).
4. **Telas**, na ordem dos grupos de `design/screens/README.md`.
5. **Limpeza.** Remover o CSS e os componentes que deixaram de ser usados.

Cada passo deixa o app funcionando e passa em `scripts/ci.sh`.

Andamento: passo 1 concluído em 0.4.0 (tokens importados de `design/tokens.css`, tema por `data-theme` em `frontend/src/lib/theme.ts`, Newsreader e favicon).
Passo 2 concluído em 0.5.0: `frontend/src/components/ui/` tem um componente React por arquivo de `design/components/`, todos sobre as classes `rv-` de `design/components.css`, importado sem cópia. `lib/viewport.ts` decide celular ou computador.
Passo 3 concluído em 0.6.0: `App.tsx` monta `AppHeader` ou `TabBar` e escolhe a tela por `lib/screens.ts` (testado com `node --test`). Carregando e erro já seguem o design; as demais telas ainda mostram a área de trabalho anterior (`screens/legacy-workspace.tsx`) até o passo 4. Layout das páginas em `design/components.css` (`rv-page`, `rv-columns`, `rv-message`).

## Do que existe hoje para o que deve existir

| Hoje | Passa a ser |
|---|---|
| `App.tsx`: uma página com tudo empilhado | Uma tela por estado, com cabeçalho ou barra inferior |
| Barra lateral "Seus livros" | Tela `livros` |
| `ImportBook` | `novo-livro` e `novo-livro-com-word-em-espanhol` |
| `BookSetup` (escopo, orientações e glossário num só painel) | Linhas de resumo em `pronto-para-comecar`, com `escolher-capitulos`, `orientacoes` e `glossario` como telas próprias |
| `BookProgress` (quatro barras em grade) | Componente `Steps`, com os nomes de etapa do design |
| `BookJobStatus` | O cartão de situação de `acompanhar`, `pausado`, `parou-no-meio` e `precisa-de-atencao` |
| Seletor de trecho (`<select>`) | Tela `trechos`, paginada |
| `BookReader` (três colunas) | `conferir`, com três visões e as correções junto de cada parágrafo |
| Bloco "Modo manual" e ações de aprovar, recusar e ajustar | As telas `aprovar-a-mao…`, ligadas em "Mais opções" |
| "Conferir consistência" | Tela `alertas` |
| "Observações para a autora" | Tela `observacoes`, anunciada em `livro-pronto` |
| `BookGlossary` (texto no formato `português = espanhol`) | Tela `glossario`, com dois campos por termo |
| Rodapé de exportação | Os dois botões de `livro-pronto` |
| Rodapé com modelo e esforço | "Sobre este livro", em `mais-opcoes` |

## Qual tela mostrar

| Condição | Tela |
|---|---|
| Carregando a lista ou o livro | `carregando` |
| Erro ao falar com o servidor | `erro` |
| Nenhum livro | `inicio` |
| Há processamento em outro livro e este não começou | `outro-livro` |
| Livro sem trecho revisado e sem processamento | `pronto-para-comecar` |
| `job.status` é `running` ou `stopping` | `acompanhar` (em `stopping`, o botão "Pausar" fica desativado com o texto "Pausando…") |
| `job.status` é `paused` | `pausado` |
| `job.status` é `failed` ou `interrupted` | `parou-no-meio` |
| `job.status` é `needs_attention` | `precisa-de-atencao`, listando `job.problems` |
| Existe `automatic_result` | `livro-pronto` |
| Aprovação à mão ligada | `aprovar-a-mao` no lugar das telas de andamento |

## Nomes das etapas

| No design | Campo de `progress` |
|---|---|
| Revisar o português | `draft_percent` |
| Conferir e aplicar as correções | `review_percent` |
| Traduzir para o espanhol | `translation_percent` |
| Revisar o espanhol | `checked_percent` |

A etapa em andamento é a primeira que ainda não chegou a 100%. As seguintes, se já tiverem progresso, usam a barra neutra.

## O que sai da tela principal

- A contagem de parágrafos por etapa. Fica só a porcentagem.
- O nome do arquivo e o modelo. Vão para "Sobre este livro".
- O tempo decorrido e a contagem de trechos da etapa.
- O campo "Quantidade de trechos" do modo manual.
- Os botões de baixar enquanto o livro não está pronto. No lugar, uma frase.

## Lacunas

A única lacuna da API foi resolvida em 0.3.0: cada item de `chunks` traz `corrections`, a contagem que `trechos` mostra em cada linha.

O restante se resolve no frontend:

- **Tema e tamanho do texto:** preferências guardadas no navegador.
- **Glossário em dois campos:** a tela monta o mesmo dicionário que a ação `glossary` já recebe.
- **"1 observação para você" na lista de trechos e o filtro "Com observações":** derivados de `editorial_notes`.
- **Paginação de trechos:** a lista já vem inteira; a tela mostra em partes.

## Decisões tomadas

- **Revisão anterior:** retirada por completo em 0.3.0, com o código e a API que só ela usava.
- **Contagem de correções por trecho:** incluída na API em 0.3.0.

## Verificação

- `scripts/ci.sh` e o typecheck do frontend passam.
- Cada tela é conferida contra o arquivo correspondente em `design/screens/`, no computador e no celular, nos dois temas.
- Nenhuma cor, espaço ou raio escrito direto no código: tudo sai dos tokens.
- Foco visível em todos os controles, texto nunca menor que 16px, alvos de toque de pelo menos 44px.
