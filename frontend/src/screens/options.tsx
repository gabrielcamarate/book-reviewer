import { useState } from "react"
import { PlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Choice } from "@/components/ui/choice"
import { ConfirmDialog } from "@/components/ui/dialog"
import { Field, Input, Textarea } from "@/components/ui/field"
import { StatusIcon } from "@/components/ui/notice"
import { ProgressBar } from "@/components/ui/progress"
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
        <Button variant="primary" size="lg" block={mobile} onClick={() => submit()} disabled={busy}>Salvar e voltar</Button>
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
            <Button variant="primary" block={mobile} onClick={() => submit()} disabled={busy}>Salvar orientações</Button>
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
        <Button variant="primary" size="lg" block={mobile} onClick={() => submit()} disabled={busy}>Salvar glossário</Button>
        <Button block={mobile} onClick={onBack} disabled={busy}>Cancelar</Button>
      </Actions>
    </>
  )
}

function times(n: number) {
  return n === 1 ? "1 vez" : `${n} vezes`
}

/** Author spellings found in the original (eXilados, CamaraTTe) and kept by the app, plus the ones the author adds. */
function SpellingsCard({ book, busy, save }: { book: BookDetail; busy: boolean; save: Save }) {
  const [word, setWord] = useState("")
  const [error, setError] = useState("")
  const { auto, suggested, added, removed, active } = book.spellings
  const counts = new Map([...auto, ...suggested].map(item => [item.word, item.count]))
  const running = book.job?.status === "running" || book.job?.status === "stopping"
  const update = (nextAdded: string[], nextRemoved: string[]) => save("spellings", { added: nextAdded, removed: nextRemoved })
  const keep = (value: string) => update([...new Set([...added, value])], removed.filter(item => item !== value))
  const drop = (value: string) => update(added.filter(item => item !== value), auto.some(item => item.word === value) ? [...new Set([...removed, value])] : removed)
  async function add() {
    const value = word.trim()
    if (!value || /\s/.test(value)) { setError("Escreva uma palavra só, do jeito que está no livro."); return }
    setError("")
    if (await keep(value)) setWord("")
  }
  return (
    <Card variant="outline" aria-labelledby="grafias-titulo">
      <CardTitle id="grafias-titulo">Grafias de quem escreveu</CardTitle>
      <p className="rv-muted">Palavras escritas de um jeito próprio, como letras maiúsculas no meio. O Revisor encontra as que se repetem no livro e nunca as corrige.</p>
      {active.length ? <SummaryRows items={active.map(item => ({
        term: item,
        value: <span className="rv-muted rv-num">{counts.has(item) ? times(counts.get(item)!) : "acrescentada por você"}</span>,
        action: <TextLink variant="quiet" onClick={() => drop(item)} disabled={busy}>Deixar de proteger</TextLink>,
      }))} /> : <p className="ui-strong">Nenhuma grafia protegida.</p>}
      {(suggested.length > 0 || removed.length > 0) && <div className="rv-stack rv-stack--xs">
        <span className="ui-strong">Talvez também</span>
        <SummaryRows items={[...suggested.map(item => item.word), ...removed].filter((item, index, list) => list.indexOf(item) === index && !active.includes(item)).map(item => ({
          term: item,
          value: <span className="rv-muted rv-num">{counts.has(item) ? times(counts.get(item)!) : ""}</span>,
          action: <TextLink onClick={() => keep(item)} disabled={busy}>Proteger</TextLink>,
        }))} />
      </div>}
      <Field id="nova-grafia" label="Acrescentar uma grafia" error={error || undefined} help={running ? "Vale já para os próximos trechos. Os já revisados são ajustados no fim do processamento, antes de gerar os Word." : "Os trechos já revisados voltam a usar a grafia na hora; só esses são traduzidos de novo."}>
        <div className="rv-actions">
          <Input id="nova-grafia" type="text" value={word} placeholder="Ex.: eXilados" onChange={event => setWord(event.target.value)} disabled={busy} aria-invalid={Boolean(error) || undefined} />
          <Button onClick={() => add()} disabled={busy}>Acrescentar</Button>
        </div>
      </Field>
    </Card>
  )
}

