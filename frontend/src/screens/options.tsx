import { useState } from "react"
import { PlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Choice } from "@/components/ui/choice"
import { Field, Input, Textarea } from "@/components/ui/field"
import { TextLink } from "@/components/ui/link"
import { SegmentedControl } from "@/components/ui/segmented-control"
import { SummaryRows } from "@/components/ui/summary-row"
import type { BookDetail } from "@/book-types"
import { scopeLabel, termsLabel } from "@/lib/copy"
import { setManual, useManual } from "@/lib/manual"
import { setTextSize, setTheme, useTextSize, useThemeChoice, type TextSize, type ThemeChoice } from "@/lib/theme"
import { cn } from "@/lib/utils"
import { useIsMobile } from "@/lib/viewport"
import { CardTitle, Columns, PageTitle } from "@/screens/parts"

type Save = (operation: string, data?: unknown) => Promise<unknown>

function Actions({ children }: { children: React.ReactNode }) {
  const mobile = useIsMobile()
  return <div className={cn("rv-actions", mobile && "rv-actions--stack")}>{children}</div>
}

function started(book: BookDetail) {
  return book.chunks.some(chunk => chunk.status !== "pending" || chunk.translated)
}

/** escolher-capitulos: the whole book or some chapters, before the review starts. */
export function ChaptersScreen({ book, busy, onBack, save }: { book: BookDetail; busy: boolean; onBack: () => void; save: Save }) {
  const mobile = useIsMobile()
  const forced = Boolean(book.destination_filename)
  const [scope, setScope] = useState<"whole" | "sections">(forced ? "sections" : book.settings.scope)
  const [selected, setSelected] = useState<string[]>(book.settings.section_ids)
  const [error, setError] = useState("")
  const count = selected.length
  async function submit() {
    if (scope === "sections" && !count) { setError("Marque pelo menos um capítulo."); return }
    if (await save("configure", { scope, section_ids: scope === "sections" ? selected : [] })) onBack()
  }
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div>
      <PageTitle eyebrow={book.name}>O que revisar</PageTitle>
      {forced ? <p className="rv-muted">Como a tradução vai para um Word em espanhol que você já tem, escolha os capítulos que entram nele.</p>
        : <div role="radiogroup" aria-label="O que revisar" className="rv-cards">
          <Choice name="escopo" checked={scope === "whole"} onChange={() => setScope("whole")} title="O livro inteiro" text="Todos os capítulos, do começo ao fim." />
          <Choice name="escopo" checked={scope === "sections"} onChange={() => setScope("sections")} title="Só alguns capítulos" text="Você marca abaixo quais entram." />
        </div>}
      {scope === "sections" && <div className="rv-stack rv-stack--sm">
        <div className="rv-page-title rv-page-title--row">
          <strong role="status">{count === 1 ? "1 capítulo escolhido" : `${count} capítulos escolhidos`}</strong>
          <div className="rv-actions">
            <TextLink onClick={() => setSelected(book.sections.map(section => section.key))}>Marcar todos</TextLink>
            <TextLink onClick={() => setSelected([])}>Desmarcar todos</TextLink>
          </div>
        </div>
        <div role="group" aria-label="Capítulos do livro" className={mobile ? "rv-stack rv-stack--xs" : "rv-cards"}>
          {book.sections.map(section => (
            <Choice key={section.key} type="checkbox" row checked={selected.includes(section.key)} disabled={busy}
              onChange={event => setSelected(event.target.checked ? [...selected, section.key] : selected.filter(key => key !== section.key))}
              title={section.title} text={section.paragraph_ids.length === 1 ? "1 parágrafo" : `${section.paragraph_ids.length} parágrafos`} />
          ))}
        </div>
      </div>}
      <p className="rv-help">Depois que a revisão começa, não dá mais para mudar esta escolha.</p>
      {error && <p className="rv-error" role="alert">{error}</p>}
      <Actions>
        <Button variant="primary" size="lg" block={mobile} onClick={() => void submit()} disabled={busy}>Salvar e voltar</Button>
        <Button block={mobile} onClick={onBack} disabled={busy}>Cancelar</Button>
      </Actions>
    </>
  )
}

