# Interface do revisor

React para importar livros, escolher o que revisar, acompanhar o processamento, conferir as correções, aprovar à mão quando ligado e baixar os Word. Execute `./scripts/dev.sh` na raiz; instalação e operação no [README principal](../README.md).

`App.tsx` escolhe a tela pelo estado do livro (`lib/screens.ts`) e monta cabeçalho ou barra inferior. `screens/` tem uma função por tela de `design/screens/`; `components/ui/` tem um componente por arquivo de `design/components/`, todos sobre as classes `rv-` de `design/components.css`. `useBooks.ts` mantém estado HTTP e polling. O proxy lê `REVIEW_API_PORT`, com padrão 8766.

Computador e celular (abaixo de 768px, `lib/viewport.ts`) seguem as telas de referência. Estado editorial é persistido pelo backend, não pelo navegador. LocalStorage recorda o livro selecionado, o tema, o tamanho do texto e a aprovação à mão de cada livro. Testes da lógica de telas e correções: `node --test src/lib/*.test.ts`. Polling usa abort/cancelamento na troca de trabalho e acompanha jobs em background.