/** Start the book over or take it out of the list, each after a confirmation. */
function BookCard({ book, busy, save, onRemove }: { book: BookDetail; busy: boolean; save: Save; onRemove: () => Promise<unknown> }) {
  const mobile = useIsMobile()
  const [asking, setAsking] = useState<"reset" | "remove" | null>(null)
  const running = book.job?.status === "running" || book.job?.status === "stopping"
  return (
    <Card variant="outline" aria-labelledby="livro-titulo">
      <CardTitle id="livro-titulo">Este livro</CardTitle>
      <p className="rv-muted">Para mudar o que revisar ou as orientações depois de começar, recomece o livro. Para tirar um livro importado por engano, remova.</p>
      <div className={cn("rv-actions", mobile && "rv-actions--stack")}>
        <Button block={mobile} onClick={() => setAsking("reset")} disabled={busy || running}>Recomeçar do zero</Button>
        <Button block={mobile} onClick={() => setAsking("remove")} disabled={busy || running}>Remover este livro</Button>
      </div>
      {running && <p className="rv-help">Pause o processamento antes de recomeçar ou remover.</p>}
      <ConfirmDialog open={asking === "reset"} onOpenChange={open => setAsking(open ? "reset" : null)}
        title={`Recomeçar “${book.name}” do zero?`}
        description="Todas as correções, aprovações e traduções voltam ao início. O arquivo original, as grafias protegidas e o glossário ficam. O trabalho de agora fica guardado numa cópia dentro da pasta do livro."
        confirm={<Button variant="primary" onClick={() => save("reset").then(() => setAsking(null))}>Recomeçar do zero</Button>}
        cancel={<Button onClick={() => setAsking(null)}>Voltar sem mudar nada</Button>} />
      <ConfirmDialog open={asking === "remove"} onOpenChange={open => setAsking(open ? "remove" : null)}
        title={`Remover “${book.name}”?`}
        description="O livro sai de Meus livros. Os arquivos dele vão para a pasta .removidos, dentro da pasta de livros, e podem ser recuperados por quem instalou o Revisor."
        confirm={<Button variant="primary" onClick={() => onRemove().then(() => setAsking(null))}>Remover o livro</Button>}
        cancel={<Button onClick={() => setAsking(null)}>Voltar sem remover</Button>} />
    </Card>
  )
}

type OptionsProps = {
  book: BookDetail | null
  busy: boolean
  save: Save
  onRemove: () => Promise<unknown>
  onBack: (() => void) | null
  go: (view: "escolher-capitulos" | "orientacoes" | "glossario" | "alertas") => void
}

