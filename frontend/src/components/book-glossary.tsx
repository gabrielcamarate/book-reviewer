import { useState } from "react"
import { Button } from "./ui/button"
import type { BookDetail } from "@/book-types"

export function BookGlossary({ book, disabled, onDirty, action }: { book: BookDetail; disabled: boolean; onDirty: (dirty: boolean) => void; action: (operation: string, data?: unknown) => Promise<unknown> }) {
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState("")
  const [error, setError] = useState("")
  async function save() {
    const glossary: Record<string, string> = {}
    for (const line of text.split("\n").filter(value => value.trim())) {
      const at = line.indexOf("=")
      if (at < 1 || !line.slice(at + 1).trim()) { setError("Use um termo por linha: português = espanhol."); return }
      glossary[line.slice(0, at).trim()] = line.slice(at + 1).trim()
    }
    const result = await action("glossary", { glossary, revision: book.revision })
    if (result) { setEditing(false); onDirty(false); setError("") }
  }
  return <details className="glossary-panel"><summary>Glossário da tradução ({Object.keys(book.glossary).length} termos)</summary>
    <p className="field-help">As escolhas são compartilhadas entre capítulos. Ao mudar um termo, o app libera os trechos afetados para nova tradução.</p>
    {!editing && <Button disabled={disabled} onClick={() => { setText(Object.entries(book.glossary).map(([pt, es]) => `${pt} = ${es}`).join("\n")); setEditing(true) }}>Editar glossário</Button>}
    {editing ? <div className="book-form"><div className="form-field"><label className="rv-label" htmlFor="shared-glossary">Português = espanhol, um termo por linha</label><textarea id="shared-glossary" rows={6} value={text} onChange={event => { setText(event.target.value); onDirty(true) }} disabled={disabled} aria-invalid={Boolean(error)} /></div>{error && <p role="alert" className="form-error">{error}</p>}<div className="actions"><Button variant="primary" disabled={disabled} onClick={() => void save()}>Salvar glossário</Button><Button onClick={() => { setEditing(false); onDirty(false); setError("") }} disabled={disabled}>Cancelar</Button></div></div> : <dl>{Object.entries(book.glossary).map(([pt, es]) => <div key={pt}><dt>{pt}</dt><dd lang="es-419">{es}</dd></div>)}</dl>}
  </details>
}
