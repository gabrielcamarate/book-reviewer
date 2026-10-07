import { PlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ProgressBar } from "@/components/ui/progress"
import type { BookSummary } from "@/book-types"
import { cn } from "@/lib/utils"
import { stageOf, stageTitle } from "@/lib/screens"
import { useIsMobile } from "@/lib/viewport"
import { PageTitle } from "@/screens/parts"

function describe(book: BookSummary, active: boolean) {
  const stage = stageOf(book.progress)
  if (stage === 4) return { label: "Pronto", line: "Revisado e traduzido · dois arquivos Word para baixar" }
  if (active) return { label: "Em andamento", line: `${stageTitle(book.progress)} · etapa ${stage + 1} de 4` }
  const started = book.progress.draft_percent > 0
  return started ? { label: "Pausado", line: `Parou em: ${stageTitle(book.progress).toLowerCase()} · etapa ${stage + 1} de 4` }
    : { label: "Pronto para começar", line: "Ainda não foi revisado" }
}

/** livros: every imported book, the one in progress highlighted. */
export function BooksScreen({ projects, activeProjectId, onOpen, onNew }: { projects: BookSummary[]; activeProjectId: string | null; onOpen: (id: string) => void; onNew: () => void }) {
  const mobile = useIsMobile()
  const newBook = <Button variant="primary" block={mobile} onClick={onNew}><PlusIcon size={20} aria-hidden="true" />Novo livro</Button>
  return (
    <>
      <PageTitle action={mobile ? undefined : newBook}>Meus livros</PageTitle>
      <ul className="rv-cards">
        {projects.map(book => {
          const active = book.id === activeProjectId
          const { label, line } = describe(book, active)
          const stage = stageOf(book.progress)
          const percent = stage < 4 ? book.progress[(["draft_percent", "review_percent", "translation_percent", "checked_percent"] as const)[stage]] : 100
          return (
            <li key={book.id}>
              <button type="button" className={cn("rv-card rv-card--button", active ? "rv-card--current" : "rv-card--outline", mobile && "rv-card--mobile")} onClick={() => onOpen(book.id)}>
                <span className={cn("ui-label", active ? "rv-accent" : "rv-muted")}>{label}</span>
                <span className={mobile ? "title-section" : "title-card"}>{book.name}</span>
                <span className="rv-muted">{line}</span>
                {stage > 0 && <ProgressBar value={percent} label={`Progresso de ${book.name}`} neutral={!active} />}
                <span className="rv-link">Abrir este livro</span>
              </button>
            </li>
          )
        })}
      </ul>
      {mobile && newBook}
      <p className="rv-muted">O Revisor trabalha em um livro por vez. Os outros ficam guardados aqui, do jeito que você deixou.</p>
    </>
  )
}
