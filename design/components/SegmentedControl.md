# SegmentedControl

Grupo de duas ou três opções em que só uma fica marcada. Serve para trocar o que a tela mostra, não para navegar para longe.

**Quem usa fornece:** de duas a três opções com rótulos curtos, qual está marcada (`aria-pressed="true"`) e um `aria-label` para o grupo.

**Onde aparece**
- Tema: "Escuro" e "Claro" no cabeçalho (`rv-segmented--sm`).
- O que mostrar ao conferir um trecho: "O que mudou", "Texto original", "Em espanhol".
- Filtro de lista: "Todos os 86", "Com observações (3)".
- Tamanho do texto: "Normal", "Grande", "Muito grande".

**Variações**
- `rv-segmented`: em linha, largura do conteúdo.
- `rv-segmented--sm`: opções de 44px, para o cabeçalho.
- `rv-segmented--block`: colunas iguais ocupando a largura toda. No celular, com rótulos encurtados ("Mudanças", "Original", "Espanhol").
- `rv-segmented--stack`: opções empilhadas, para rótulos longos no celular ("Igual ao do aparelho").

**Regras**
- A opção marcada usa `selected` e `selected-foreground`, e também peso 700, para não depender só da cor.
- Mais de três opções viram lista de escolha (`Choice`), não grupo segmentado.
- Uma opção que só faz sentido em alguns casos some do grupo; não fica desativada.