/** orientacoes: what the review must respect, before it starts. */
export function InstructionsScreen({ book, busy, onBack, save }: { book: BookDetail; busy: boolean; onBack: () => void; save: Save }) {
  const mobile = useIsMobile()
  const [text, setText] = useState(book.settings.instructions)
  async function submit() {
    if (await save("configure", { instructions: text })) onBack()
  }
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle eyebrow={book.name}>Orientações para a revisão</PageTitle>
        <p className="rv-muted">Escreva aqui o que o Revisor deve respeitar no seu texto. Não é obrigatório.</p>
      </div>
      <Columns
        main={<Card aria-label="Escrever as orientações">
          <Field id="orientacoes" label="O que deve ficar como você escreveu" help="Uma orientação por linha fica mais fácil de ler.">
            <Textarea id="orientacoes" rows={8} value={text} maxLength={12000} onChange={event => setText(event.target.value)} disabled={busy} />
          </Field>
          <Actions>
            <Button variant="primary" block={mobile} onClick={() => void submit()} disabled={busy}>Salvar orientações</Button>
            <Button block={mobile} onClick={onBack} disabled={busy}>Cancelar</Button>
          </Actions>
        </Card>}
        side={<Card variant="outline" aria-labelledby="exemplos-titulo">
          <CardTitle id="exemplos-titulo">Exemplos do que escrever</CardTitle>
          <ul className="rv-bullets">
            <li>Nomes e apelidos que não devem ser corrigidos.</li>
            <li>Jeitos de falar dos personagens.</li>
            <li>Escolhas de pontuação, como travessões nos diálogos.</li>
          </ul>
          <p className="rv-muted">Depois que a revisão começa, as orientações ficam fixas.</p>
        </Card>}
      />
    </>
  )
}

/** glossario: Portuguese and Spanish terms, two fields per term. */
export function GlossaryScreen({ book, busy, onBack, save }: { book: BookDetail; busy: boolean; onBack: () => void; save: Save }) {
  const mobile = useIsMobile()
  const [rows, setRows] = useState(() => Object.entries(book.glossary).map(([pt, es], index) => ({ id: index, pt, es })))
  const [checked, setChecked] = useState(false)
  const missing = (row: { pt: string; es: string }) => (row.pt.trim() && !row.es.trim() ? "Falta a palavra em espanhol." : !row.pt.trim() && row.es.trim() ? "Falta a palavra em português." : "")
  async function submit() {
    setChecked(true)
    if (rows.some(row => missing(row))) return
    const glossary = Object.fromEntries(rows.filter(row => row.pt.trim()).map(row => [row.pt.trim(), row.es.trim()]))
    if (await save("glossary", { glossary, revision: book.revision })) onBack()
  }
  const update = (id: number, field: "pt" | "es", value: string) => setRows(rows.map(row => (row.id === id ? { ...row, [field]: value } : row)))
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar às opções</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle>Glossário da tradução</PageTitle>
        <p className="rv-muted">Como certas palavras devem ficar em espanhol, sempre do mesmo jeito. O Revisor também anota aqui as escolhas que faz durante a tradução.</p>
      </div>
      <Card aria-label="Termos do glossário">
        <div className={cn("rv-terms", mobile && "rv-terms--stack")}>
          {!mobile && <><span className="rv-terms__head">Em português</span><span className="rv-terms__head">Em espanhol</span><span /></>}
          {rows.map((row, index) => {
            const error = checked ? missing(row) : ""
            return [
              <Input key={`${row.id}-pt`} type="text" value={row.pt} aria-label={`Termo em português, linha ${index + 1}`} placeholder={mobile ? "Em português" : undefined} onChange={event => update(row.id, "pt", event.target.value)} disabled={busy} aria-invalid={error.includes("português") || undefined} />,
              <Input key={`${row.id}-es`} type="text" lang="es-419" value={row.es} aria-label={`Termo em espanhol, linha ${index + 1}`} placeholder={mobile ? "Em espanhol" : undefined} onChange={event => update(row.id, "es", event.target.value)} disabled={busy} aria-invalid={error.includes("espanhol") || undefined} aria-describedby={error ? `termo-erro-${row.id}` : undefined} />,
              <TextLink key={`${row.id}-x`} variant="quiet" aria-label={`Remover a linha ${index + 1}`} onClick={() => setRows(rows.filter(item => item.id !== row.id))} disabled={busy}>Remover</TextLink>,
              error ? <p key={`${row.id}-e`} id={`termo-erro-${row.id}`} className="rv-error rv-terms__error" role="alert">{error}</p> : null,
            ]
          })}
        </div>
        <div><Button onClick={() => setRows([...rows, { id: Math.max(-1, ...rows.map(row => row.id)) + 1, pt: "", es: "" }])} disabled={busy}><PlusIcon size={20} aria-hidden="true" />Adicionar termo</Button></div>
      </Card>
      <p className="rv-muted">Se você mudar um termo, os trechos que usam essa palavra são traduzidos de novo.</p>
      <Actions>
        <Button variant="primary" size="lg" block={mobile} onClick={() => void submit()} disabled={busy}>Salvar glossário</Button>
        <Button block={mobile} onClick={onBack} disabled={busy}>Cancelar</Button>
      </Actions>
    </>
  )
}

