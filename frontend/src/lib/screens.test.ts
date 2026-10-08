import assert from "node:assert/strict"
import { test } from "node:test"

import { bookScreen, openProblems, stageOf, stageTitle, steps } from "./screens.ts"
import type { BookDetail, ProgressState } from "../book-types"

const progress = (values: Partial<ProgressState> = {}): ProgressState => ({
  draft_paragraphs: 0, draft_percent: 0, total_paragraphs: 10, approved_paragraphs: 0, translated_paragraphs: 0,
  total_chunks: 2, ready_chunks: 0, pending_chunks: 2, review_percent: 0, translation_percent: 0, checked_paragraphs: 0, checked_percent: 0, ...values,
})

const book = (values: Partial<BookDetail> = {}): BookDetail => ({
  id: "b1", name: "Livro", filename: "livro.docx", destination_filename: null, model: "m", reasoning_effort: "low", locale: "es-419",
  settings: { scope: "whole", section_ids: [], instructions: "", glossary: {} }, sections: [], progress: progress(), current: null,
  chunks: [{ id: "c1", title: "Um", status: "pending", translated: false, corrections: 0 }, { id: "c2", title: "Dois", status: "pending", translated: false, corrections: 0 }],
  automatic_result: null, job: null, glossary: {}, consistency_warnings: [], revision: 1, ...values,
})

const job = (status: NonNullable<BookDetail["job"]>["status"]) => ({ id: "j", task: "automatic" as const, status, total: 2, processed: 1, message: "" })

test("app-level states come before any book", () => {
  assert.equal(bookScreen({ loading: true, error: "", hasBooks: false, book: null, activeProjectId: null, manual: false }), "carregando")
  assert.equal(bookScreen({ loading: false, error: "Sem servidor", hasBooks: true, book: null, activeProjectId: null, manual: false }), "erro")
  assert.equal(bookScreen({ loading: false, error: "", hasBooks: false, book: null, activeProjectId: null, manual: false }), "inicio")
  assert.equal(bookScreen({ loading: false, error: "", hasBooks: true, book: null, activeProjectId: null, manual: false }), "carregando")
})

test("book screens follow the job and the result", () => {
  const screen = (value: BookDetail, extra: { activeProjectId?: string | null; manual?: boolean } = {}) =>
    bookScreen({ loading: false, error: "", hasBooks: true, book: value, activeProjectId: extra.activeProjectId ?? null, manual: extra.manual ?? false })
  assert.equal(screen(book()), "pronto-para-comecar")
  assert.equal(screen(book(), { activeProjectId: "other" }), "outro-livro")
  assert.equal(screen(book({ job: job("running") }), { activeProjectId: "b1" }), "acompanhar")
  assert.equal(screen(book({ job: job("stopping") }), { activeProjectId: "b1" }), "acompanhar")
  assert.equal(screen(book({ job: job("paused") })), "pausado")
  assert.equal(screen(book({ job: job("failed") })), "parou-no-meio")
  assert.equal(screen(book({ job: job("interrupted") })), "parou-no-meio")
  assert.equal(screen(book({ job: job("needs_attention") })), "precisa-de-atencao")
  const ready = book({ job: job("completed"), automatic_result: { revision: 1, files: { "pt-BR": { path: "a", filename: "a", download_url: "/a" }, es: { path: "b", filename: "b", download_url: "/b" } } } })
  assert.equal(screen(ready), "livro-pronto")
  assert.equal(screen(book({ job: job("paused") }), { manual: true }), "aprovar-a-mao")
  assert.equal(screen(book({ job: job("running") }), { activeProjectId: "b1", manual: true }), "acompanhar")
})

test("a book with saved work and no running job can continue", () => {
  const started = book({ chunks: [{ id: "c1", title: "Um", status: "approved", translated: false, corrections: 2 }, { id: "c2", title: "Dois", status: "pending", translated: false, corrections: 0 }] })
  assert.equal(bookScreen({ loading: false, error: "", hasBooks: true, book: started, activeProjectId: null, manual: false }), "pausado")
  assert.equal(bookScreen({ loading: false, error: "", hasBooks: true, book: { ...started, job: job("completed") }, activeProjectId: null, manual: false }), "pausado")
})

test("the current stage is the first one below 100%", () => {
  assert.equal(stageOf(progress()), 0)
  assert.equal(stageOf(progress({ draft_percent: 100, review_percent: 40 })), 1)
  assert.equal(stageOf(progress({ draft_percent: 100, review_percent: 100, translation_percent: 71, checked_percent: 50 })), 2)
  assert.equal(stageOf(progress({ draft_percent: 100, review_percent: 100, translation_percent: 100, checked_percent: 100 })), 4)
})

test("steps mark done, current and waiting with design names", () => {
  const list = steps(progress({ draft_percent: 100, review_percent: 100, translation_percent: 71, checked_percent: 50 }), true)
  assert.deepEqual(list.map(s => s.title), ["Revisar o português", "Conferir e aplicar as correções", "Traduzir para o espanhol", "Revisar o espanhol"])
  assert.deepEqual(list.map(s => s.state), ["done", "done", "current", "waiting"])
  assert.equal(list[3].percent, 50)
  assert.deepEqual(steps(progress({ draft_percent: 30 }), false).map(s => s.state), ["waiting", "waiting", "waiting", "waiting"])
})

test("a chunk the author already finished leaves the attention list without another run", () => {
  const detail = book({
    chunks: [{ id: "c1", title: "Um", status: "approved", translated: true, corrections: 0, author_handled: true },
      { id: "c2", title: "Dois", status: "approved", translated: true, corrections: 0 }],
    job: { ...job("needs_attention"), problems: [{ chunk_id: "c1", phase: "Tradução para espanhol", message: "Escreva o espanhol." },
      { chunk_id: "c2", phase: "Revisão do espanhol", message: "Pendência." }] },
  })
  assert.deepEqual(openProblems(detail).map(problem => problem.chunk_id), ["c2"])
})

test("after the four stages a running job says it is preparing the Word files", () => {
  const done = progress({ draft_percent: 100, review_percent: 100, translation_percent: 100, checked_percent: 100 })
  assert.equal(stageTitle(done, true), "Preparando os arquivos Word")
  assert.equal(stageTitle(done), "Concluído")
  assert.equal(stageTitle(progress(), true), "Revisando o português")
})
