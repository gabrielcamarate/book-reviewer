# Arquitetura consolidada

Uma interface React e um pacote Python substituem interfaces duplicadas e pacotes sem consumidores. A API local opera os livros importados; o fluxo editorial anterior (CLI, `manuscript/` e rotas próprias) foi removido em 0.3.0.

A orquestração automática fica em book_pipeline.py; persistência e guardas ficam em workspace.py; contratos de parágrafos e terminologia ficam em book_response.py e book_terms.py. Isso mantém filas e validações independentes da interface.

Refactors preservam dados locais. A distribuição pública contém apenas código, testes fictícios e documentação genérica. Livros e relatórios pessoais não são necessários para instalar, iniciar ou executar os testes.

As verificações aplicáveis estão em scripts/ci.sh e na integração GitHub Actions. As limitações editoriais ficam em README.md e AUTOMATIC.md.
