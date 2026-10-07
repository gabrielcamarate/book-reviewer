# Fluxos de livros

Importe um Word português e selecione livro inteiro ou seções. Para inserir as seções traduzidas em um Word espanhol existente, indique esse destino na importação. Ocorrências no sumário não substituem os títulos do corpo.

O processamento completo revisa e valida o português, registra aprovação automática, traduz e revisa o espanhol e gera novas cópias Word. O modo manual permite conferir propostas e decidir aprovações/exportações.

Cada importação cria um trabalho independente em `.books/<uuid>/`. O original fica preservado e a inserção mantém o conteúdo fora do escopo.

A interface mostra propostas, português aprovado, tradução e espanhol revisado em contagens separadas. Pendências indicam trecho e motivo. Retomar reaproveita resultados válidos; o startup não processa livros por conta própria.

Os dados são privados e locais. Clonar este repositório fornece código e testes fictícios, sem livros ou andamento. [Operação](RUNBOOK.md).
