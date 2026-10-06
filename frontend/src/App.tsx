import { useState } from "react"
import { BookOpenIcon, CheckIcon, DownloadIcon, LanguagesIcon, PauseIcon, RefreshCwIcon, SparklesIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { BookSetup, ImportBook, NewBookButton } from "@/components/book-setup"
import { BookReader } from "@/components/book-reader"
import { BookGlossary } from "@/components/book-glossary"
import { BookProgress, BookJobStatus } from "@/components/book-processing"
import { useBooks } from "@/useBooks"
import LegacyReview from "@/LegacyReview"

function App() {
  const books = useBooks()
  const [importOpen, setImportOpen] = useState(false)
  const [legacyOpen, setLegacyOpen] = useState(false)
  const [approvalOpen, setApprovalOpen] = useState(false)
  const [manualOpen, setManualOpen] = useState(false)
  const [limit, setLimit] = useState("")
  const [setupDirty, setSetupDirty] = useState(false)
  const book = books.detail
  const running = ["running", "stopping"].includes(book?.job?.status ?? "")
  const disabled = Boolean(books.busy) || Boolean(books.activeProjectId) || running || setupDirty
  const allApproved = Boolean(book?.progress.total_paragraphs) && book?.progress.approved_paragraphs === book?.progress.total_paragraphs
  const allTranslated = allApproved && book?.progress.translated_paragraphs === book?.progress.total_paragraphs
  const locked = book?.chunks.some(c => c.status !== "pending") ?? false
  if (legacyOpen) return <><div className="legacy-nav"><Button variant="outline" onClick={() => setLegacyOpen(false)}>Voltar aos livros</Button><span>Trabalho editorial anterior</span></div><LegacyReview /></>
  async function start(task: "review" | "translate" | "automatic", currentOnly = false) {
    await books.action("start", { task, ...(task !== "automatic" && limit ? { limit: Number(limit) } : {}), ...(currentOnly ? { chunk_id: book?.current?.id } : {}) })
  }
  return <div className="book-app">
    <a href="#book-main" className="skip-link">Ir para o livro</a>
    <header className="app-topbar"><div className="app-brand"><BookOpenIcon aria-hidden="true" /><span>Revisor</span></div><nav aria-label="Ações do aplicativo"><NewBookButton onClick={() => setImportOpen(true)} disabled={disabled} />{books.legacy && <Button variant="ghost" onClick={() => setLegacyOpen(true)} disabled={disabled}>Revisão anterior</Button>}</nav></header>
    <div className="workspace-layout">
      <aside className="book-sidebar" aria-label="Seus livros"><div className="sidebar-title"><h2>Seus livros</h2><Button variant="ghost" size="icon" aria-label="Atualizar lista de livros" disabled={Boolean(books.busy)} onClick={() => void books.retryLoading()}><RefreshCwIcon /></Button></div>
        {books.projects.length ? <ul className="book-list">{books.projects.map(project => <li key={project.id}><button className="book-list-item" aria-current={books.projectId === project.id ? "page" : undefined} onClick={() => { books.selectProject(project.id); setImportOpen(false); setSetupDirty(false) }} disabled={Boolean(books.busy)}><span>{project.name}</span><small>{project.progress.translation_percent === 100 ? `Espanhol revisado ${project.progress.checked_percent}%` : project.progress.review_percent === 100 ? `Tradução ${project.progress.translation_percent}%` : project.progress.draft_percent > project.progress.review_percent ? `Propostas ${project.progress.draft_percent}% · aprovado ${project.progress.review_percent}%` : `Revisão ${project.progress.review_percent}%`}</small></button></li>)}</ul> : <p className="sidebar-empty">Os livros importados aparecerão aqui.</p>}
        <p className="sidebar-note">Português brasileiro<br />Espanhol da América Latina</p>
      </aside>
      <main id="book-main" className="book-main">
        {books.error && <div role="alert" className="message error-message">{books.error}<Button variant="ghost" disabled={Boolean(books.busy)} onClick={() => void books.retryLoading()}>Atualizar</Button></div>}
        {books.notice && <p role="status" className="message">{books.notice}</p>}
        {books.activeProjectId && books.activeProjectId !== books.projectId && <div className="message" role="status">Há um processamento em outro livro. <Button variant="link" onClick={() => books.selectProject(books.activeProjectId!)}>Acompanhar o livro em processamento</Button></div>}
        {(importOpen || (!books.projects.length && books.busy !== "loading")) && <ImportBook busy={books.busy === "import"} onCancel={books.projects.length ? () => setImportOpen(false) : undefined} onImport={async (...args) => { const ok = await books.importBook(...args); if (ok) setImportOpen(false); return ok }} />}
        {books.busy === "loading" && <div className="loading-state" role="status"><Spinner />Carregando seus livros…</div>}
        {!importOpen && books.projectId && !book && books.busy !== "loading" && <div className="loading-state" role="status"><Spinner />Abrindo o livro…</div>}
        {!importOpen && book && <>
          <header className="book-heading"><h1>{book.name}</h1><p className="source-filename" title={book.filename}>{book.filename}</p><p>Receba seu livro revisado em português e traduzido para espanhol da América Latina.</p></header>
          <BookSetup key={`setup-${book.id}`} book={book} locked={locked} busy={Boolean(books.busy) || Boolean(books.activeProjectId) || running} onDirty={() => setSetupDirty(true)} onSave={async data => { const result = await books.action("configure", data); if (result) setSetupDirty(false); return result }} />
          {setupDirty && <p role="status" className="field-help">Salve as mudanças de escopo e critérios antes de iniciar o processamento.</p>}
          <BookProgress book={book} />
          <section className="processing-panel" aria-label="Processamento do livro">
            <h2>Do manuscrito ao Word revisado</h2>
            <p>Revisão do português, validação das correções e aplicação automática, tradução e revisão do espanhol. Você pode acompanhar, interromper e retomar.</p>
            <div className="processing-actions"><Button size="lg" onClick={() => void start("automatic")} disabled={disabled || Boolean(book.automatic_result)}><SparklesIcon data-icon="inline-start" />{running ? "Processando…" : book.automatic_result ? "Processamento concluído" : book.job?.status === "needs_attention" ? "Tentar os trechos pendentes" : book.job?.task === "automatic" && ["paused", "failed", "interrupted", "completed"].includes(book.job.status) ? "Continuar processamento" : book.settings.scope === "whole" ? "Processar livro completo" : "Processar seções selecionadas"}</Button>
              {running && <Button variant="outline" onClick={() => void books.action("stop")} disabled={Boolean(books.busy) || book.job?.status === "stopping"}><PauseIcon data-icon="inline-start" />Parar após operações em andamento</Button>}</div>
            <BookJobStatus book={book} onInspect={chunkId => { books.setChunkId(chunkId); setManualOpen(true); document.getElementById("chunk-select")?.focus() }} />
            {book.automatic_result && <p role="status" className="message">Processamento completo concluído. Os dois arquivos Word estão disponíveis abaixo.</p>}
            <details className="batch-options" open={manualOpen} onToggle={event => setManualOpen(event.currentTarget.open)}><summary>Modo manual — conferir e aprovar as propostas</summary>
              <div className="processing-actions"><Button variant="outline" onClick={() => void start("review")} disabled={disabled || book.progress.pending_chunks === 0}><SparklesIcon data-icon="inline-start" />Revisar pendentes</Button>{book.progress.ready_chunks > 0 && <Button variant="outline" onClick={() => setApprovalOpen(true)} disabled={disabled}><CheckIcon data-icon="inline-start" />Aprovar propostas ({book.progress.ready_chunks})</Button>}<Button variant="outline" onClick={() => void start("translate")} disabled={disabled || !allApproved || allTranslated}><LanguagesIcon data-icon="inline-start" />{book.progress.translated_paragraphs ? "Continuar tradução" : "Traduzir para espanhol"}</Button></div>
              <label htmlFor="batch-limit">Quantidade de trechos <span>(vazio = todo o escopo)</span></label><input id="batch-limit" type="number" min={1} max={100000} value={limit} onChange={event => setLimit(event.target.value)} disabled={disabled} inputMode="numeric" />
              <p className="field-help">Aqui você aprova as propostas e decide quando exportar. O processamento completo faz a validação e a revisão do espanhol automaticamente.</p>
            </details>
          </section>
          {book.current && <div className="chunk-navigation"><label htmlFor="chunk-select">Trecho</label><select id="chunk-select" value={book.current.id} onChange={event => books.setChunkId(event.target.value)} disabled={Boolean(books.busy)}>{book.chunks.map((chunk, index) => <option key={chunk.id} value={chunk.id}>{index + 1}. {chunk.title} · {chunk.translated ? "traduzido" : ({ pending: "pendente", ready: "conferir proposta", approved: "aprovado", rejected: "recusado" })[chunk.status]}</option>)}</select>{["pending", "rejected"].includes(book.current.status) && <Button variant="outline" disabled={disabled} onClick={() => void start("review", true)}>Revisar este trecho</Button>}</div>}
          <BookReader key={`${book.id}-${book.current?.id}-${book.current?.proposal_id}-${Boolean(book.current?.translations)}`} book={book} disabled={disabled} action={books.action} />
          {book.consistency_warnings.length > 0 && <section className="consistency-panel"><h2>Conferir consistência ({book.consistency_warnings.length})</h2><p>São alertas para conferência; formas literárias e flexões podem ser intencionais.</p><ul>{book.consistency_warnings.map((warning, index) => <li key={index}><button onClick={() => books.setChunkId(warning.chunk_id)}>{warning.message}</button></li>)}</ul></section>}
          {locked && <BookGlossary key={`glossary-${book.id}`} book={book} disabled={Boolean(books.busy) || Boolean(books.activeProjectId) || running} onDirty={setSetupDirty} action={books.action} />}
          {Boolean(book.editorial_notes?.length) && <details className="consistency-panel"><summary>Observações para a autora ({book.editorial_notes!.length})</summary><p>Expressões ambíguas ou incompletas do original foram preservadas. As observações ficam registradas para sua decisão, sem inventar informações no livro.</p><ul>{book.editorial_notes!.map((note, index) => <li key={index}><button onClick={() => books.setChunkId(note.chunk_id)}>Trecho {note.index}: {note.title} · {note.language === "pt" ? "Português" : "Espanhol"}</button><p>{note.message}</p></li>)}</ul></details>}
          <footer className="export-panel"><div><h2>Baixar o resultado em Word</h2><p>{book.destination_filename ? "O espanhol será inserido numa cópia do livro de destino." : "O resultado preserva a estrutura e a formatação do Word. A paginação pode mudar com o texto."}</p></div><div className="actions"><Button variant="outline" disabled={disabled || !allApproved || (!manualOpen && !book.automatic_result)} onClick={() => void books.download("pt-BR")}><DownloadIcon data-icon="inline-start" />Word revisado em português</Button><Button disabled={disabled || !allTranslated || (!manualOpen && !book.automatic_result)} onClick={() => void books.download("es")}><DownloadIcon data-icon="inline-start" />Word em espanhol</Button></div></footer>
        </>}
        <p className="app-footnote">GPT 6.1 SOL · esforço low · Processamento automático com histórico de alterações · Modo manual disponível.</p>
      </main>
    </div>
    <Dialog open={approvalOpen} onOpenChange={setApprovalOpen}><DialogContent><DialogHeader><DialogTitle>Aprovar {book?.progress.ready_chunks ?? 0} propostas?</DialogTitle><DialogDescription>As correções propostas serão aplicadas aos trechos já revisados. Confira as propostas antes de aprovar. Você pode reabrir qualquer trecho depois.</DialogDescription></DialogHeader><DialogFooter><Button variant="outline" onClick={() => setApprovalOpen(false)}>Voltar para conferir</Button><Button disabled={disabled} onClick={() => void books.action("approve-all", { revision: book?.revision }).then(result => { if (result) setApprovalOpen(false) })}>Aprovar propostas revisadas</Button></DialogFooter></DialogContent></Dialog>
  </div>
}

export default App
