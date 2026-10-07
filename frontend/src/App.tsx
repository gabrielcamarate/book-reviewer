import { useState } from "react"

import { AppHeader, MobileHeader, type Area } from "@/components/ui/app-header"
import { TabBar } from "@/components/ui/tab-bar"
import { cn } from "@/lib/utils"
import { bookScreen } from "@/lib/screens"
import { useIsMobile } from "@/lib/viewport"
import { LegacyWorkspace } from "@/screens/legacy-workspace"
import { ErrorScreen, LoadingScreen } from "@/screens/status"
import { useBooks } from "@/useBooks"

function App() {
  const books = useBooks()
  const mobile = useIsMobile()
  const [area, setArea] = useState<Area>("book")
  const [importOpen, setImportOpen] = useState(false)
  const screen = bookScreen({
    loading: books.busy === "loading",
    error: books.error,
    hasBooks: books.projects.length > 0,
    book: books.detail,
    activeProjectId: books.activeProjectId,
    manual: false,
  })
  function navigate(next: Area) {
    setArea(next)
    setImportOpen(false)
  }
  const centered = screen === "carregando"
  return (
    <div className="rv-app">
      <a href="#conteudo" className="rv-skip">Ir para o conteúdo</a>
      {mobile ? <MobileHeader /> : <AppHeader current={area} onNavigate={navigate} />}
      <main id="conteudo" className={cn("rv-page", mobile && "rv-page--mobile", centered && "rv-page--center")}>
        {screen === "carregando" ? <LoadingScreen book={books.projects.length > 0} />
          : screen === "erro" ? <ErrorScreen onRetry={() => void books.retryLoading()} busy={Boolean(books.busy)} mobile={mobile} />
          : <LegacyWorkspace books={books} area={area} onOpenBook={() => setArea("book")} importOpen={importOpen} setImportOpen={setImportOpen} />}
      </main>
      {mobile && <TabBar current={area} onNavigate={navigate} />}
    </div>
  )
}

export default App
