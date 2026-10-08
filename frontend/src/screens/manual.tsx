import { useState } from "react"
import { CheckIcon, ChevronRightIcon, DownloadIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ConfirmDialog } from "@/components/ui/dialog"
import { Field, Textarea } from "@/components/ui/field"
import { TextLink } from "@/components/ui/link"
import { Notice } from "@/components/ui/notice"
import { Steps } from "@/components/ui/steps"
import type { BookDetail } from "@/book-types"
import { chunkChanges } from "@/lib/marks"
import { cn } from "@/lib/utils"
import { useIsMobile } from "@/lib/viewport"
import { CardTitle, Columns, PageTitle } from "@/screens/parts"
import { ChangesBody, ChangesCount, ChunkHeader, ChunkNav, OriginalBody, PaneBar, type Pane } from "@/screens/review"

type Act = (operation: string, data?: unknown) => Promise<unknown>

function plural(n: number, one: string, many: string) {
  return n === 1 ? `1 ${one}` : `${n} ${many}`
}

function tally(book: BookDetail) {
  const total = book.chunks.length
  const approved = book.chunks.filter(chunk => chunk.status === "approved").length
  const waiting = book.chunks.filter(chunk => chunk.status === "ready").length
  const proposed = approved + waiting
  const missing = book.chunks.filter(chunk => chunk.status === "pending" || chunk.status === "rejected").length
  const translated = book.chunks.filter(chunk => chunk.translated).length
  return { total, approved, waiting, proposed, missing, translated }
}

type HomeProps = {
  book: BookDetail
  busy: boolean
  act: Act
  onAutomatic: () => void
  onNext: (chunkId: string) => void
  onList: () => void
  onDownload: (language: "pt-BR" | "es") => void
}

