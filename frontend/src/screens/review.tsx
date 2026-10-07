import { useState } from "react"
import type * as React from "react"
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Check } from "@/components/ui/choice"
import { CorrectedParagraph } from "@/components/ui/correction"
import { Field, Textarea } from "@/components/ui/field"
import { TextLink } from "@/components/ui/link"
import { ListItem } from "@/components/ui/list-item"
import { Notice } from "@/components/ui/notice"
import { SegmentedControl } from "@/components/ui/segmented-control"
import type { BookChunk, BookDetail } from "@/book-types"
import { chunkChanges, segments, type Segment } from "@/lib/marks"
import { cn } from "@/lib/utils"
import { useIsMobile } from "@/lib/viewport"
import { CardTitle, PageTitle } from "@/screens/parts"

export type Pane = "changes" | "original" | "spanish"

function count(n: number, one: string, many: string) {
  return n === 1 ? `1 ${one}` : `${n} ${many}`
}

function Marked({ parts, original = false }: { parts: Segment[]; original?: boolean }) {
  return <>{parts.map((part, index) => part.marked ? <mark key={index} className={cn("rv-mark", original && "rv-mark--original")}>{part.text}</mark> : <span key={index}>{part.text}</span>)}</>
}

type ChunkNavProps = { book: BookDetail; onChunk: (chunkId: string) => void; onList?: () => void }

export function ChunkNav({ book, onChunk, onList }: ChunkNavProps) {
  const mobile = useIsMobile()
  const index = book.chunks.findIndex(chunk => chunk.id === book.current?.id)
  const previous = book.chunks[index - 1]
  const next = book.chunks[index + 1]
  return (
    <nav aria-label="Navegar entre trechos" className="rv-actions">
      {previous && <Button onClick={() => onChunk(previous.id)}><ChevronLeftIcon size={20} aria-hidden="true" />{mobile ? "Anterior" : "Trecho anterior"}</Button>}
      {next && <Button onClick={() => onChunk(next.id)}>{mobile ? "Próximo" : "Próximo trecho"}<ChevronRightIcon size={20} aria-hidden="true" /></Button>}
      {onList && <TextLink onClick={onList}>Escolher outro trecho</TextLink>}
    </nav>
  )
}

type HeaderProps = ChunkNavProps & { onBack: () => void; status?: string }

/** Back link, chunk position and title, and the previous/next navigation. */
export function ChunkHeader({ book, onBack, onChunk, onList, status }: HeaderProps) {
  const mobile = useIsMobile()
  const index = book.chunks.findIndex(item => item.id === book.current?.id)
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div>
      <div className="rv-toolbar">
        <PageTitle eyebrow={`Trecho ${index + 1} de ${book.chunks.length}${status ? ` · ${status}` : ""}`}>{book.current?.title}</PageTitle>
        {!mobile && <ChunkNav book={book} onChunk={onChunk} onList={onList} />}
      </div>
      {mobile && <ChunkNav book={book} onChunk={onChunk} onList={onList} />}
    </>
  )
}

/** Segmented control for the views, with the line that goes beside it. */
export function PaneBar({ pane, onPane, spanish, aside }: { pane: Pane; onPane: (pane: Pane) => void; spanish: boolean; aside?: React.ReactNode }) {
  const mobile = useIsMobile()
  const options = [
    { value: "changes" as const, label: mobile ? "Mudanças" : "O que mudou" },
    { value: "original" as const, label: mobile ? "Original" : "Texto original" },
    ...(spanish ? [{ value: "spanish" as const, label: mobile ? "Espanhol" : "Em espanhol" }] : []),
  ]
  return <div className="rv-toolbar"><SegmentedControl<Pane> label="O que mostrar" variant={mobile ? "block" : "default"} value={pane} onChange={onPane} options={options} />{aside}</div>
}

export function ChangesCount({ total, onlyChanged, setOnlyChanged }: { total: number; onlyChanged: boolean; setOnlyChanged: (value: boolean) => void }) {
  const mobile = useIsMobile()
  return (
    <div className="rv-stack rv-stack--xs">
      <strong role="status">{total ? `${count(total, "correção", "correções")} neste trecho` : "Nenhuma correção neste trecho"}</strong>
      {total > 0 && <Check checked={onlyChanged} onChange={event => setOnlyChanged(event.target.checked)}>{mobile ? "Só parágrafos com correção" : "Mostrar só os parágrafos com correção"}</Check>}
    </div>
  )
}

