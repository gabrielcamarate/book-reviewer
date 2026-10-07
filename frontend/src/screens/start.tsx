import { useState } from "react"
import { UploadIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Check } from "@/components/ui/choice"
import { Field, Input } from "@/components/ui/field"
import { FilePicker } from "@/components/ui/file-picker"
import { TextLink } from "@/components/ui/link"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"
import { useIsMobile } from "@/lib/viewport"
import { WHAT_IT_DOES } from "@/lib/copy"
import { CardTitle, Columns, NumberedList, PageTitle } from "@/screens/parts"

function WhatItDoes() {
  return (
    <Card variant="outline" aria-labelledby="oque-titulo">
      <CardTitle id="oque-titulo">O que o Revisor faz</CardTitle>
      <NumberedList items={WHAT_IT_DOES} />
      <p className="rv-muted">No fim, você baixa dois arquivos Word: o livro revisado em português e o livro em espanhol.</p>
    </Card>
  )
}

/** inicio: no book yet. */
export function StartScreen({ onChoose }: { onChoose: () => void }) {
  const mobile = useIsMobile()
  return (
    <Columns
      main={<Card aria-labelledby="inicio-titulo">
        <h1 id="inicio-titulo" className={mobile ? "title-page-mobile" : "title-page"}>Vamos começar pelo seu livro</h1>
        <p className="rv-muted">O Revisor corrige o português do seu livro, traduz para o espanhol da América Latina e devolve dois arquivos Word. Seu arquivo original não é alterado.</p>
        <Button variant="primary" size="lg" block={mobile} onClick={onChoose}><UploadIcon size={20} aria-hidden="true" />Escolher o arquivo do livro</Button>
        <p className="rv-small rv-muted">Precisa ser um arquivo Word (.docx).</p>
      </Card>}
      side={<WhatItDoes />}
    />
  )
}

type NewBookProps = {
  busy: boolean
  canCancel: boolean
  onCancel: () => void
  onImport: (name: string, source: File, destination?: File) => Promise<boolean>
}

/** novo-livro and novo-livro-com-word-em-espanhol. */
export function NewBookScreen({ busy, canCancel, onCancel, onImport }: NewBookProps) {
  const mobile = useIsMobile()
  const [source, setSource] = useState<File | null>(null)
  const [destination, setDestination] = useState<File | null>(null)
  const [withDestination, setWithDestination] = useState(false)
  const [name, setName] = useState("")
  const [error, setError] = useState("")
  function choose(file: File | null, set: (file: File | null) => void) {
    if (file && !file.name.toLowerCase().endsWith(".docx")) { setError("Este arquivo não é um Word (.docx). Escolha outro."); return }
    if (file && file.size > 32 * 1024 * 1024) { setError("Este arquivo passa de 32 MB. Escolha outro."); return }
    setError("")
    set(file)
  }
  async function submit() {
    if (!source) { setError("Escolha o arquivo do livro em português."); return }
    if (withDestination && !destination) { setError("Escolha o Word em espanhol que vai receber a tradução."); return }
    await onImport(name.trim(), source, withDestination ? destination ?? undefined : undefined)
  }
  return (
    <>
      {canCancel && <div><TextLink variant="back" onClick={onCancel}>Voltar aos meus livros</TextLink></div>}
      <PageTitle>Novo livro</PageTitle>
      <Columns
        main={<Card aria-label="Importar o livro">
          <div className="rv-stack rv-stack--sm">
            <CardTitle>Arquivo do livro em português</CardTitle>
            <FilePicker id="arquivo-livro" file={source} onChange={file => { choose(file, setSource); if (file && !name) setName(file.name.replace(/\.docx$/i, "")) }} disabled={busy} />
          </div>
          <Field id="nome-livro" label="Nome do trabalho" optional>
            <Input id="nome-livro" type="text" value={name} placeholder="Ex.: Meu romance" onChange={event => setName(event.target.value)} disabled={busy} />
          </Field>
          <div className="rv-stack rv-stack--sm">
            <Check checked={withDestination} onChange={event => setWithDestination(event.target.checked)} disabled={busy}>Já tenho um Word em espanhol que vai receber a tradução</Check>
            {withDestination && <div role="group" aria-labelledby="destino-titulo" className="rv-stack rv-stack--sm">
              <h3 id="destino-titulo" className="ui-strong">Livro em espanhol que vai receber os capítulos</h3>
              <FilePicker id="arquivo-destino" file={destination} onChange={file => choose(file, setDestination)} title="Escolher o Word em espanhol" disabled={busy} />
              <p className="rv-help">O restante desse livro é preservado. Você recebe um arquivo novo, e o seu continua como está.</p>
              <p className="rv-help">No próximo passo você escolhe quais capítulos traduzir.</p>
            </div>}
          </div>
          {error && <p className="rv-error" role="alert">{error}</p>}
          <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
            <Button variant="primary" size="lg" block={mobile} onClick={() => submit()} disabled={busy}>{busy ? <><Spinner />Importando…</> : "Importar livro"}</Button>
            {canCancel && <Button block={mobile} onClick={onCancel} disabled={busy}>Cancelar</Button>}
          </div>
        </Card>}
        side={mobile ? undefined : <WhatItDoes />}
      />
    </>
  )
}
