import { useState } from "react"

import { AppHeader, MobileHeader, type Area } from "@/components/ui/app-header"
import { TabBar } from "@/components/ui/tab-bar"
import { cn } from "@/lib/utils"
import { bookScreen } from "@/lib/screens"
import { useIsMobile } from "@/lib/viewport"
import { DoneScreen, ProgressScreen, ReadyScreen, type BookView } from "@/screens/book"
import { BooksScreen } from "@/screens/books"
import { LegacyWorkspace } from "@/screens/legacy-workspace"
import { NewBookScreen, StartScreen } from "@/screens/start"
import { ErrorScreen, LoadingScreen } from "@/screens/status"
import { useBooks } from "@/useBooks"

function App() {
  const books = useBooks()
  const mobile = useIsMobile()
  const [area, setArea] = useState<Area>("book")
  const [view, setView] = useState<BookView | null>(null)
  const book = books.detail
  const busy = Boolean(books.busy)
  const screen = bookScreen({
    loading: books.busy === "loading",
    error: books.error,
    hasBooks: books.projects.length > 0,
    book,
    activeProjectId: books.activeProjectId,
    manual: false,
  })
  function navigate(next: Area) {
    setArea(next)
    setView(null)
    window.scrollTo(0, 0)
  }
  function go(next: BookView) {
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
  const otherBook = books.projects.find(project => project.id === books.activeProjectId)

  function content() {
    if (screen === "carregando") return <LoadingScreen book={books.projects.length > 0} />
    if (screen === "erro") return <ErrorScreen onRetry={() => void books.retryLoading()} busy={busy} mobile={mobile} />
    if (view === "novo-livro" || (screen === "inicio" && area === "books"))
      return <NewBookScreen busy={books.busy === "import"} canCancel={books.projects.length > 0} onCancel={() => navigate("books")} onImport={importBook} />
    if (screen === "inicio") return <StartScreen onChoose={() => go("novo-livro")} />
    if (area === "books") return <BooksScreen projects={books.projects} activeProjectId={books.activeProjectId} onOpen={openBook} onNew={() => go("novo-livro")} />
    if (area === "options" || view || !book) return <LegacyWorkspace books={books} />
    if (screen === "pronto-para-comecar") return <ReadyScreen book={book} busy={busy} go={go} onStart={() => void books.action("start", { task: "automatic" })} />
    if (screen === "outro-livro") return <ReadyScreen book={book} busy={busy} go={go} onStart={() => undefined} otherBook={otherBook && { name: otherBook.name, onFollow: () => openBook(otherBook.id) }} />
    if (screen === "acompanhar") return <ProgressScreen book={book} busy={busy} go={go} onPause={() => void books.action("stop")} />
    if (screen === "livro-pronto") return <DoneScreen book={book} busy={busy} go={go} onDownload={language => void books.download(language)} />
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
