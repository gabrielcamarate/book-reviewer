# Design do Revisor

Esta pasta é a referência de design do app: como as telas devem ser, com que valores e por quê. Leia este arquivo antes de mudar qualquer coisa na interface.

O Revisor corrige o português de um livro, traduz para o espanhol da América Latina e devolve dois arquivos Word. Ele é feito para autores e revisores que não precisam entender de tecnologia, no computador ou no celular. Cada decisão abaixo existe para que ninguém precise adivinhar o que fazer.

## O que há nesta pasta

| Caminho | O que é |
|---|---|
| `README.md` | Este guia: princípios, voz, cores, tipografia, estrutura. |
| `IMPLEMENTACAO.md` | Roteiro para levar o design ao código: ordem, mapa do que existe hoje para o que deve existir, lacunas e decisões em aberto. |
| `tokens.json` | Todos os valores (cores nos dois temas, tipos, espaços, raios, tamanhos), cada um com a nota de onde usar. |
| `tokens.css` | Os mesmos valores como variáveis CSS e classes de texto. Espelha o `tokens.json`. |
| `components.css` | As classes `rv-…` de cada componente, escritas só com os tokens. |
| `components/` | Uma orientação (`.md`) e um exemplo que abre no navegador (`.html`) por componente. |
| `screens/` | As 35 telas, no computador e no celular, em HTML. Comece por `screens/index.html`; o inventário e o mapa de navegação estão em `screens/README.md`. |
| `assets/icons/` | Os 15 ícones do Lucide que as telas usam. |
| `assets/brand/` | O ícone do app e o favicon. |

Os arquivos em `screens/` e os exemplos em `components/` são referência visual, não código do app: têm estilos escritos direto no HTML e texto de exemplo. O que vale no app são os tokens e os componentes.

Quando o design mudar, esta pasta muda na mesma revisão que o código.

## Princípios

- **Uma coisa por vez.** Cada tela tem uma frase que diz o que está acontecendo e uma ação principal. O resto fica em "Mais opções".
- **Página, não janela.** Tudo abre como página inteira, com um link "Voltar" no topo. A única caixa de confirmação é a de aprovar vários trechos de uma vez.
- **Nada só com ícone.** Todo botão tem texto. Ícone acompanha, nunca substitui.
- **Mostrar só o que serve agora.** Arquivo que ainda não está pronto aparece como texto, não como botão desativado.

## Voz e texto

- Escreva em português do Brasil, com frases curtas e palavras do dia a dia.
- Fale com "você". O app é "o Revisor".
- Diga "trecho", "correção", "livro", "arquivo Word". Nunca "chunk", "job", "escopo", "proposta", "prévia", "exportar".
- Botão começa com verbo e diz o resultado: "Processar o livro completo", "Baixar o livro em espanhol", "Continuar de onde parou".
- Explique o que acontece depois do clique numa linha de apoio: "Termina o que já começou e guarda o progresso."
- Diante de um problema, diga primeiro o que está a salvo: "O resto do livro está salvo. Tente esses dois de novo."
- Motivo de correção cabe em uma linha e não usa nome de regra gramatical: "“Mas” indica oposição; “mais” indica quantidade."
- Sem emoji, sem ponto de exclamação, sem maiúsculas para dar ênfase.

## Cores

- Há dois temas com os mesmos nomes de token: **Escuro** (padrão) e **Claro**. Nunca escreva uma cor direto no código; use o token.
- Fundo da página em `background`; conteúdo agrupado em `card`. Texto em `foreground`; apoio em `muted-foreground`. Não existe cinza mais fraco que `muted-foreground`.
- `primary` marca o que é ação ou andamento: o botão principal, links, a etapa atual, o termo corrigido. Use um botão principal por tela.
- Texto sobre `primary` é sempre `primary-foreground`. No tema escuro isso é quase preto, não branco.
- `neutral` mostra progresso que não está rodando agora. `destructive` é só para alerta e erro, sempre com ícone ou frase junto.
- Palavra corrigida dentro do texto do livro: fundo `highlight`, texto `highlight-foreground`.
- Separe com borda, não com sombra. O sistema não tem sombras. Linha fina `border` entre itens; `border-strong` em cartões vazados; `border-control` em tudo que se clica ou se preenche.

## Tipografia

- **Newsreader** (`serif`) para títulos e para o texto do livro. **Manrope** (`sans`) para a interface. As duas vêm do Google Fonts.
- O menor texto é 16px (`ui-small`). O texto padrão é 18px (`ui-body`).
- O texto do livro usa `book-text` (23px) no computador e `book-text-mobile` (21px) no celular, com no máximo `reading-max` de largura.
- Um `title-page` por tela. Dentro de cartões, `title-card` no principal e `title-section` nos demais.
- Peso 700 para valores e ações; 600 para botões secundários; 500 nos títulos em serif. Não use itálico fora de `book-quote`.
- Números que mudam (porcentagens, contagens) usam algarismos tabulares.

## Espaço, forma e tamanho

- Todo espaçamento sai da escala `space-1` a `space-16`. Entre seções da página, `space-8`; entre cartões, `space-6`.
- Cartões têm `radius-2xl` no computador e `radius-card-mobile` no celular. Botões e campos, `radius-md`. Um elemento dentro de outro arredondado usa o raio de fora menos a folga.
- Botões e campos têm `control` (56px) de altura. A ação principal da tela pode usar `control-lg` (68px). Nada clicável tem menos que `control-min` (44px).
- No celular, botões ocupam a largura toda e ficam empilhados, o principal em cima.
- Foco do teclado: contorno de 3px em `ring`, afastado 3px. Nunca remova.

## Estrutura das telas

- **Computador:** cabeçalho com a marca à esquerda e, à direita, "Meus livros", "Mais opções" e o tema. Conteúdo centralizado com `content-max`. Duas colunas na proporção 3 para 2: à esquerda o cartão com a ação principal; à direita, arquivos, etapas ou explicações.
- **Celular:** coluna única com `space-5` de margem e uma barra inferior fixa com três abas escritas por extenso: "Livro", "Meus livros", "Opções".
- Listas longas são paginadas com um botão "Mostrar mais", nunca rolagem infinita.
- Correções ficam junto do parágrafo a que pertencem: ao lado no computador, fechadas embaixo dele no celular.

## Ícones e marca

- Os ícones são os da biblioteca Lucide (`lucide-react`, já usada no código), em traço, na cor do texto ao redor. Tamanho 20px dentro de botões, 22px na barra inferior, 28px na marca. Os 15 que as telas usam estão em `assets/icons/`, com a lista de onde cada um aparece.
- Dentro das telas, a marca é a palavra "Revisor" em `title-section`, precedida do ícone `book-open` em `primary`. Não há logotipo escrito.
- O ícone do app e o favicon estão em `assets/brand/`: três linhas de texto com a palavra corrigida em âmbar. Ele fica fora das telas, na aba do navegador e no atalho do celular.

## Como usar no código

- Cada token vira uma variável CSS com o mesmo nome (`--background`, `--primary`, `--space-6`), declarada para os dois temas. O tema ativo vem do atributo `data-theme` (`dark` ou `light`) no elemento `html`.
- Os nomes de cor seguem a convenção do shadcn/ui, que o projeto já usa, e substituem as variáveis atuais uma a uma.
- `components.css` mostra como cada componente se monta sobre os tokens. No app, os componentes são React; as classes `rv-…` servem de especificação e podem ser usadas direto onde for mais simples.
- Cada componente tem uma orientação em `components/` dizendo o que quem usa precisa fornecer, as variações e as regras.
