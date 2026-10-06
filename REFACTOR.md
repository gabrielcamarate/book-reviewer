# Arquitetura consolidada

Uma interface React e um pacote Python substituem interfaces duplicadas e pacotes sem consumidores. API e CLI compartilham o núcleo editorial. O acervo anterior é opcional e permanece separado dos trabalhos importados.

A orquestração automática fica em book_pipeline.py; persistência e guardas ficam em workspace.py; contratos de parágrafos e terminologia ficam em book_response.py e book_terms.py. Isso mantém filas e validações independentes da interface.

Refactors preservam dados locais. A distribuição pública contém apenas código, testes fictícios e documentação genérica. Livros e relatórios pessoais não são necessários para instalar, iniciar ou executar os testes.

As verificações aplicáveis estão em scripts/ci.sh e na integração GitHub Actions. As limitações editoriais ficam em README.md e AUTOMATIC.md.
