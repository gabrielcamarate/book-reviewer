# Interface do revisor

React para importar livros, escolher escopo, revisar/aprovar, acompanhar lotes, traduzir e baixar Word. Execute `./scripts/dev.sh` na raiz; instalação e operação no [README principal](../README.md).

`App.tsx`, `useBooks.ts` e `components/book-*` compõem o fluxo novo. `components/ui` contém primitivas locais existentes. O proxy lê `REVIEW_API_PORT`, com padrão 8766.

Desktop compara original, português e espanhol lado a lado; celular usa abas. Estado editorial é persistido pelo backend, não pelo navegador. LocalStorage recorda somente o livro selecionado. Polling usa abort/cancelamento na troca de trabalho e acompanha jobs em background.