/** aprovar-a-mao: review, approve and translate, step by step. */
export function ManualScreen({ book, busy, act, onAutomatic, onNext, onList, onDownload }: HomeProps) {
  const [confirm, setConfirm] = useState(false)
  const mobile = useIsMobile()
  const { total, approved, waiting, proposed, missing, translated } = tally(book)
  const allApproved = approved === total && total > 0
  const allTranslated = allApproved && translated === total
  const next = book.chunks.find(chunk => chunk.status === "ready")
  return (
    <>
      <div className="rv-stack rv-stack--xs">
        <PageTitle eyebrow="Livro aberto">{book.name}</PageTitle>
        <p className="rv-actions"><span className="rv-muted">Aprovação à mão ligada ·</span><TextLink onClick={onAutomatic}>Voltar para o automático</TextLink></p>
      </div>
      <Columns
        main={<Card aria-labelledby="mao-titulo">
          <div className="rv-stack rv-stack--xs">
            <CardTitle id="mao-titulo" main>Você decide cada correção</CardTitle>
            <p className="rv-muted">O Revisor propõe, você aprova. A tradução só começa quando {total === 1 ? "o trecho estiver aprovado" : `os ${total} trechos estiverem aprovados`}.</p>
          </div>
          <Steps steps={[
            { title: "Revisar o português", percent: book.progress.draft_percent, state: missing === 0 ? "done" : "current", hideStatus: missing > 0,
              detail: `${proposed} de ${total} trechos já têm correções propostas.`,
              action: missing > 0 ? <div><Button onClick={() => act("start", { task: "review" })} disabled={busy}>{missing === 1 ? "Revisar o que falta" : `Revisar os ${missing} que faltam`}</Button></div> : undefined },
            { title: "Aprovar as correções", percent: book.progress.review_percent, state: allApproved ? "done" : proposed > 0 ? "current" : "waiting", hideStatus: !allApproved,
              detail: `${plural(waiting, "trecho esperando você", "trechos esperando você")} · ${approved} já ${approved === 1 ? "aprovado" : "aprovados"}.`,
              action: waiting > 0 ? <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
                {next && <Button variant="primary" onClick={() => onNext(next.id)}>Conferir o próximo trecho</Button>}
                <Button onClick={() => setConfirm(true)} disabled={busy}>{waiting === 1 ? "Aprovar o que falta" : `Aprovar os ${waiting} de uma vez`}</Button>
              </div> : undefined },
            { title: "Traduzir para o espanhol", percent: book.progress.translation_percent, state: allTranslated ? "done" : allApproved ? "current" : "waiting", hideStatus: !allTranslated,
              detail: allApproved ? (allTranslated ? "Tradução concluída." : `${translated} de ${total} trechos traduzidos.`) : `Fica disponível quando ${total === 1 ? "o trecho estiver aprovado" : `os ${total} trechos estiverem aprovados`}.`,
              action: allApproved && !allTranslated ? <div><Button variant="primary" onClick={() => act("start", { task: "translate" })} disabled={busy}>{translated ? "Continuar a tradução" : "Traduzir para o espanhol"}</Button></div> : undefined },
          ]} />
        </Card>}
        side={<>
          <Card variant="outline" aria-labelledby="mao-arquivos">
            <CardTitle id="mao-arquivos">Seus arquivos</CardTitle>
            {allApproved ? <div className="rv-stack rv-stack--sm">
              <Button block className="rv-btn--start" onClick={() => onDownload("pt-BR")} disabled={busy}><DownloadIcon size={20} aria-hidden="true" />Baixar o livro revisado em português</Button>
              {allTranslated ? <Button block className="rv-btn--start" onClick={() => onDownload("es")} disabled={busy}><DownloadIcon size={20} aria-hidden="true" />Baixar o livro em espanhol</Button>
                : <p className="rv-muted">O livro em espanhol aparece aqui quando a tradução terminar.</p>}
            </div> : <>
              <ul className="rv-summary">
                <li className="rv-summary__row"><span>Livro revisado em português</span><span className="rv-muted">Ainda não está pronto</span></li>
                <li className="rv-summary__row"><span>Livro em espanhol</span><span className="rv-muted">Ainda não está pronto</span></li>
              </ul>
              <p className="rv-muted">Os dois arquivos Word aparecem aqui quando a tradução terminar.</p>
            </>}
          </Card>
          <Button block onClick={onList}>Ver todos os trechos</Button>
        </>}
      />
      <ConfirmDialog open={confirm} onOpenChange={setConfirm}
        title={waiting === 1 ? "Aprovar o trecho que falta?" : `Aprovar os ${waiting} trechos de uma vez?`}
        description="As correções propostas nesses trechos serão aplicadas sem você conferir uma por uma. Depois, se quiser, dá para reabrir qualquer trecho."
        confirm={<Button variant="primary" disabled={busy} onClick={() => act("approve-all", { revision: book.revision }).then(result => { if (result) setConfirm(false) })}>{waiting === 1 ? "Aprovar" : `Aprovar os ${waiting}`}</Button>}
        cancel={<Button onClick={() => setConfirm(false)}>Voltar para conferir</Button>} />
    </>
  )
}

type ChunkProps = {
  book: BookDetail
  busy: boolean
  act: Act
  onBack: () => void
  onChunk: (chunkId: string) => void
  onList: () => void
  onAdjust: () => void
  onRefuse: () => void
}

