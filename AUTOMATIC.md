# Processamento automático

O fluxo principal cobre o escopo escolhido: revisão pt-BR, validação independente e aprovação registrada, tradução es-419, revisão bilíngue e geração dos Word. O modo manual permanece opcional.

Cada fase usa até quatro chamadas simultâneas, salva resultados independentes e respeita parada/retomada. A tradução exige todo o português aprovado. A entrega exige cobertura espanhola completa, checks atuais, ausência de alertas remanescentes e ZIP/XML válidos.

No automático, o modelo fornece exatamente um texto completo por parágrafo, com justificativa das mudanças. O código valida IDs, ordem, conteúdo e quebras e calcula diferenças sem sobreposições. Respostas inválidas têm uma segunda tentativa com feedback; pendências não descartam resultados válidos de outros trechos. Falhas de provedor e conflitos de estado interrompem o processamento.

Ambiguidades do original preservadas ficam em observações para o autor. Informações ausentes não são inventadas. Erros remanescentes das correções/traduções continuam bloqueando a entrega. Glossário efetivo considera palavras inteiras, expressões específicas, número, maiúsculas e contrações espanholas.

Receipts registram modelo, contrato, assinatura do conteúdo, alterações e observações. Mudanças no texto, glossário ou contrato invalidam resultados afetados. Uma entrega antiga não representa a revisão atual.

As regressões de software cobrem cobertura, filas, retomada, preservação, validação bilíngue, Word e HTTP. Fixtures são fictícias. A validação do software não certifica qualidade literária geral ou diagramação exigida por uma plataforma editorial.

Livros reais, resultados editoriais e provas pessoais permanecem fora do Git. Consulte [Operação](RUNBOOK.md) e [Publicação](PUBLICATION.md).
