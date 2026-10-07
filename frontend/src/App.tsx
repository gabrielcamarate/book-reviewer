import { useState } from "react"

import { AppHeader, MobileHeader, type Area } from "@/components/ui/app-header"
import { TabBar } from "@/components/ui/tab-bar"
import { cn } from "@/lib/utils"
import { bookScreen } from "@/lib/screens"
import { useManual } from "@/lib/manual"
import { useIsMobile } from "@/lib/viewport"
import { AttentionScreen, DoneScreen, ProgressScreen, ReadyScreen, StoppedScreen, type BookView } from "@/screens/book"
import { BooksScreen } from "@/screens/books"
import { LegacyWorkspace } from "@/screens/legacy-workspace"
import { AlertsScreen, ChaptersScreen, GlossaryScreen, InstructionsScreen, NotesScreen, OptionsScreen } from "@/screens/options"
import { NewBookScreen, StartScreen } from "@/screens/start"
import { ErrorScreen, LoadingScreen } from "@/screens/status"
import { useBooks } from "@/useBooks"

function App() {
  const books = useBooks()
  const mobile = useIsMobile()
  const [area, setArea] = useState<Area>("book")
  const [view, setView] = useState<BookView | null>(null)
  const [origin, setOrigin] = useState<Area>("book")
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
    if (next === "books") void books.refreshList().catch(() => undefined)
    setArea(next)
    setView(null)
    window.scrollTo(0, 0)
  }
  function go(next: BookView) {
    setOrigin(area === "options" ? "options" : "book")
    setArea("book")
    setView(next)
    window.scrollTo(0, 0)
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
    books.setChunkId(chunkId)
    go("conferir")
  }
  const save = (operation: string, data?: unknown) => books.action(operation, data)
  const otherBook = books.projects.find(project => project.id === books.activeProjectId)

  function content() {
    if (screen === "carregando") return <LoadingScreen book={books.projects.length > 0} />
    if (screen === "erro") return <ErrorScreen onRetry={() => void books.retryLoading()} busy={busy} mobile={mobile} />
    if (view === "novo-livro" || (screen === "inicio" && area === "books"))
      return <NewBookScreen busy={books.busy === "import"} canCancel={books.projects.length > 0} onCancel={() => navigate("books")} onImport={importBook} />
    if (screen === "inicio") return <StartScreen onChoose={() => go("novo-livro")} />
    if (area === "books") return <BooksScreen projects={books.projects} activeProjectId={books.activeProjectId} onOpen={openBook} onNew={() => go("novo-livro")} />
    if (area === "options") return <OptionsScreen book={book} onBack={book ? () => navigate("book") : null} go={go} />
    if (book && view === "escolher-capitulos") return <ChaptersScreen key={book.id} book={book} busy={busy} onBack={back} save={save} />
    if (book && view === "orientacoes") return <InstructionsScreen key={book.id} book={book} busy={busy} onBack={back} save={save} />
    if (book && view === "glossario") return <GlossaryScreen key={`${book.id}-${book.revision}`} book={book} busy={busy} onBack={back} save={save} />
    if (book && view === "alertas") return <AlertsScreen book={book} onBack={back} onOpenChunk={openChunk} />
    if (book && view === "observacoes") return <NotesScreen book={book} onBack={back} onOpenChunk={openChunk} />
    if (view || !book) return <LegacyWorkspace books={books} />
    if (screen === "pronto-para-comecar") return <ReadyScreen book={book} busy={busy} go={go} onStart={() => void books.action("start", { task: "automatic" })} />
    if (screen === "outro-livro") return <ReadyScreen book={book} busy={busy} go={go} onStart={() => undefined} otherBook={otherBook && { name: otherBook.name, onFollow: () => openBook(otherBook.id) }} />
    if (screen === "acompanhar") return <ProgressScreen book={book} busy={busy} go={go} onPause={() => void books.action("stop")} />
    if (screen === "livro-pronto") return <DoneScreen book={book} busy={busy} go={go} onDownload={language => void books.download(language)} />
    const other = Boolean(books.activeProjectId && books.activeProjectId !== book.id)
    const resume = () => void books.action("start", { task: "automatic" })
    if (screen === "pausado" || screen === "parou-no-meio") return <StoppedScreen book={book} busy={busy} go={go} onContinue={resume} disabled={other} failed={screen === "parou-no-meio"} />
    if (screen === "precisa-de-atencao") return <AttentionScreen book={book} busy={busy} go={go} onContinue={resume} disabled={other} onOpenChunk={openChunk} />
    return <LegacyWorkspace books={books} />
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