/** aprovar-a-mao-conferir, -aprovado, -recusado and -nao-revisado, by the chunk's state. */
export function ManualChunkScreen({ book, busy, act, onBack, onChunk, onList, onAdjust, onRefuse }: ChunkProps) {
  const mobile = useIsMobile()
  const [pane, setPane] = useState<Pane>("changes")
  const [onlyChanged, setOnlyChanged] = useState(false)
  const chunk = book.current
  if (!chunk) return <><div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div><p className="rv-muted">Escolha o que revisar para ver os trechos do livro.</p></>
  const { total } = chunkChanges(chunk)
  const status = { ready: "esperando sua aprovação", approved: "aprovado por você", rejected: undefined, pending: undefined }[chunk.status]
  const nextWaiting = book.chunks.find(item => item.status === "ready" && item.id !== chunk.id)
  const review = () => act("start", { task: "review", chunk_id: chunk.id })
  if (chunk.status === "pending" || chunk.status === "rejected") return (
    <>
      <ChunkHeader book={book} onBack={onBack} onChunk={onChunk} onList={onList} />
      <div className="rv-notice rv-notice--plain" role="status">
        <div className="rv-notice__text rv-stack rv-stack--xs">
          {chunk.status === "rejected" ? <>
            <strong>Você recusou a revisão deste trecho</strong>
            {chunk.feedback && <><p className="rv-muted">Seu pedido:</p><blockquote className="book-quote">“{chunk.feedback}”</blockquote></>}
          </> : <><strong>Este trecho ainda não foi revisado</strong><p className="rv-muted">O texto abaixo está como você escreveu.</p></>}
        </div>
        <div className="rv-stack rv-stack--xs">
          <Button variant="primary" block={mobile} onClick={review} disabled={busy}>{chunk.status === "rejected" ? "Pedir nova revisão deste trecho" : "Revisar este trecho agora"}</Button>
          {chunk.status === "rejected" && <p className="rv-small rv-muted">O Revisor refaz as correções levando em conta o seu pedido.</p>}
        </div>
      </div>
      <section aria-label="Texto do trecho" className={cn("rv-book-paragraphs", mobile ? "book-text-mobile" : "book-text")}>
        {chunk.paragraphs.map(paragraph => <p key={paragraph.id}>{paragraph.text}</p>)}
      </section>
      <ChunkNav book={book} onChunk={onChunk} />
    </>
  )
  return (
    <>
      <ChunkHeader book={book} onBack={onBack} onChunk={onChunk} onList={onList} status={status} />
      <PaneBar pane={pane} onPane={setPane} spanish={false} aside={pane === "changes" ? <ChangesCount total={total} onlyChanged={onlyChanged} setOnlyChanged={setOnlyChanged} /> : <p className="rv-muted">Como você escreveu, antes da revisão</p>} />
      {pane === "changes" ? <ChangesBody chunk={chunk} onlyChanged={onlyChanged} /> : <OriginalBody chunk={chunk} />}
      {chunk.status === "ready" ? <section aria-labelledby="decisao-titulo" className="rv-notice rv-notice--plain">
        <strong id="decisao-titulo" className="rv-notice__text">O que você quer fazer com este trecho?</strong>
        <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
          <Button variant="primary" block={mobile} onClick={() => act("approve", { chunk_id: chunk.id, proposal_id: chunk.proposal_id })} disabled={busy}><CheckIcon size={20} aria-hidden="true" />Aprovar este trecho</Button>
          <Button block={mobile} onClick={onAdjust} disabled={busy}>Ajustar o texto</Button>
          <Button block={mobile} onClick={onRefuse} disabled={busy}>Recusar e pedir outra revisão</Button>
        </div>
      </section> : <>
        <div><TextLink onClick={onAdjust} disabled={busy}>Ajustar o português</TextLink></div>
        <p className="rv-actions"><span className="rv-muted">Mudou de ideia?</span><TextLink variant="quiet" onClick={() => act("reopen", { chunk_id: chunk.id })} disabled={busy}>Reabrir a revisão deste trecho</TextLink></p>
        {nextWaiting && <div><Button variant="primary" block={mobile} onClick={() => onChunk(nextWaiting.id)}>Próximo trecho esperando você<ChevronRightIcon size={20} aria-hidden="true" /></Button></div>}
      </>}
      <ChunkNav book={book} onChunk={onChunk} />
    </>
  )
}

type FormProps = { book: BookDetail; busy: boolean; act: Act; onDone: () => void }

