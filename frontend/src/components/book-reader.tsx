import { useState } from "react"
import { CheckIcon, PencilIcon, RotateCcwIcon, XIcon } from "lucide-react"
import { Button } from "./ui/button"
import { Label } from "./ui/label"
import type { BookDetail } from "@/book-types"

function Highlight({ text, ranges }: { text: string; ranges: { start: number; end: number }[] }) {
  const parts: { text: string; marked: boolean }[] = []
  let cursor = 0
  for (const range of ranges) {
    if (range.start < cursor || range.end <= range.start) continue
    parts.push({ text: text.slice(cursor, range.start), marked: false }, { text: text.slice(range.start, range.end), marked: true })
    cursor = range.end
  }
  parts.push({ text: text.slice(cursor), marked: false })
  return <>{parts.map((part, i) => part.marked ? <mark key={i}>{part.text}</mark> : <span key={i}>{part.text}</span>)}</>
}

function changeRanges(edits: NonNullable<BookDetail["current"]>["edits"], id: string | number, revised = false) {
  let offset = 0
  return (edits ?? []).filter(e => String(e.paragraph_id) === String(id) && e.start !== undefined)
    .sort((a, b) => a.start! - b.start!).map(e => {
      const start = e.start! + (revised ? offset : 0)
      const end = start + (revised ? e.replacement.length : e.original.length)
      offset += e.replacement.length - e.original.length
      return { start, end }
    })
}