type OptionsProps = {
  book: BookDetail | null
  onBack: (() => void) | null
  go: (view: "escolher-capitulos" | "orientacoes" | "glossario" | "alertas") => void
}

/** mais-opcoes: appearance and the optional settings of the open book. */
export function OptionsScreen({ book, onBack, go }: OptionsProps) {
  const mobile = useIsMobile()
  const theme = useThemeChoice()
  const size = useTextSize()
  const manual = useManual(book?.id ?? null)
  const locked = book ? started(book) : true
  const warnings = book?.consistency_warnings.length ?? 0
  const terms = book ? Object.entries(book.glossary) : []
  return (
    <>
      {onBack && <div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div>}
      <div className="rv-stack rv-stack--sm">
        <PageTitle>{mobile ? "Opções" : "Mais opções"}</PageTitle>
        <p className="rv-muted">Nada aqui é obrigatório. O Revisor funciona bem sem mexer em nenhuma destas opções.</p>
      </div>
      <div className="rv-cards">
        <Card variant="outline" aria-labelledby="aparencia-titulo">
          <CardTitle id="aparencia-titulo">Aparência</CardTitle>
          <div className="rv-stack rv-stack--xs">
            <span className="ui-strong">Tema</span>
            <SegmentedControl<ThemeChoice> label="Tema" variant={mobile ? "stack" : "default"} value={theme} onChange={setTheme} options={[{ value: "dark", label: "Escuro" }, { value: "light", label: "Claro" }, { value: "system", label: "Igual ao do aparelho" }]} />
          </div>
          <div className="rv-stack rv-stack--xs">
            <span className="ui-strong">Tamanho do texto</span>
            <SegmentedControl<TextSize> label="Tamanho do texto" variant={mobile ? "block" : "default"} value={size} onChange={setTextSize} options={[{ value: "normal", label: "Normal" }, { value: "large", label: "Grande" }, { value: "larger", label: "Muito grande" }]} />
          </div>
        </Card>
        {book && <>
          <Card variant="outline" aria-labelledby="escopo-titulo">
            <CardTitle id="escopo-titulo">O que revisar</CardTitle>
            <p className="ui-strong">{scopeLabel(book.settings.scope, book.settings.section_ids.length)}</p>
            {locked ? <p className="rv-muted">Não dá para mudar depois que a revisão começou. Para revisar outros capítulos, importe o livro de novo e escolha antes de começar.</p>
              : <div><TextLink onClick={() => go("escolher-capitulos")}>Mudar</TextLink></div>}
          </Card>
          <Card variant="outline" aria-labelledby="orientacoes-titulo">
            <CardTitle id="orientacoes-titulo">Orientações para a revisão</CardTitle>
            <p className="rv-muted">Nomes, apelidos e expressões que devem ficar exatamente como você escreveu.</p>
            <p className="ui-strong">{book.settings.instructions.trim() ? "Orientações escritas" : "Nenhuma orientação escrita"}</p>
            {locked ? <p className="rv-help">As orientações ficam fixas depois que a revisão começa.</p>
              : <div><TextLink onClick={() => go("orientacoes")}>{book.settings.instructions.trim() ? "Ver e mudar" : "Escrever"}</TextLink></div>}
          </Card>
          <Card variant="outline" aria-labelledby="glossario-titulo">
            <CardTitle id="glossario-titulo">Glossário da tradução</CardTitle>
            <p className="rv-muted">Como certas palavras devem ficar em espanhol, sempre do mesmo jeito.</p>
            {terms.length ? <SummaryRows items={terms.slice(0, 5).map(([pt, es]) => ({ term: pt, value: <span lang="es-419">{es}</span> }))} /> : <p className="ui-strong">{termsLabel(0)}</p>}
            {terms.length > 5 && <p className="rv-help">E mais {terms.length - 5}.</p>}
            <div><Button onClick={() => go("glossario")}>Editar glossário</Button></div>
          </Card>
          <Card variant="outline" aria-labelledby="manual-titulo">
            <CardTitle id="manual-titulo">Aprovar as correções à mão</CardTitle>
            <p className="rv-muted">{manual ? "Você aprova ou recusa cada trecho antes da tradução." : "Hoje o Revisor confere e aplica as correções sozinho. Ligue esta opção se quiser aprovar ou recusar cada trecho antes da tradução."}</p>
            <p className="ui-strong">{manual ? "Ligado" : "Desligado"}</p>
            <div><Button onClick={() => { setManual(book.id, !manual); if (!manual && onBack) onBack() }}>{manual ? "Desligar aprovação à mão" : "Ligar aprovação à mão"}</Button></div>
          </Card>
          <Card variant="outline" aria-labelledby="alertas-titulo">
            <CardTitle id="alertas-titulo">Alertas de consistência</CardTitle>
            <p className="rv-muted">Avisos sobre nomes e palavras que aparecem escritos de mais de um jeito no livro.</p>
            <p className="ui-strong">{warnings === 0 ? "Nenhum alerta" : warnings === 1 ? "1 alerta para conferir" : `${warnings} alertas para conferir`}</p>
            {warnings > 0 && <div><Button onClick={() => go("alertas")}>Ver os alertas</Button></div>}
          </Card>
          <Card variant="outline" aria-labelledby="sobre-titulo">
            <CardTitle id="sobre-titulo">Sobre este livro</CardTitle>
            <SummaryRows items={[
              { term: "Arquivo", value: <span className="rv-file__name">{book.filename}</span> },
              ...(book.destination_filename ? [{ term: "Word em espanhol", value: <span className="rv-file__name">{book.destination_filename}</span> }] : []),
              ...(book.author ? [{ term: "Autoria", value: book.author }] : []),
              { term: "Modelo", value: `${book.model.toUpperCase().replace(/-/g, " ")} · esforço ${book.reasoning_effort}` },
            ]} />
          </Card>
        </>}
      </div>
    </>
  )
}