/** aprovar-a-mao-ajustar: edit the revised text, then approve it. */
export function ManualAdjustScreen({ book, busy, act, onDone }: FormProps) {
  const mobile = useIsMobile()
  const chunk = book.current!
  const [values, setValues] = useState<Record<string, string>>(chunk.revised ?? {})
  const index = book.chunks.findIndex(item => item.id === chunk.id)
  async function submit() {
    if (await act("approve", { chunk_id: chunk.id, proposal_id: chunk.proposal_id, revised: values })) onDone()
  }
  return (
    <>
      <div><TextLink variant="back" onClick={onDone}>Voltar sem salvar</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle eyebrow={`Trecho ${index + 1} de ${book.chunks.length} · ${chunk.title}`}>Ajustar o texto</PageTitle>
        <p className="rv-muted">Mude o que quiser no texto revisado. Seu original continua guardado.</p>
      </div>
      <section aria-label="Texto revisado do trecho" className="rv-stack">
        {chunk.paragraphs.map((paragraph, position) => {
          const id = String(paragraph.id)
          return (
            <Field key={id} id={`ajuste-pt-${id}`} label={`Parágrafo ${position + 1}`}>
              <Textarea id={`ajuste-pt-${id}`} book rows={Math.max(3, Math.ceil((values[id]?.length ?? 0) / 70))} value={values[id] ?? ""} onChange={event => setValues({ ...values, [id]: event.target.value })} disabled={busy} />
            </Field>
          )
        })}
      </section>
      <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
        <Button variant="primary" size="lg" block={mobile} onClick={() => submit()} disabled={busy}>Aprovar com meus ajustes</Button>
        <Button block={mobile} onClick={onDone} disabled={busy}>Cancelar</Button>
      </div>
    </>
  )
}

/** aprovar-a-mao-recusar: say what must change and ask for another review. */
export function ManualRefuseScreen({ book, busy, act, onDone }: FormProps) {
  const mobile = useIsMobile()
  const chunk = book.current!
  const [reason, setReason] = useState("")
  const [error, setError] = useState("")
  const index = book.chunks.findIndex(item => item.id === chunk.id)
  async function submit() {
    if (!reason.trim()) { setError("Escreva o que precisa mudar."); return }
    if (await act("reject", { chunk_id: chunk.id, proposal_id: chunk.proposal_id, reason: reason.trim() })) onDone()
  }
  return (
    <>
      <div><TextLink variant="back" onClick={onDone}>Voltar ao trecho</TextLink></div>
      <PageTitle eyebrow={`Trecho ${index + 1} de ${book.chunks.length} · ${chunk.title}`}>Recusar esta revisão</PageTitle>
      <Card aria-label="Pedir outra revisão">
        <Field id="motivo-recusa" label="O que precisa mudar?" help="O Revisor refaz as correções deste trecho seguindo o que você escrever." error={error || undefined}>
          <Textarea id="motivo-recusa" value={reason} placeholder="Ex.: mantenha a expressão “fazia em criança” como está." onChange={event => { setReason(event.target.value); setError("") }} disabled={busy} aria-invalid={Boolean(error) || undefined} />
        </Field>
        <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
          <Button variant="primary" block={mobile} onClick={() => submit()} disabled={busy}>Registrar e pedir outra revisão</Button>
          <Button block={mobile} onClick={onDone} disabled={busy}>Cancelar</Button>
        </div>
      </Card>
    </>
  )
}

type AuthorProps = { book: BookDetail; busy: boolean; act: Act; onBack: () => void }