/** The revised paragraphs with each correction beside (or under) its paragraph. */
export function ChangesBody({ chunk, onlyChanged }: { chunk: BookChunk; onlyChanged: boolean }) {
  const { revisedText, listOf } = chunkChanges(chunk)
  return (
    <div>
      {chunk.paragraphs.map(paragraph => ({ paragraph, list: listOf(paragraph) })).filter(({ list }) => !onlyChanged || list.length).map(({ paragraph, list }) => (
        <CorrectedParagraph key={paragraph.id} text={<Marked parts={segments(revisedText(paragraph.id), list.map(item => item.revised))} />} items={list} />
      ))}
    </div>
  )
}

/** The text as written, with the corrected words underlined when there is a review. */
export function OriginalBody({ chunk }: { chunk: BookChunk }) {
  const mobile = useIsMobile()
  const { listOf, total } = chunkChanges(chunk)
  return (
    <>
      <section aria-label="Texto original" className={cn("rv-book-paragraphs", mobile ? "book-text-mobile" : "book-text")}>
        {chunk.paragraphs.map(paragraph => <p key={paragraph.id}><Marked original parts={segments(paragraph.text, listOf(paragraph).map(item => item.original))} /></p>)}
      </section>
      {total > 0 && <p className="rv-muted">As palavras sublinhadas foram corrigidas. O motivo de cada uma está em “O que mudou”.</p>}
    </>
  )
}

type ReviewProps = {
  book: BookDetail
  pane: Pane
  onPane: (pane: Pane) => void
  onBack: () => void
  onChunk: (chunkId: string) => void
  onList: () => void
  onAdjust: () => void
}

/** conferir, conferir-original, conferir-espanhol and conferir-sem-traducao. */
export function ReviewScreen({ book, pane, onPane, onBack, onChunk, onList, onAdjust }: ReviewProps) {
  const mobile = useIsMobile()
  const [onlyChanged, setOnlyChanged] = useState(false)
  const chunk = book.current
  if (!chunk) return <><div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div><p className="rv-muted">Escolha o que revisar para ver os trechos do livro.</p></>
  const reviewed = Boolean(chunk.revised)
  const { revisedText, total } = chunkChanges(chunk)
  return (
    <>
      <ChunkHeader book={book} onBack={onBack} onChunk={onChunk} onList={onList} />
      <PaneBar pane={pane} onPane={onPane} spanish aside={<>
        {pane === "changes" && reviewed && <ChangesCount total={total} onlyChanged={onlyChanged} setOnlyChanged={setOnlyChanged} />}
        {pane === "original" && <p className="rv-muted">Como você escreveu, antes da revisão</p>}
        {pane === "spanish" && chunk.translations && <div className="rv-stack rv-stack--xs">
          <strong>{chunk.spanish_checked ? "Espanhol já revisado neste trecho" : "Espanhol traduzido, ainda sem a revisão final"}</strong>
          <div><TextLink onClick={onAdjust}>Ajustar o espanhol</TextLink></div>
        </div>}
      </>} />

      {pane === "changes" && (reviewed ? <ChangesBody chunk={chunk} onlyChanged={onlyChanged} /> : <Notice plain>
        <strong>Este trecho ainda não foi revisado.</strong> As correções aparecem aqui quando o Revisor passar por ele.
      </Notice>)}

      {pane === "original" && <OriginalBody chunk={chunk} />}

      {pane === "spanish" && (chunk.translations ? <div className={cn("rv-bilingual", mobile && "rv-bilingual--stack")}>
        {!mobile && <div className="rv-bilingual__row"><span className="ui-label rv-muted">Português revisado</span><span className="ui-label rv-muted">Espanhol da América Latina</span></div>}
        {chunk.paragraphs.map(paragraph => (
          <div key={paragraph.id} className="rv-bilingual__row">
            <p className={mobile ? "book-text-mobile rv-muted" : "book-text"}>{revisedText(paragraph.id) || paragraph.text}</p>
            <p lang="es-419" className={mobile ? "book-text-mobile" : "book-text"}>{chunk.translations?.[String(paragraph.id)]}</p>
          </div>
        ))}
      </div> : <Card variant="outline" aria-labelledby="sem-traducao-titulo">
        <CardTitle id="sem-traducao-titulo">Este trecho ainda não foi traduzido</CardTitle>
        <p className="rv-muted">A tradução começa quando todo o português estiver revisado. Enquanto isso, você pode ver o que mudou no português.</p>
        <div><Button onClick={() => onPane("changes")}>Ver o que mudou</Button></div>
      </Card>)}

      <ChunkNav book={book} onChunk={onChunk} />
    </>
  )
}