/** mais-opcoes: appearance and the optional settings of the open book. */
export function OptionsScreen({ book, busy, save, onRemove, onBack, go }: OptionsProps) {
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
          <SpellingsCard book={book} busy={busy} save={save} />
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
          <BookCard book={book} busy={busy} save={save} onRemove={onRemove} />
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

const GROUPS = 6

/** observacoes: ambiguities of the original kept for the author; each one can be marked as read. */
export function NotesScreen({ book, busy, onBack, onOpenChunk, onAdjustChunk, save }: { book: BookDetail; busy: boolean; onBack: () => void; onOpenChunk: (chunkId: string) => unknown; onAdjustChunk: (chunkId: string) => unknown; save: Save }) {
  const mobile = useIsMobile()
  const notes = book.editorial_notes ?? []
  const unread = notes.filter(note => !note.read)
  const [tab, setTab] = useState<"unread" | "read">(unread.length ? "unread" : "read")
  const [shown, setShown] = useState(GROUPS)
  const visible = notes.filter(note => (tab === "unread" ? !note.read : note.read))
  const groups = [...new Set(visible.map(note => note.chunk_id))].map(chunkId => ({ chunkId, notes: visible.filter(note => note.chunk_id === chunkId) }))
  const mark = (ids: string[], read: boolean) => save("notes", { ids, read })
  return (
    <>
      <div><TextLink variant="back" onClick={onBack}>Voltar ao livro</TextLink></div>
      <div className="rv-stack rv-stack--sm">
        <PageTitle>Observações para você</PageTitle>
        <p className="rv-muted">São pontos em que o seu texto original permite mais de uma leitura. Nada foi inventado para resolver: o texto ficou como estava, e a decisão é sua. Depois de ler, marque como lida.</p>
      </div>
      {!notes.length ? <p className="ui-strong">Nenhuma observação para este livro.</p> : <>
        <Card variant={unread.length ? "default" : "outline"} aria-labelledby="leitura-titulo">
          <div className="rv-toolbar">
            <div className="rv-stack rv-stack--xs">
              {unread.length ? <strong id="leitura-titulo" role="status">{`${notes.length - unread.length} de ${notes.length} lidas`}</strong>
                : <div role="status" className="rv-status-row"><StatusIcon /><strong id="leitura-titulo">Você leu todas as observações</strong></div>}
              {unread.length > 0 && <p className="rv-small rv-muted">{unread.length === 1 ? "Falta 1 para ler." : `Faltam ${unread.length} para ler.`} Ler não muda o livro; serve para você saber o que já viu.</p>}
            </div>
            {unread.length > 0 && <Button block={mobile} onClick={() => mark(unread.map(note => note.id), true)} disabled={busy}>Marcar todas como lidas</Button>}
          </div>
          {unread.length > 0 && <ProgressBar value={((notes.length - unread.length) / notes.length) * 100} label="Observações lidas" />}
        </Card>
        <SegmentedControl<"unread" | "read"> label="Quais observações mostrar" variant={mobile ? "block" : "default"} value={tab} onChange={value => { setTab(value); setShown(GROUPS) }}
          options={[{ value: "unread", label: `Para ler (${unread.length})` }, { value: "read", label: `Lidas (${notes.length - unread.length})` }]} />
        {!groups.length ? <p className="rv-muted">{tab === "unread" ? "Nada para ler. Todas as observações já foram lidas." : "Nenhuma observação lida ainda."}</p> : <ol className="rv-list">
          {groups.slice(0, shown).map(group => (
            <li key={group.chunkId}>
              <div className="rv-toolbar">
                <h2 className="ui-strong">Trecho {group.notes[0].index} · {group.notes[0].title}</h2>
                <div className="rv-actions">
                  <TextLink onClick={() => onOpenChunk(group.chunkId)}>Abrir este trecho</TextLink>
                  {book.chunks.find(chunk => chunk.id === group.chunkId)?.status === "approved" && <TextLink onClick={() => onAdjustChunk(group.chunkId)}>Ajustar o português</TextLink>}
                </div>
              </div>
              <ul className="rv-stack rv-stack--sm">
                {group.notes.map(note => (
                  <li key={note.id} className="rv-note">
                    <div className="rv-stack rv-stack--xs">
                      <span className="rv-small rv-muted">{note.language === "pt" ? "No português" : "No espanhol"}</span>
                      <p>{note.message}</p>
                    </div>
                    {note.read ? <TextLink variant="quiet" onClick={() => mark([note.id], false)} disabled={busy}>Marcar como não lida</TextLink>
                      : <Button onClick={() => mark([note.id], true)} disabled={busy}>Marcar como lida</Button>}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>}
        {groups.length > shown && <div className="rv-actions">
          <Button onClick={() => setShown(shown + GROUPS)}>Mostrar mais trechos</Button>
          <span className="rv-muted rv-num">Mostrando {shown} de {groups.length} trechos</span>
        </div>}
      </>}
    </>
  )
}
