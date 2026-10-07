import type { BookDetail, ProgressState } from "../book-types"

// Which screen the book area shows (design/IMPLEMENTACAO.md, "Qual tela mostrar").
export type BookScreen =
  | "carregando" | "erro" | "inicio" | "outro-livro" | "pronto-para-comecar" | "acompanhar"
  | "pausado" | "parou-no-meio" | "precisa-de-atencao" | "livro-pronto" | "aprovar-a-mao"

type ScreenInput = {
  loading: boolean
  error: string
  hasBooks: boolean
  book: BookDetail | null
  activeProjectId: string | null
  manual: boolean
}

export function bookScreen({ loading, error, hasBooks, book, activeProjectId, manual }: ScreenInput): BookScreen {
  if (loading) return "carregando"
  if (error && !book) return "erro"
  if (!hasBooks) return "inicio"
  if (!book) return "carregando"
  const status = book.job?.status
  if (status === "running" || status === "stopping") return "acompanhar"
  if (book.automatic_result) return "livro-pronto"
  if (manual) return "aprovar-a-mao"
  if (status === "paused") return "pausado"
  if (status === "failed" || status === "interrupted") return "parou-no-meio"
  if (status === "needs_attention") return "precisa-de-atencao"
  const started = book.chunks.some(chunk => chunk.status !== "pending" || chunk.translated)
  if (activeProjectId && activeProjectId !== book.id) return "outro-livro"
  return started ? "pausado" : "pronto-para-comecar"
}

const STAGES = [
  { title: "Revisar o português", field: "draft_percent", running: "Revisando o português" },
  { title: "Conferir e aplicar as correções", field: "review_percent", running: "Conferindo e aplicando as correções" },
  { title: "Traduzir para o espanhol", field: "translation_percent", running: "Traduzindo para o espanhol" },
  { title: "Revisar o espanhol", field: "checked_percent", running: "Revisando o espanhol" },
] as const

/** Index of the first stage below 100%; 4 when every stage is complete. */
export function stageOf(progress: ProgressState) {
  const index = STAGES.findIndex(stage => progress[stage.field] < 100)
  return index === -1 ? STAGES.length : index
}

export function stageTitle(progress: ProgressState) {
  const index = stageOf(progress)
  return index < STAGES.length ? STAGES[index].running : "Concluído"
}

export function steps(progress: ProgressState, running: boolean) {
  const current = stageOf(progress)
  return STAGES.map((stage, index) => ({
    title: stage.title,
    percent: progress[stage.field],
    state: index < current ? "done" as const : index === current && running ? "current" as const : "waiting" as const,
  }))
}