/** revisar-manual: a chunk the automatic review could not finish; the author decides it by hand. */
export function AuthorReviewScreen({ book, busy, act, onBack, onAdjust, onApproved }: AuthorProps & { onAdjust: () => void; onApproved: () => void }) {
  const mobile = useIsMobile()
  const [pane, setPane] = useState<Pane>("changes")
  const [onlyChanged, setOnlyChanged] = useState(false)
  const chunk = book.current
  if (!chunk) return null
  const proposal = chunk.status === "ready" && chunk.revised ? chunk.revised : null
  const original = Object.fromEntries(chunk.paragraphs.map(p => [String(p.id), p.text]))
  const { total } = chunkChanges(chunk)
  const approve = (revised: Record<string, string>) => act("author-approve", { chunk_id: chunk.id, revised, revision: book.revision }).then(result => { if (result) onApproved() })
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div>
      <PageTitle eyebrow={`Trecho ${book.chunks.findIndex(item => item.id === chunk.id) + 1} de ${book.chunks.length} · revisão manual`}>{chunk.title}</PageTitle>
      <Notice plain><strong>Este trecho fica com você.</strong> O Revisor não vai revisar nem traduzir este trecho. Confira o texto, decida e, depois, escreva o espanhol.</Notice>
      {proposal ? <>
        <PaneBar pane={pane} onPane={setPane} spanish={false} aside={pane === "changes" ? <ChangesCount total={total} onlyChanged={onlyChanged} setOnlyChanged={setOnlyChanged} /> : <p className="rv-muted">Como você escreveu, antes da revisão</p>} />
        {pane === "changes" ? <ChangesBody chunk={chunk} onlyChanged={onlyChanged} /> : <OriginalBody chunk={chunk} />}
      </> : <section aria-label="Texto do trecho" className={cn("rv-book-paragraphs", mobile ? "book-text-mobile" : "book-text")}>
        {chunk.paragraphs.map(paragraph => <p key={paragraph.id}>{paragraph.text}</p>)}
      </section>}
      <section aria-labelledby="manual-decisao" className="rv-notice rv-notice--plain">
        <strong id="manual-decisao" className="rv-notice__text">{proposal ? "O que você quer fazer com as correções propostas?" : "O Revisor não chegou a propor correções. O que você quer fazer?"}</strong>
        <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
          {proposal && <Button variant="primary" block={mobile} onClick={() => approve(proposal)} disabled={busy}><CheckIcon size={20} aria-hidden="true" />Aprovar as correções</Button>}
          <Button variant={proposal ? "secondary" : "primary"} block={mobile} onClick={() => approve(original)} disabled={busy}>{proposal ? "Manter o original" : "Aprovar o texto como está"}</Button>
          <Button block={mobile} onClick={onAdjust} disabled={busy}>Ajustar o texto</Button>
        </div>
      </section>
    </>
  )
}

/** ajustar-manual: the author writes the final Portuguese of that chunk. */
export function AuthorEditScreen({ book, busy, act, onBack, onApproved }: AuthorProps & { onApproved: () => void }) {
  const mobile = useIsMobile()
  const chunk = book.current!
  const start = chunk.status === "ready" && chunk.revised ? chunk.revised : Object.fromEntries(chunk.paragraphs.map(p => [String(p.id), p.text]))
  const [values, setValues] = useState<Record<string, string>>(start)
  const [checked, setChecked] = useState(false)
  const index = book.chunks.findIndex(item => item.id === chunk.id)
  const empty = Object.entries(values).filter(([, text]) => !text.trim()).map(([id]) => id)
  async function submit() {
    setChecked(true)
    if (empty.length) return
    if (await act("author-approve", { chunk_id: chunk.id, revised: values, revision: book.revision })) onApproved()
  }
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar sem salvar</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle eyebrow={`Trecho ${index + 1} de ${book.chunks.length} · ${chunk.title}`}>Ajustar o texto</PageTitle>
        <p className="rv-muted">Escreva o português final deste trecho. Seu original continua guardado.</p>
      </div>
      <section aria-label="Texto do trecho" className="rv-stack">
        {chunk.paragraphs.map((paragraph, position) => {
          const id = String(paragraph.id)
          return (
            <Field key={id} id={`manual-pt-${id}`} label={`Parágrafo ${position + 1}`} error={checked && empty.includes(id) ? "Este parágrafo não pode ficar vazio." : undefined}>
              <Textarea id={`manual-pt-${id}`} book rows={Math.max(3, Math.ceil((values[id]?.length ?? 0) / 70))} value={values[id] ?? ""} onChange={event => setValues({ ...values, [id]: event.target.value })} disabled={busy} aria-invalid={(checked && empty.includes(id)) || undefined} />
            </Field>
          )
        })}
      </section>
      <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
        <Button variant="primary" size="lg" block={mobile} onClick={() => submit()} disabled={busy}>Aprovar este texto</Button>
        <Button block={mobile} onClick={onBack} disabled={busy}>Cancelar</Button>
      </div>
    </>
  )
}

