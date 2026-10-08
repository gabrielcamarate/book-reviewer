import { useState } from "react"

import { AppHeader, MobileHeader, type Area } from "@/components/ui/app-header"
import { TabBar } from "@/components/ui/tab-bar"
import { cn } from "@/lib/utils"
import { bookScreen } from "@/lib/screens"
import { setManual, useManual } from "@/lib/manual"
import { useIsMobile } from "@/lib/viewport"
import { AttentionScreen, DoneScreen, ProgressScreen, ReadyScreen, StoppedScreen, type BookView } from "@/screens/book"
import { BooksScreen } from "@/screens/books"
import { AuthorEditScreen, AuthorReviewScreen, AuthorSpanishScreen, ManualAdjustScreen, ManualChunkScreen, ManualRefuseScreen, ManualScreen } from "@/screens/manual"
import { AlertsScreen, ChaptersScreen, GlossaryScreen, InstructionsScreen, NotesScreen, OptionsScreen } from "@/screens/options"
import { AdjustPortugueseScreen, AdjustSpanishScreen, ChunksScreen, ReviewScreen, type Pane } from "@/screens/review"
import { Notice } from "@/components/ui/notice"
import { Button } from "@/components/ui/button"
import { NewBookScreen, StartScreen } from "@/screens/start"
import { ErrorScreen, LoadingScreen } from "@/screens/status"
import { useBooks } from "@/useBooks"

