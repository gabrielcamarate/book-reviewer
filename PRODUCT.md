# Revisor e tradutor de livros

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Autores e revisores que precisam preparar livros em português e espanhol da América Latina, no desktop ou celular, com processamento completo e conferência manual opcional.

## Product Purpose

Corrigir erros objetivos em português brasileiro com mínima intervenção, preservar a voz da autora, validar/aplicar automaticamente as correções, traduzir o português estabilizado com consistência e revisar o espanhol comparando com a fonte. A conferência/aprovação manual permanece opcional. O resultado é uma nova cópia Word, com cobertura verificável e originais preservados.

## Operating Context

Uso local no navegador, Python/React e Codex CLI autenticado. Livro inteiro e seções específicas são escopos configuráveis; um Word espanhol existente pode receber somente as seções selecionadas.

## Capabilities and Constraints

Importação DOCX, seleção integral ou por seções, comparação original/proposta/tradução, motivos, aprovação/recusa/ajustes, glossário, lotes com progresso/parada/retomada e exportação. Modelo padrão confirmado: GPT 6.1 SOL low. Autorizações editoriais são explícitas; gerar uma proposta não a aprova. Tradução definitiva exige aprovação de todo o escopo. O app coordena um livro por vez, com até quatro chamadas simultâneas em cada etapa automática, e conserva checkpoints. A paginação pode variar com o texto traduzido.

## Evidence on Hand

Testes unitários, HTTP, fixtures fictícias e inspeções de UI/Word. Não há dataset literário rotulado nem certificação de publicação. A aprovação automática exige validação separada; o startup não processa manuscritos. Registros editoriais de usuários ficam fora do repositório.

## Product Principles

- Preservar originais, conteúdo fora do escopo e decisões do operador.
- Preservar correções, motivos e auditoria; distinguir validação/aprovação automática de aprovação humana.
- Cobrir todos os parágrafos escolhidos; bloquear resultado final incompleto.
- Salvar progresso e tornar falhas e retomada visíveis.
- Usar português claro na interface e espanhol da América Latina no resultado.

O progresso distingue propostas salvas, português aprovado, tradução e espanhol revisado. Falhas editoriais de um trecho deixam o restante avançar e oferecem navegação para conferência; a passagem ao espanhol e a entrega respeitam as barreiras de cobertura completa. No automático, o modelo fornece parágrafos finais e motivos e o aplicativo calcula as diferenças; o autor não precisa resolver interseções de recortes gerados pela IA.

O autor recebe observações sobre ambiguidades já existentes no original, preservadas fielmente. Elas não permitem inventar palavras, fatos ou unidades para tornar a história mais explícita. Erros não resolvidos das propostas/traduções continuam impedindo a entrega automática. Aprovação da IA continua distinta de aceite humano e de uma garantia de texto sem erros.
