import { useState } from "react"
import { ChevronDownIcon, FileUpIcon, PlusIcon, UploadIcon } from "lucide-react"
import { Button } from "./ui/button"
import { Label } from "./ui/label"
import { Spinner } from "./ui/spinner"
import type { BookDetail } from "@/book-types"

export function ImportBook({ busy, onImport, onCancel }: { busy: boolean; onImport: (name: string, source: File, destination?: File) => Promise<boolean>; onCancel?: () => void }) {
  const [name, setName] = useState("")
  const [source, setSource] = useState<File>()
  const [destination, setDestination] = useState<File>()
  const [withDestination, setWithDestination] = useState(false)
  return <section className="import-panel" aria-labelledby="import-title">
    <div className="section-heading"><FileUpIcon aria-hidden="true" /><div><h2 id="import-title">Importar um livro</h2><p>Trabalhe em uma cópia. Seus arquivos originais permanecem preservados.</p></div></div>
    <form onSubmit={event => { event.preventDefault(); if (source) void onImport(name, source, withDestination ? destination : undefined) }} className="book-form">
      <div className="form-field"><Label htmlFor="book-name">Nome do trabalho <span className="text-muted-foreground">(opcional)</span></Label><input id="book-name" value={name} onChange={event => setName(event.target.value)} placeholder="Ex.: Meu romance" maxLength={200} disabled={busy} /></div>
      <div className="form-field"><Label htmlFor="source-file">Manuscrito em português (.docx)</Label><input id="source-file" type="file" accept=".docx" required onChange={event => setSource(event.target.files?.[0])} disabled={busy} /><p className="field-help">Livro inteiro ou arquivo com as seções que você deseja revisar. Até 32 MB.</p></div>
      <label className="check-row"><input type="checkbox" checked={withDestination} onChange={event => setWithDestination(event.target.checked)} disabled={busy} />Inserir as seções traduzidas em um Word espanhol existente</label>
      {withDestination && <div className="form-field"><Label htmlFor="destination-file">Livro em espanhol que receberá as seções (.docx)</Label><input id="destination-file" type="file" accept=".docx" required onChange={event => setDestination(event.target.files?.[0])} disabled={busy} /><p className="field-help">O restante desse livro será preservado. Você receberá um novo arquivo.</p></div>}
      <div className="actions"><Button type="submit" size="lg" disabled={busy || !source || (withDestination && !destination)}>{busy ? <Spinner data-icon="inline-start" /> : <UploadIcon data-icon="inline-start" />}{busy ? "Importando…" : "Importar Word"}</Button>{onCancel && <Button type="button" variant="ghost" onClick={onCancel} disabled={busy}>Cancelar</Button>}</div>
    </form>
  </section>
}

export function BookSetup({ book, locked, busy, onSave, onDirty }: { book: BookDetail; locked: boolean; busy: boolean; onSave: (data: unknown) => Promise<unknown>; onDirty: () => void }) {
  const [scope, setScope] = useState(book.settings.scope)
  const [selected, setSelected] = useState(book.settings.section_ids)
  const [instructions, setInstructions] = useState(book.settings.instructions)
  const [terms, setTerms] = useState(Object.entries(book.settings.glossary).map(([pt, es]) => `${pt} = ${es}`).join("\n"))
  const [formError, setFormError] = useState("")
  function save() {
    const glossary: Record<string, string> = {}
    for (const line of terms.split("\n").filter(line => line.trim())) {
      const at = line.indexOf("=")
      if (at < 1 || !line.slice(at + 1).trim()) { setFormError("Use um termo por linha, no formato português = espanhol."); return }
      glossary[line.slice(0, at).trim()] = line.slice(at + 1).trim()
    }
    setFormError(""); void onSave({ scope, section_ids: selected, instructions, glossary })
  }
  return <details className="setup-panel" open={!locked || undefined}>
    <summary>Escopo e critérios editoriais <span>{book.settings.scope === "whole" ? "Livro inteiro" : `${book.settings.section_ids.length} seções`}</span><ChevronDownIcon className="disclosure-icon" aria-hidden="true" /></summary>
    <div className="book-form" onChangeCapture={onDirty}>
      {locked && <p className="field-help">O escopo está fixado porque a revisão já começou. Para outro escopo, importe uma nova cópia.</p>}
      <fieldset disabled={locked || busy}><legend>O que você deseja revisar e traduzir?</legend><div className="scope-options"><label className="check-row"><input type="radio" name="scope" value="whole" checked={scope === "whole"} disabled={Boolean(book.destination_filename)} onChange={() => setScope("whole")} />Livro inteiro</label><label className="check-row"><input type="radio" name="scope" value="sections" checked={scope === "sections"} onChange={() => setScope("sections")} />Seções escolhidas</label></div>
        {scope === "sections" && <div className="section-options">{book.sections.map(section => <label key={section.key} className="check-row"><input type="checkbox" checked={selected.includes(section.key)} onChange={event => setSelected(event.target.checked ? [...selected, section.key] : selected.filter(key => key !== section.key))} /><span>{section.title}<small>Parágrafos {section.start}–{section.end} do corpo · {section.paragraph_ids.length} com texto</small></span></label>)}</div>}
      </fieldset>
      <p className="field-help">Todo o texto escolhido entra como pendente de revisão. Títulos do sumário não são usados para localizar Epílogo e Posfácio.</p>
      <div className="form-field"><Label htmlFor="editorial-instructions">Orientações do autor <span className="text-muted-foreground">(opcional)</span></Label><textarea id="editorial-instructions" rows={3} value={instructions} onChange={event => setInstructions(event.target.value)} disabled={locked || busy} placeholder="Nomes que devem ser preservados, escolhas de pontuação…" maxLength={12000} /></div>
      <div className="form-field"><Label htmlFor="glossary-input">Glossário português → espanhol <span className="text-muted-foreground">(opcional)</span></Label><textarea id="glossary-input" rows={3} value={terms} onChange={event => setTerms(event.target.value)} disabled={locked || busy} placeholder={"Terra = Tierra\nCada termo em uma linha"} aria-invalid={Boolean(formError)} /><p className="field-help">O app também registra escolhas terminológicas durante a tradução.</p></div>
      {formError && <p role="alert" className="form-error">{formError}</p>}
      {!locked && <Button onClick={save} disabled={busy || (scope === "sections" && selected.length === 0)}>Salvar escopo e critérios</Button>}
      {book.destination_filename && <p className="destination-note">Destino: <strong>{book.destination_filename}</strong></p>}
    </div>
  </details>
}

export function NewBookButton({ onClick, disabled }: { onClick: () => void; disabled?: boolean }) { return <Button variant="outline" onClick={onClick} disabled={disabled}><PlusIcon data-icon="inline-start" />Novo livro</Button> }