export function BookReader({ book, disabled, action }: { book: BookDetail; disabled: boolean; action: (operation: string, data?: unknown) => Promise<unknown> }) {
  const chunk = book.current
  const [pane, setPane] = useState("revised")
  const [edit, setEdit] = useState(false)
  const [editSpanish, setEditSpanish] = useState(false)
  const [revised, setRevised] = useState<Record<string, string>>(chunk?.revised ?? {})
  const [translations, setTranslations] = useState<Record<string, string>>(chunk?.translations ?? {})
  const [rejecting, setRejecting] = useState(false)
  const [reason, setReason] = useState("")
  if (!chunk) return <p className="reader-empty">Salve o escopo para carregar os trechos.</p>
  const ready = chunk.status === "ready"
  const base = { chunk_id: chunk.id, proposal_id: chunk.proposal_id }
  const hasChanges = (chunk.edits?.length ?? 0) > 0
  return <section className="reader" aria-labelledby="reader-heading">
    <div className="reader-header"><div><h2 id="reader-heading">{chunk.title}</h2><p>{chunk.status === "approved" ? chunk.approval_mode === "automatic" ? "Português validado e aprovado automaticamente" : "Português aprovado no modo manual" : ready ? `${chunk.edits?.length ?? 0} correções propostas` : chunk.status === "rejected" ? "Proposta recusada · gere uma nova revisão" : "Aguardando revisão"}</p></div>
      {chunk.status === "approved" && <Button variant="ghost" disabled={disabled} onClick={() => void action("reopen", { chunk_id: chunk.id })}><RotateCcwIcon data-icon="inline-start" />Reabrir revisão</Button>}
    </div>
    <div className="reader-tabs" role="tablist" aria-label="Versão do trecho">{[["original", "Original"], ["revised", "Revisão"], ["spanish", "Espanhol"]].map(([id, label]) => <button key={id} id={`tab-${id}`} role="tab" aria-selected={pane === id} aria-controls={`pane-${id}`} tabIndex={pane === id ? 0 : -1} onClick={() => setPane(id)} onKeyDown={event => { if (["ArrowLeft", "ArrowRight"].includes(event.key)) { const ids = ["original", "revised", "spanish"]; const next = ids[(ids.indexOf(pane) + (event.key === "ArrowRight" ? 1 : 2)) % 3]; setPane(next); document.getElementById(`tab-${next}`)?.focus() } }}>{label}</button>)}</div>
    <div className="reading-grid" data-pane={pane}>
      <article id="pane-original" className="text-pane original-pane" aria-labelledby="original-heading"><h3 id="original-heading">Original em português</h3><div className="manuscript-text">{chunk.paragraphs.map(p => <p key={p.id}><Highlight text={p.text} ranges={changeRanges(chunk.edits, p.id)} /></p>)}</div></article>
      <article id="pane-revised" className="text-pane revised-pane" aria-labelledby="revised-heading"><div className="pane-heading"><h3 id="revised-heading">{ready ? "Proposta em português" : "Revisão em português"}</h3>{ready && <Button variant="ghost" disabled={disabled} onClick={() => { setRevised(chunk.revised ?? {}); setEdit(!edit) }}><PencilIcon data-icon="inline-start" />{edit ? "Fechar ajuste" : "Ajustar"}</Button>}</div>
        {chunk.revised ? <div className="manuscript-text">{chunk.paragraphs.map(p => edit ? <div key={p.id} className="form-field"><Label htmlFor={`paragraph-${p.id}`}>Parágrafo {p.id}</Label><textarea id={`paragraph-${p.id}`} rows={Math.min(12, Math.max(3, Math.ceil((revised[String(p.id)]?.length ?? 0) / 80)))} value={revised[String(p.id)] ?? ""} onChange={event => setRevised({ ...revised, [p.id]: event.target.value })} disabled={disabled} /></div> : <p key={p.id}><Highlight text={chunk.revised?.[String(p.id)] ?? ""} ranges={changeRanges(chunk.edits, p.id, true)} /></p>)}</div> : <p className="pane-placeholder">Gere a revisão para comparar as correções com o original.</p>}
        {ready && !hasChanges && <p className="field-help">Nenhuma correção proposta neste trecho. Confira o texto antes de aprovar.</p>}
      </article>
      <article id="pane-spanish" className="text-pane spanish-pane" aria-labelledby="spanish-heading"><div className="pane-heading"><h3 id="spanish-heading">Espanhol da América Latina</h3>{chunk.translations && <Button variant="ghost" disabled={disabled} onClick={() => { setTranslations(chunk.translations ?? {}); setEditSpanish(!editSpanish) }}><PencilIcon data-icon="inline-start" />{editSpanish ? "Fechar ajuste" : "Ajustar espanhol"}</Button>}</div>
        {chunk.translations ? <div className="manuscript-text" lang="es-419">{chunk.paragraphs.map(p => editSpanish ? <div key={p.id} className="form-field"><Label htmlFor={`spanish-${p.id}`}>Parágrafo {p.id}</Label><textarea id={`spanish-${p.id}`} value={translations[String(p.id)] ?? ""} rows={4} onChange={event => setTranslations({ ...translations, [p.id]: event.target.value })} disabled={disabled} /></div> : <p key={p.id}>{chunk.translations?.[String(p.id)]}</p>)}</div> : <p className="pane-placeholder">A tradução aparece depois que todo o escopo estiver revisado e aprovado.</p>}
        {editSpanish && <Button disabled={disabled} onClick={() => void action("save-translation", { chunk_id: chunk.id, translations, revision: book.revision }).then(result => { if (result) setEditSpanish(false) })}>Salvar ajuste em espanhol</Button>}
      </article>
    </div>
    {hasChanges && <details className="proposed-changes"><summary>Correções e motivos ({chunk.edits?.length})</summary><ol>{chunk.edits?.map((change, index) => <li key={index}><div className="change-text"><del>{change.original || "Inserir"}</del><span aria-hidden="true">→</span><ins>{change.replacement || "Remover"}</ins></div><p>{change.reason}</p></li>)}</ol></details>}
    {Object.entries(chunk.checks ?? {}).map(([language, check]) => <div key={language} className="feedback-note"><strong>{language === "pt" ? "Validação do português" : "Revisão bilíngue do espanhol"}</strong>{check.issues.length ? <ul>{check.issues.map((issue, index) => <li key={index}>{issue}</li>)}</ul> : language === "es" && !chunk.spanish_checked ? <p>A tradução ou o glossário mudou. Retome o processamento completo para revisar novamente.</p> : <p>Etapa concluída. {check.edits?.length ?? 0} correções adicionais.</p>}{Boolean(check.notes?.length) && <><p>Expressões do original preservadas para decisão do autor:</p><ul>{check.notes!.map((note, index) => <li key={index}>{note}</li>)}</ul></>}</div>)}
    {chunk.feedback && <p className="feedback-note">Motivo da recusa: {chunk.feedback}</p>}
    {ready && <div className="decision-bar"><Button size="lg" disabled={disabled} onClick={() => void action("approve", { ...base, ...(edit ? { revised } : {}) }).then(result => { if (result) setEdit(false) })}><CheckIcon data-icon="inline-start" />{edit ? "Aprovar com meus ajustes" : "Aprovar trecho"}</Button><Button size="lg" variant="outline" disabled={disabled} onClick={() => setRejecting(!rejecting)}><XIcon data-icon="inline-start" />Recusar proposta</Button></div>}
    {rejecting && ready && <form className="reject-form" onSubmit={event => { event.preventDefault(); void action("reject", { ...base, reason }).then(result => { if (result) setRejecting(false) }) }}><Label htmlFor="rejection-reason">O que precisa mudar na revisão?</Label><textarea id="rejection-reason" value={reason} onChange={event => setReason(event.target.value)} placeholder="Ex.: preserve essa expressão do autor…" required rows={3} disabled={disabled} /><div className="actions"><Button type="submit" disabled={disabled || !reason.trim()}>Registrar recusa</Button><Button type="button" variant="ghost" onClick={() => setRejecting(false)}>Cancelar</Button></div></form>}
  </section>
}
