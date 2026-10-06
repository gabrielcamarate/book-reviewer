# Distribuição do código

A branch main distribui a versão atual do aplicativo com histórico próprio, sem manuscritos, arquivos Word/PDF, revisões pessoais, livros importados, credenciais ou provas editoriais de usuários. A documentação usa caminhos relativos e exemplos fictícios.

Instalação: clone main, instale o frontend com o lockfile e inicie scripts/dev.sh. O app começa sem livros; os Word são importados pela interface. Dados locais e andamento ficam em .books e não são sincronizados pelo Git.

Gates de distribuição: verificar a árvore e os exemplos publicados, executar scripts/ci.sh numa cópia sem acervo pessoal, executar Bandit e conferir o startup vazio. O check do acervo anterior continua exigido quando seus índices estão presentes. Uma fórmula do glossário anterior é derivada do texto aprovado, sem frases de um livro embutidas no código.

Ferramentas: leituras/Git/rg nos caminhos confirmados, sem descoberta semântica necessária. Pruner dispensado por histórico com conteúdo privado; nenhum histórico enviado. Test Filter dispensado para testes rápidos e gates finais completos. Smoke de UI usa Jev Browser oficial e documentos fictícios. Hunch é consultivo e recebe somente fonte pública atual, sem diffs que revelem dados removidos. Não há avaliação literária calibrada nem ganho de economia medido.

A distribuição de código não substitui revisão editorial pelo autor, não publica o app na internet e não transporta autenticação do provedor. Registros de execução e livros permanecem em backup privado do operador.

Verificação local da distribuição: 122 testes (5,820 s), lint, TypeScript/Vite e Bandit aprovados numa cópia sem acervo. Jev Browser oficial confirmou formulário inicial, placeholder fictício, zero livros e zero erros de console. Hunch revisou somente quatro arquivos públicos atuais: seis chunks, 12 perguntas, seis requests, 14.746 input tokens; resultado completo, sem findings, notices ou falhas. Flags incompatíveis com whole-file review e um assert de atributo não suportado foram recusados e corrigidos antes da verificação, sem mutações duplicadas.

As fixtures foram neutralizadas sem reduzir asserções. Uma regressão inicialmente falhou porque o glossário dependia de frases específicas de livro; a fórmula agora usa segmentos do texto aprovado, com caso negativo para pausa curta. Duas diferenças entre exemplos novos e expectativas antigas foram corrigidas; o gate final completo passou. A primeira instalação offline não tinha todas as dependências no cache; instalação normal com lockfile completou o cache e a cópia final instalou corretamente.