function chunkLabel(book: BookDetail, chunkId: string) {
  const index = book.chunks.findIndex(chunk => chunk.id === chunkId)
  return index === -1 ? "" : `Trecho ${index + 1} · ${book.chunks[index].title}`
}

/** alertas: names and words written more than one way. */
export function AlertsScreen({ book, onBack, onOpenChunk }: { book: BookDetail; onBack: () => void; onOpenChunk: (chunkId: string) => void }) {
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar às opções</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle>Alertas de consistência</PageTitle>
        <p className="rv-muted">São só avisos para você conferir. Formas diferentes da mesma palavra podem ser de propósito, e nada foi alterado por causa deles.</p>
      </div>
      {book.consistency_warnings.length ? <ol className="rv-list">
        {book.consistency_warnings.map((warning, index) => (
          <li key={index}>
            <span className="rv-small rv-muted">{chunkLabel(book, warning.chunk_id)}</span>
            <p>{warning.message}</p>
            <div><TextLink onClick={() => onOpenChunk(warning.chunk_id)}>Abrir este trecho</TextLink></div>
          </li>
        ))}
      </ol> : <p className="ui-strong">Nenhum alerta para conferir.</p>}
    </>
  )
}

/** observacoes: ambiguities of the original kept for the author to decide. */
export function NotesScreen({ book, onBack, onOpenChunk }: { book: BookDetail; onBack: () => void; onOpenChunk: (chunkId: string) => void }) {
  const notes = book.editorial_notes ?? []
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle>Observações para você</PageTitle>
        <p className="rv-muted">São pontos em que o seu texto original permite mais de uma leitura. Nada foi inventado para resolver: o texto ficou como estava, e a decisão é sua.</p>
      </div>
      {notes.length ? <ol className="rv-list">
        {notes.map((note, index) => (
          <li key={index}>
            <span className="rv-small rv-muted">Trecho {note.index} · {note.title} · {note.language === "pt" ? "no português" : "no espanhol"}</span>
            <p>{note.message}</p>
            <div><TextLink onClick={() => onOpenChunk(note.chunk_id)}>Abrir este trecho</TextLink></div>
          </li>
        ))}
      </ol> : <p className="ui-strong">Nenhuma observação para este livro.</p>}
    </>
  )
}
