# Changelog

Mudanças relevantes do Revisor, em português. Datas em UTC. `VERSION` identifica o
aplicativo inteiro (interface e backend). Fluxo em [RELEASES.md](RELEASES.md).

## [Unreleased]

## [0.8.0] - 2026-10-07

### Adicionado

- Telas do novo design para quando o trabalho sai do caminho: pausado, parou no meio (computador desligado ou servidor reiniciado) e trechos que precisam de atenção, cada uma com o que está salvo, as etapas e a ação para continuar.

## [0.7.0] - 2026-10-07

### Adicionado

- Telas do novo design para começar e acompanhar um livro: início, Meus livros, novo livro (com a opção de Word em espanhol), pronto para começar, livro na fila (outro em processamento), acompanhar as quatro etapas e livro pronto com os dois downloads.

### Alterado

- Importar valida tipo e tamanho do Word antes do envio e explica o problema numa frase.
- "Pausar" mostra "Pausando…" enquanto termina o que já começou.

## [0.6.0] - 2026-10-07

### Adicionado

- Estrutura do novo design: cabeçalho com "Meus livros", "Mais opções" e o tema no computador; barra inferior "Livro", "Meus livros" e "Opções" no celular; link para pular ao conteúdo.
- Escolha da tela pelo estado do livro (carregando, erro, início, outro livro, pronto para começar, acompanhar, pausado, parou no meio, precisa de atenção, livro pronto, aprovar à mão), com testes em `node --test` no CI.
- Telas de carregando e de erro do servidor no novo design.
- Classes de layout das páginas em `design/components.css`.

### Alterado

- A lista de livros sai da barra lateral e vai para "Meus livros". Até o passo 4, o livro aberto ainda mostra a área de trabalho anterior dentro da estrutura nova.

## [0.5.0] - 2026-10-07

### Adicionado

- Componentes base do novo design em `frontend/src/components/ui/`: Button, TextLink, Card, Field, FilePicker, SegmentedControl, Choice, ProgressBar, Steps, Notice, Spinner, SummaryRows, ListItem, CorrectedParagraph, ConfirmDialog, AppHeader e TabBar, todos sobre as classes `rv-` de `design/components.css`.
- Seletor de tema Escuro/Claro pronto no AppHeader, para a estrutura nova.

### Alterado

- Telas atuais usam os botões, a barra de progresso e a caixa de confirmação do design. O botão de atualizar a lista ganhou texto.
- Celular é abaixo de 768px, registrado em `design/README.md`.

### Removido

- Primitivas shadcn sem uso (empty, hover-card, scroll-area, separator, label) e as dependências `class-variance-authority` e `tw-animate-css`.

## [0.4.0] - 2026-10-07

### Alterado

- Interface passa a usar os tokens de `design/tokens.css` (cores, espaços, raios, tamanhos e tipos), sem paleta própria no frontend. Primeiro passo da migração para o novo design.
- Tema escuro e claro: segue o sistema por padrão e guarda a escolha da pessoa no navegador, aplicado antes da primeira pintura.
- Newsreader substitui Fraunces nos títulos e no texto do livro; Manrope continua na interface.
- Favicon, ícone SVG e ícone de atalho do celular vêm de `design/assets/brand/`.

### Removido

- Regras de `.gitignore` e `.dockerignore` das pastas do acervo anterior, já fora do projeto.

## [0.3.0] - 2026-10-07

### Adicionado

- A lista de trechos em `/api/books/<id>` informa `corrections`, a quantidade de correções de cada trecho, para a tela de trechos do novo design.

### Removido

- Fluxo editorial anterior: tela "Revisão anterior", CLI `revisor.cli`, rotas `/api/simple-home`, `/api/translate`, `/api/export`, `/api/rollback`, `/downloads/ptbr` e `/downloads/es`, e o núcleo `core/`, `prompts/`, `schemas/` e `docx/writer.py` que só ele usava.
- `/api/books` deixa de informar `legacy_available`. O CI não procura mais o acervo `manuscript/`.

### Incompatibilidades

- `create_server` recebe a pasta raiz em vez de um `ReviewService`. Livros em `.books/` não mudam.

## [0.2.1] - 2026-10-07

### Alterado

- AGENTS.md referencia as skills `gabriel-*` do repositório canônico `my-skills`, com a skill de cada etapa adaptada ao fluxo só com `main`.

## [0.2.0] - 2026-10-07

Primeira versão formal: consolida o histórico anterior como pré-release.

### Design e versões

- Releases versionadas: `VERSION` é a fonte canônica, espelhada em `frontend/package.json` e `pyproject.toml`; o CI valida versão e changelog e a publicação da tag e da GitHub Release ocorre automaticamente após CI verde na `main`.
- Referência de design em `design/` passa a ser versionada: tokens, componentes, 35 telas, ícones e marca. AGENTS.md aponta para ela como fonte das decisões de interface.

### Distribuição em main

- Consolidação local e remota em uma única branch `main` e um checkout principal; branches antigas e arquivos exclusivos são arquivados antes da limpeza.
- Mantidas autoria a partir do criador do Word e exportações com o nome original + REVISADO, inclusive acentos e entregas já concluídas.