/** escrever-espanhol: the author's Spanish for a chunk that stays with them. */
export function AuthorSpanishScreen({ book, busy, act, onBack, onSaved }: AuthorProps & { onSaved: () => void }) {
  const mobile = useIsMobile()
  const chunk = book.current!
  // After the model translated what it accepted, the author writes only the paragraphs it declined.
  const fromModel = !chunk.translations && chunk.model_translations ? chunk.model_translations : null
  const wanted = fromModel ? chunk.author_paragraphs ?? [] : Object.keys(chunk.revised ?? {})
  const [values, setValues] = useState<Record<string, string>>(fromModel ? Object.fromEntries(wanted.map(id => [id, ""])) : chunk.translations ?? Object.fromEntries(wanted.map(id => [id, ""])))
  const [checked, setChecked] = useState(false)
  const index = book.chunks.findIndex(item => item.id === chunk.id)
  const empty = Object.entries(values).filter(([, text]) => !text.trim()).map(([id]) => id)
  async function submit() {
    setChecked(true)
    if (empty.length) return
    if (await act("author-translate", { chunk_id: chunk.id, translations: values, revision: book.revision })) onSaved()
  }
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar sem salvar</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle eyebrow={`Trecho ${index + 1} de ${book.chunks.length} · ${chunk.title}`}>Escrever o espanhol</PageTitle>
        <p className="rv-muted">{fromModel
          ? `O modelo traduziu o resto do trecho. Escreva só ${wanted.length === 1 ? "o parágrafo que ele recusou" : `os ${wanted.length} parágrafos que ele recusou`}; o que você escrever entra no Word em espanhol como está.`
          : "Este trecho fica com você: o que você escrever entra no Word em espanhol como está. O português ao lado é só para consulta."}</p>
        {!fromModel && !chunk.translations && <p className="rv-muted">Se preferir, volte e continue o processamento: o modelo traduz os parágrafos que aceitar e deixa aqui só os que recusar.</p>}
      </div>
      <div className={cn("rv-bilingual", mobile && "rv-bilingual--stack")}>
        {chunk.paragraphs.map((paragraph, position) => {
          const id = String(paragraph.id)
          const field = `manual-es-${id}`
          return (
            <div key={id} className="rv-bilingual__row">
              <p className={cn(mobile ? "book-text-mobile" : "book-text", "rv-muted")}>{chunk.revised?.[id] ?? paragraph.text}</p>
              {fromModel && !wanted.includes(id) ? <p lang="es-419" className={mobile ? "book-text-mobile" : "book-text"}>{fromModel[id]}</p> : <Field id={field} label={`Parágrafo ${position + 1} em espanhol`} error={checked && empty.includes(id) ? "Escreva o parágrafo em espanhol." : undefined}>
                <Textarea id={field} book lang="es-419" rows={Math.max(3, Math.ceil(((chunk.revised?.[id] ?? paragraph.text).length) / 60))} value={values[id] ?? ""} onChange={event => setValues({ ...values, [id]: event.target.value })} disabled={busy} aria-invalid={(checked && empty.includes(id)) || undefined} />
              </Field>}
            </div>
          )
        })}
      </div>
      <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
        <Button variant="primary" size="lg" block={mobile} onClick={() => submit()} disabled={busy}>Salvar o espanhol</Button>
        <Button block={mobile} onClick={onBack} disabled={busy}>Cancelar</Button>
      </div>
    </>
  )
}
