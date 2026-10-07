# Revisor e tradutor — orientações

Responda em pt-BR. O produto é um aplicativo local para revisão editorial em português e tradução para espanhol. Preserve a voz do autor. A interface segue o design descrito em `design/`.

## Arquitetura e escopo

Leia README.md, ARCHITECTURE.md e TASKS.md antes de trabalho relevante. Há uma interface React e um pacote Python em backend/revisor. API e CLI chamam o mesmo serviço; regras editoriais ficam no núcleo e modelos no adaptador provider.py. Não reintroduza páginas HTML, dashboards paralelos, monorepo de pacotes vazios ou canais futuros sem necessidade explícita.

O manuscrito, segmentação e registros editoriais são dados do usuário. Preserve livro.docx, manuscript/, editorial/, reviews/, reports/ e deliverables/ durante refactors. Revisão aplicada grava estado consolidado e auditoria, nunca sobrescreve o original. Não regenere índices ou normalize aprovações reais durante testes.

## Editorial e modelos

Separe correção objetiva, polimento opcional e tradução. Corrija com mínima intervenção; preserve nomes, termos, repetições intencionais e estilo. A tradução definitiva parte de português estabilizado. Prévia não é aprovação. O usuário autorizou um modo automático: validação separada antes de autoaprovação registrada, revisão bilíngue antes da entrega, sem escore de confiança inventado. Modo manual permanece disponível. Persistir sugestão, motivo e proveniência é obrigatório.

Jev fornece julgamentos, não gera traduções. Avaliação de qualidade e limiares exigem exemplos reais rotulados; testes com runners controlados comprovam software, não qualidade literária. Não envie o manuscrito real em experimentos por consequência de um refactor.

## Desenvolvimento

- Neste projeto, mantenha somente `main` e o checkout principal, conforme pedido do usuário. Não deixe branches ou worktrees auxiliares após concluir tarefas. Preserve processos ativos e trabalho desconhecido; não faça reset/stash/clean indiscriminado.
- Planeje mudanças estruturais e registre evidências em REFACTOR.md quando pertinente.
- Para comportamento novo/corrigido, escreva primeiro a prova de regressão; mantenha testes do núcleo. Testes de funcionalidades explicitamente aposentadas podem ser removidos junto com elas.
- Use scripts/jail.sh quando viável para validação isolada. Não copie credenciais para containers.
- Gates: scripts/ci.sh e Bandit no backend. UI deve ter smoke isolado e inspeção visual proporcionais.
- README, arquitetura, operação, tarefas e changelog devem refletir a mesma revisão.
- Commits Conventional Commits após verificação; push, merge, deploy e publicação só com autorização específica.
- Toda mudança de comportamento, configuração, tooling, contrato ou `design/` prepara uma versão e a nota no CHANGELOG no mesmo commit, conforme [RELEASES.md](RELEASES.md). A publicação da tag e da release após CI verde na `main` é automática e foi autorizada em 07/10/2026; ela não autoriza push. Confira a release antes de relatar conclusão.

## Frontend

O design do app está em `design/`. Leia `design/README.md` antes de qualquer mudança de interface e `design/IMPLEMENTACAO.md` enquanto a migração para esse design estiver em curso. Cores, espaços, raios, tamanhos e estilos de texto vêm de `design/tokens.json`; não escreva valores soltos no código. As telas de referência ficam em `design/screens/` e as regras de cada componente em `design/components/`. Quando o design mudar, atualize `design/` na mesma revisão que o código.

Use as skills instaladas relevantes: vercel-react-best-practices para React; frontend-design para apresentação; tailwind-design-system para estilos; shadcn para componentes; web-design-guidelines para auditoria de UI. Componentes existentes têm fontes locais, sem dependência do gerador shadcn no runtime. Consulte sua interface oficial ao acrescentar/atualizar componentes; não crie um segundo design system.

## Ferramentas pessoais

Siga a autorização My Tools da sessão e a referência tool-routing.md da skill gabriel-* aplicada. Busca sem localização confirmada usa Siftr primeiro; símbolos conhecidos usam rg. Checks extensos elegíveis usam o wrapper Pruner, respeitando a autorização do histórico. Smoke isolado usa Jev Browser oficial. Registre chamadas e dispensas concretas; não invente ganhos nem dependências só para acionar ferramentas.