function App() {
  const books = useBooks()
  const mobile = useIsMobile()
  const [area, setArea] = useState<Area>("book")
  const [view, setView] = useState<BookView | null>(null)
  const [origin, setOrigin] = useState<Area>("book")
  const [pane, setPane] = useState<Pane>("changes")
  const [saved, setSaved] = useState(false)
  const book = books.detail
  const manual = useManual(book?.id ?? null)
  const busy = Boolean(books.busy)
  const screen = bookScreen({
    loading: books.busy === "loading",
    error: books.error,
    hasBooks: books.projects.length > 0,
    book,
    activeProjectId: books.activeProjectId,
    manual,
  })
  function navigate(next: Area) {
    setSaved(false)
    if (next === "books") void books.refreshList().catch(() => undefined)
    setArea(next)
    setView(null)
    window.scrollTo(0, 0)
  }
  function go(next: BookView, chunkId?: string) {
    // A finished book opens at its first chunk; while working, the server picks the next one waiting.
    const target = chunkId ?? (next === "conferir" && !books.chunkId && book?.chunks.every(chunk => chunk.status === "approved") ? book.chunks[0]?.id : undefined)
    const from = area === "options" ? "options" : "book"
    const open = () => {
      if (next === "conferir") setPane("changes")
      setOrigin(from)
      setArea("book")
      setView(next)
      window.scrollTo(0, 0)
    }
    // Stay on the current screen, with the button spinning, until the chunk's text has arrived.
    if (target) return books.showChunk(target).then(open)
    open()
    return Promise.resolve()
  }
  function openBook(id: string) {
    books.selectProject(id)
    navigate("book")
  }
  async function importBook(name: string, source: File, destination?: File) {
    const ok = await books.importBook(name, source, destination)
    if (ok) { setArea("book"); setView(destination ? "escolher-capitulos" : null) }
    return ok
  }
  function back() {
    setView(null)
    setArea(origin)
    window.scrollTo(0, 0)
  }
  function openChunk(chunkId: string) {
    return go("conferir", chunkId)
  }
  async function showChunk(chunkId: string) {
    await books.showChunk(chunkId)
    window.scrollTo(0, 0)
  }
  function inBook(next: BookView) {
    setSaved(false)
    setView(next)
    window.scrollTo(0, 0)
  }
  const save = (operation: string, data?: unknown) => books.action(operation, data)
  async function act(operation: string, data?: unknown) {
    const result = await books.action(operation, data)
    // Approving keeps the same chunk on screen, now marked as approved.
    if (result && operation === "approve") books.setChunkId((data as { chunk_id: string }).chunk_id)
    return result
  }
  const otherBook = books.projects.find(project => project.id === books.activeProjectId)

  function content() {
    if (screen === "carregando") return <LoadingScreen book={books.projects.length > 0} />
    if (screen === "erro") return <ErrorScreen onRetry={() => books.retryLoading()} busy={busy} mobile={mobile} />
    if (view === "novo-livro" || (screen === "inicio" && area === "books"))
      return <NewBookScreen busy={books.busy === "import"} canCancel={books.projects.length > 0} onCancel={() => navigate("books")} onImport={importBook} />
    if (screen === "inicio") return <StartScreen onChoose={() => go("novo-livro")} />
    if (area === "books") return <BooksScreen projects={books.projects} activeProjectId={books.activeProjectId} onOpen={openBook} onNew={() => go("novo-livro")} />
    if (area === "options") return <OptionsScreen book={book} busy={busy} save={save} onRemove={() => books.removeBook(book!.id).then(ok => { if (ok) navigate("books") })} onBack={book ? () => navigate("book") : null} go={go} />
    if (book && view === "escolher-capitulos") return <ChaptersScreen key={book.id} book={book} busy={busy} onBack={back} save={save} />
    if (book && view === "orientacoes") return <InstructionsScreen key={book.id} book={book} busy={busy} onBack={back} save={save} />
    if (book && view === "glossario") return <GlossaryScreen key={`${book.id}-${book.revision}`} book={book} busy={busy} onBack={back} save={save} />
    if (book && view === "alertas") return <AlertsScreen book={book} onBack={back} onOpenChunk={openChunk} />
    if (book && view === "observacoes") return <NotesScreen book={book} busy={busy} onBack={back} onOpenChunk={openChunk} onAdjustChunk={chunkId => go("ajustar-portugues", chunkId)} save={save} />
    const running = book?.job?.status === "running" || book?.job?.status === "stopping"
    const savedNotice = saved && <Notice plain action={<Button onClick={() => back()}>Voltar ao livro</Button>}><strong>Ajuste salvo.</strong> Para atualizar o espanhol e os arquivos Word, volte ao livro e continue o processamento.</Notice>
    if (book?.current?.status === "approved" && view === "ajustar-portugues") return <AdjustPortugueseScreen key={`${book.current.id}-${book.revision}`} book={book} busy={busy} onBack={() => inBook("conferir")} onSaved={() => { inBook("conferir"); setPane("changes"); setSaved(true) }} save={save} />
    if (book?.current && view === "revisar-manual") return <AuthorReviewScreen key={`${book.current.id}-${book.revision}`} book={book} busy={busy} act={act} onBack={back} onAdjust={() => inBook("ajustar-manual")} onApproved={() => inBook("escrever-espanhol")} />
    if (book?.current && view === "ajustar-manual") return <AuthorEditScreen key={book.current.id} book={book} busy={busy} act={act} onBack={() => inBook("revisar-manual")} onApproved={() => inBook("escrever-espanhol")} />
    if (book?.current?.author_handled && book.current.revised && view === "escrever-espanhol") return <AuthorSpanishScreen key={`${book.current.id}-es`} book={book} busy={busy} act={act} onBack={back} onSaved={back} />
    if (book && manual && view === "conferir") return <>{savedNotice}<ManualChunkScreen key={book.current?.id} book={book} busy={busy} act={act} onBack={back} onChunk={showChunk} onList={() => inBook("trechos")} onAdjust={() => inBook(book.current?.status === "approved" ? "ajustar-portugues" : "ajustar-texto")} onRefuse={() => inBook("recusar")} /></>
    if (book?.current?.revised && view === "ajustar-texto") return <ManualAdjustScreen key={book.current.id} book={book} busy={busy} act={act} onDone={() => inBook("conferir")} />
    if (book?.current && view === "recusar") return <ManualRefuseScreen key={book.current.id} book={book} busy={busy} act={act} onDone={() => inBook("conferir")} />
    if (book && view === "conferir") return <>{savedNotice}<ReviewScreen book={book} pane={pane} onPane={setPane} onBack={back} onChunk={showChunk} onList={() => inBook("trechos")} onAdjust={() => inBook("ajustar-espanhol")} onAdjustPortuguese={running ? undefined : () => inBook("ajustar-portugues")} /></>
    if (book && view === "trechos") return <ChunksScreen book={book} onBack={() => inBook("conferir")} onOpen={chunkId => showChunk(chunkId).then(() => inBook("conferir"))} />
    if (book?.current?.translations && view === "ajustar-espanhol") return <AdjustSpanishScreen key={`${book.current.id}-${book.revision}`} book={book} busy={busy} onBack={() => { setPane("spanish"); inBook("conferir") }} save={save} />
    if (!book) return <LoadingScreen book />
    if (view) return <ReviewScreen book={book} pane={pane} onPane={setPane} onBack={back} onChunk={showChunk} onList={() => inBook("trechos")} onAdjust={() => inBook("ajustar-espanhol")} />
    if (screen === "pronto-para-comecar") return <ReadyScreen book={book} busy={busy} go={go} onStart={() => books.action("start", { task: "automatic" })} />
    if (screen === "outro-livro") return <ReadyScreen book={book} busy={busy} go={go} onStart={() => undefined} otherBook={otherBook && { name: otherBook.name, onFollow: () => openBook(otherBook.id) }} />
    if (screen === "acompanhar") return <ProgressScreen book={book} busy={busy} go={go} onPause={() => books.action("stop")} />
    if (screen === "livro-pronto") return <DoneScreen book={book} busy={busy} go={go} onDownload={language => void books.download(language)} />
    const other = Boolean(books.activeProjectId && books.activeProjectId !== book.id)
    const resume = () => books.action("start", { task: "automatic" })
    if (screen === "pausado" || screen === "parou-no-meio") return <StoppedScreen book={book} busy={busy} go={go} onContinue={resume} disabled={other} failed={screen === "parou-no-meio"} />
    if (screen === "precisa-de-atencao") return <AttentionScreen book={book} busy={busy} go={go} onContinue={resume} disabled={other} onOpenChunk={openChunk}
      onManual={chunkId => go("revisar-manual", chunkId)} onSpanish={chunkId => go("escrever-espanhol", chunkId)}
      // The model then translates what it accepts in this chunk; only the rest is left for the author.
      onTakeSpanish={async chunkId => { if (await act("author-take-spanish", { chunk_id: chunkId, revision: book.revision })) await resume() }} />
    return <ManualScreen book={book} busy={busy} act={act} onAutomatic={() => setManual(book.id, false)} onNext={openChunk} onList={() => go("trechos")} onDownload={language => void books.download(language)} />
  }

  return (
    <div className="rv-app">
      <a href="#conteudo" className="rv-skip">Ir para o conteúdo</a>
      {mobile ? <MobileHeader /> : <AppHeader current={area} onNavigate={navigate} />}
      <main id="conteudo" className={cn("rv-page", mobile && "rv-page--mobile", screen === "carregando" && "rv-page--center")}>
        {books.error && screen !== "erro" && <p className="rv-error" role="alert">{books.error}</p>}
        {content()}
      </main>
      {mobile && <TabBar current={area} onNavigate={navigate} />}
    </div>
  )
}

export default App