/** ajustar-espanhol: one field per paragraph, Portuguese beside it for reference. */
export function AdjustSpanishScreen({ book, busy, onBack, save }: { book: BookDetail; busy: boolean; onBack: () => void; save: (operation: string, data?: unknown) => Promise<unknown> }) {
  const mobile = useIsMobile()
  const chunk = book.current as BookChunk
  const [values, setValues] = useState<Record<string, string>>(chunk.translations ?? {})
  const [checked, setChecked] = useState(false)
  const index = book.chunks.findIndex(item => item.id === chunk.id)
  const empty = Object.entries(values).filter(([, text]) => !text.trim()).map(([id]) => id)
  async function submit() {
    setChecked(true)
    if (empty.length) return
    if (await save("save-translation", { chunk_id: chunk.id, translations: values, revision: book.revision })) onBack()
  }
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar sem salvar</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle eyebrow={`Trecho ${index + 1} de ${book.chunks.length} · ${chunk.title}`}>Ajustar o espanhol</PageTitle>
        <p className="rv-muted">Mude o que quiser no texto em espanhol. O português ao lado é só para consulta.</p>
      </div>
      <div className={cn("rv-bilingual", mobile && "rv-bilingual--stack")}>
        {chunk.paragraphs.map((paragraph, position) => {
          const id = String(paragraph.id)
          const field = `ajuste-${id}`
          return (
            <div key={id} className="rv-bilingual__row">
              <p className={cn(mobile ? "book-text-mobile" : "book-text", "rv-muted")}>{chunk.revised?.[id] ?? paragraph.text}</p>
              <Field id={field} label={`Parágrafo ${position + 1} em espanhol`} error={checked && empty.includes(id) ? "Escreva o parágrafo em espanhol." : undefined}>
                <Textarea id={field} book lang="es-419" rows={Math.max(3, Math.ceil((values[id]?.length ?? 0) / 60))} value={values[id] ?? ""} onChange={event => setValues({ ...values, [id]: event.target.value })} disabled={busy} aria-invalid={(checked && empty.includes(id)) || undefined} />
              </Field>
            </div>
          )
        })}
      </div>
      <p className="rv-help">Depois de salvar, o Revisor confere este trecho de novo antes de gerar o Word.</p>
      <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
        <Button variant="primary" size="lg" block={mobile} onClick={() => void submit()} disabled={busy}>Salvar ajustes</Button>
        <Button block={mobile} onClick={onBack} disabled={busy}>Cancelar</Button>
      </div>
    </>
  )
}

const PAGE = 12

/** trechos: paginated list of chunks with a notes filter. */
export function ChunksScreen({ book, onBack, onOpen }: { book: BookDetail; onBack: () => void; onOpen: (chunkId: string) => void }) {
  const mobile = useIsMobile()
  const notes = book.editorial_notes ?? []
  const noted = new Set(notes.map(note => note.chunk_id))
  const [filter, setFilter] = useState<"all" | "notes">("all")
  const [shown, setShown] = useState(PAGE)
  const list = book.chunks.map((chunk, index) => ({ chunk, index })).filter(({ chunk }) => filter === "all" || noted.has(chunk.id))
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar ao texto</TextLink></div>
      <div className="rv-toolbar">
        <PageTitle>Escolher um trecho</PageTitle>
        {noted.size > 0 && <SegmentedControl<"all" | "notes"> label="Quais trechos mostrar" variant={mobile ? "block" : "default"} value={filter} onChange={value => { setFilter(value); setShown(PAGE) }}
          options={[{ value: "all", label: `Todos os ${book.chunks.length}` }, { value: "notes", label: `Com observações (${noted.size})` }]} />}
      </div>
      <ol className="rv-items">
        {list.slice(0, shown).map(({ chunk, index }) => {
          const current = chunk.id === book.current?.id
          const own = notes.filter(note => note.chunk_id === chunk.id && !note.read).length
          const meta = chunk.status === "pending" && !chunk.corrections ? "Ainda não revisado" : chunk.corrections ? count(chunk.corrections, "correção", "correções") : "Sem correções"
          return (
            <li key={chunk.id}>
              <ListItem index={index + 1} title={chunk.title} meta={meta} current={current} onClick={() => onOpen(chunk.id)}
                note={current ? "Aberto agora" : own ? count(own, "observação para ler", "observações para ler") : undefined} />
            </li>
          )
        })}
      </ol>
      {list.length > shown && <div className="rv-actions">
        <Button onClick={() => setShown(shown + PAGE)}>Mostrar mais trechos</Button>
        <span className="rv-muted rv-num">Mostrando {shown} de {list.length}</span>
      </div>}
    </>
  )
}