- Código atual publicado com histórico próprio, sem manuscritos, Word, resultados editoriais, credenciais ou registros pessoais.
- Instalação em outra máquina com caminhos relativos; novos clones começam sem livros.
- CI funciona sem acervo pessoal e mantém a validação de índices quando o acervo local existe.
- Regras de exclusão protegem dados e documentos pessoais no Git e no contexto Docker.

### Processamento completo

- Painéis de critérios e glossário recebem chaves React distintas, eliminando avisos repetidos e colisão de identidade em livros já revisados.

- Consistência usa palavras inteiras, expressões com prioridade, singular/plural e contrações del/al. Elimina alertas de ego/emprego e grama/programadores. Escolhas duplicadas por maiúsculas compartilham um glossário efetivo; override do autor prevalece.
- Revisão bilíngue recebe alertas de terminologia explicitamente, separando feedback de consistência de rejeição de formato.
- Sidebar mostra espanhol revisado quando a geração já terminou, mantendo visível a última etapa pendente.


- Observações do original preservado separadas de falhas nas correções/traduções: lacunas e termos possivelmente inventados ficam registrados sem inferir fatos. Falhas remanescentes continuam bloqueando. Recibo JSON e navegação por trecho para o autor.
- Mudanças no contrato de revisão invalidam a indicação automática de conclusão quando receipts espanhóis estão desatualizados.


- Respostas automáticas por parágrafo completo, com motivos e diferenças calculadas pelo código; elimina sobreposições propostas pelo modelo. Modo manual preserva seus contratos.
- Trechos com respostas inválidas ou pendências não impedem processamento independente; estado precisa de atenção, lista navegável e retomada preservam resultados válidos. Tradução e entrega mantêm barreiras de cobertura/validação completas.
- Quatro contagens cumulativas de parágrafos, tempo da execução e progresso por etapa; correções finais destacadas pela posição correta e motivos acessíveis após autoaprovação.


- Recuperação unificada de respostas inválidas: inclui tentativa de apagar parágrafo, âncora/formato/JSON incorretos, tradução incompleta e quebras alteradas. Mantidos limite de duas chamadas por operação, auditoria, bloqueio de resposta inválida e preservação do trabalho salvo.

- Correções sobrepostas: regras explícitas no prompt, recuperação automática com uma segunda tentativa apenas do trecho inválido e auditoria; falha persistente aponta o trecho e preserva as propostas já salvas. Modo manual, pendências editoriais, transporte e conflitos de estado não são repetidos automaticamente.

- Fluxo principal automático: revisão pt-BR, segunda validação e autoaprovação registrada, tradução es-419, revisão bilíngue e geração/verificação dos dois Word. Modo manual preservado.
- Até quatro chamadas simultâneas por fase, salvamento por assinatura de trecho, parada com drenagem e retomada sem repetir fases válidas.
- Pendências, cobertura incompleta e alertas de consistência impedem entrega automática. Alterações manuais invalidam os checks/resultados afetados.


### Fluxo de livros

- Desconexões durante respostas HTTP encerram somente a requisição, sem traceback ou segunda resposta de erro; regressão com reset TCP real e resposta seguinte válida.

- Trabalhos independentes com importação Word, escopo integral ou por seções e estado durável.
- Revisão conservadora pt-BR com motivos, aprovação versionada, recusa, ajustes e reabertura.
- Tradução es-419 de todo o escopo aprovado, incluindo títulos, com glossário persistente editável e alertas.
- Background com progresso, limite, parada após o trecho atual, recuperação e retomada.
- Exportação sobre o Word original e inserção em cópia espanhola, preservando conteúdo fora do escopo, imagens e estilos.
- Interface para desktop/celular e acesso preservado à revisão anterior.
- Padrão explícito GPT 6.1 SOL low no Codex exec.
- Regressões de cobertura, mutações inválidas, bloqueio concorrente, seleção sumário/corpo e estrutura DOCX.

### Consolidação (05/10/2026)

- Uma interface React e um pacote Python, substituindo interfaces duplicadas e seis workspaces separados.
- API local e CLI única compartilham revisão, aprovação, recusa, tradução em lote, rollback e exportação.
- Removidos dashboard avançado, busca/curadoria web, polimento obrigatório, canais futuros e preview remoto.
- Mantidos dados, IDs, trilha editorial, glossário, consistência baseada em regras e exportação com manifestos.
- Corrigidos aprovação de revisão sem alterações, progresso real e proteção contra aprovação de tela desatualizada.
- Aprovação completa inclui parágrafos sem correções; prévia e aplicação usam a mesma ordem de substituições.
- Modelo usa a configuração atual do Codex por padrão, com override, timeout, sessão efêmera e diretório isolado em sandbox de leitura.
- Leitura e exportação de Word rejeitam DTDs; interface compilada independe da pasta de dados do livro.
- Startup único com portas configuráveis, proxy correto e encerramento de ambos os processos.
- Removidos componentes, assets e dependências não usados; CI inclui frontend e backend.
