import { DownloadIcon, PauseIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { TextLink } from "@/components/ui/link"
import { StatusIcon } from "@/components/ui/notice"
import { Steps } from "@/components/ui/steps"
import { SummaryRows } from "@/components/ui/summary-row"
import type { BookDetail } from "@/book-types"
import { cn } from "@/lib/utils"
import { stageOf, stageTitle, steps } from "@/lib/screens"
import { useIsMobile } from "@/lib/viewport"
import { STAGE_NAMES, scopeLabel, termsLabel } from "@/lib/copy"
import { CardTitle, Columns, NumberedList, PageTitle } from "@/screens/parts"

export type BookView = "conferir" | "escolher-capitulos" | "orientacoes" | "glossario" | "observacoes" | "alertas" | "trechos" | "ajustar-espanhol" | "novo-livro"

type BookScreenProps = { book: BookDetail; busy: boolean; go: (view: BookView) => void }

function startLabel(book: BookDetail) {
  return book.settings.scope === "whole" ? "Processar o livro completo" : "Processar os capítulos escolhidos"
}

function FilesCard() {
  return (
    <Card variant="outline" aria-labelledby="arquivos-titulo">
      <CardTitle id="arquivos-titulo">Seus arquivos</CardTitle>
      <ul className="rv-summary">
        <li className="rv-summary__row"><span>Livro revisado em português</span><span className="rv-muted">Ainda não está pronto</span></li>
        <li className="rv-summary__row"><span>Livro em espanhol</span><span className="rv-muted">Ainda não está pronto</span></li>
      </ul>
      <p className="rv-muted">Os dois arquivos Word aparecem aqui para baixar quando as quatro etapas terminarem.</p>
    </Card>
  )
}

/** pronto-para-comecar: imported, nothing reviewed yet. */
export function ReadyScreen({ book, busy, go, onStart, otherBook }: BookScreenProps & { onStart: () => void; otherBook?: { name: string; onFollow: () => void } }) {
  const mobile = useIsMobile()
  const locked = Boolean(otherBook)
  const terms = Object.keys(book.glossary).length
  const items = [
    { term: "O que será revisado", value: scopeLabel(book.settings.scope, book.settings.section_ids.length), action: locked ? undefined : <TextLink onClick={() => go("escolher-capitulos")}>Mudar</TextLink> },
    { term: "Orientações para a revisão", value: book.settings.instructions.trim() ? "Escritas" : "Nenhuma", action: locked ? undefined : <TextLink onClick={() => go("orientacoes")}>{book.settings.instructions.trim() ? "Ver e mudar" : "Escrever"}</TextLink> },
    { term: "Glossário da tradução", value: termsLabel(terms), action: locked ? undefined : <TextLink onClick={() => go("glossario")}>Ver e mudar</TextLink> },
    ...(mobile ? [] : [{ term: "Idiomas", value: "Português do Brasil → espanhol da América Latina" }]),
  ]
  return (
    <>
      <PageTitle eyebrow="Livro aberto">{book.name}</PageTitle>
      {otherBook && <div className="rv-notice" role="status"><p className="rv-notice__text"><strong>O Revisor está trabalhando em “{otherBook.name}”.</strong> Ele faz um livro por vez.</p><Button block={mobile} onClick={otherBook.onFollow}>Acompanhar {otherBook.name}</Button></div>}
      <Columns
        main={<Card aria-labelledby="comecar-titulo">
          <CardTitle id="comecar-titulo" main>{otherBook ? "Este livro está na fila" : "Tudo pronto para começar"}</CardTitle>
          <p className="rv-muted">{otherBook ? "Ele pode começar quando o outro terminar ou for pausado. O arquivo já está guardado." : "O livro foi importado. Agora o Revisor corrige o português, traduz para o espanhol e revisa a tradução, tudo em sequência."}</p>
          <SummaryRows items={items} />
          <Button variant="primary" size="lg" block onClick={onStart} disabled={busy || locked} aria-describedby="comecar-ajuda">{startLabel(book)}</Button>
          <p id="comecar-ajuda" className="rv-small rv-muted">{otherBook ? "Disponível quando o outro livro terminar ou for pausado." : "Livros longos levam um bom tempo. Você pode pausar e continuar depois sem perder nada."}</p>
        </Card>}
        side={mobile ? undefined : <Card variant="outline" aria-labelledby="etapas-titulo">
          <CardTitle id="etapas-titulo">As quatro etapas</CardTitle>
          <NumberedList items={STAGE_NAMES} />
          <p className="rv-muted">No fim, você baixa dois arquivos Word.</p>
        </Card>}
      />
    </>
  )
}

/** acompanhar: the four stages while processing runs. */
export function ProgressScreen({ book, busy, go, onPause }: BookScreenProps & { onPause: () => void }) {
  const mobile = useIsMobile()
  const stopping = book.job?.status === "stopping"
  const stage = Math.min(stageOf(book.progress), 3)
  return (
    <>
      <PageTitle eyebrow="Livro aberto">{book.name}</PageTitle>
      <Columns
        main={<Card aria-labelledby="andamento-titulo">
          <div role="status" className="rv-stack rv-stack--xs">
            <p className="ui-label rv-accent">Etapa {stage + 1} de 4</p>
            <CardTitle id="andamento-titulo" main>{stageTitle(book.progress)}</CardTitle>
            <p className="rv-muted">O progresso é salvo a cada trecho. Se precisar parar, é só continuar depois.</p>
          </div>
          <Steps steps={steps(book.progress, true)} />
          <div className="rv-stack rv-stack--xs">
            <Button block={mobile} onClick={onPause} disabled={busy || stopping}><PauseIcon size={20} aria-hidden="true" />{stopping ? "Pausando…" : "Pausar"}</Button>
            <p className="rv-small rv-muted">Termina o que já começou e guarda o progresso.</p>
          </div>
        </Card>}
        side={<>
          {mobile ? <p className="rv-muted">Quando as quatro etapas terminarem, os dois arquivos Word aparecem aqui para baixar.</p> : <FilesCard />}
          <Button block onClick={() => go("conferir")}>Ver o texto e as correções</Button>
        </>}
      />
    </>
  )
}

/** livro-pronto: both Word files ready. */
export function DoneScreen({ book, busy, go, onDownload }: BookScreenProps & { onDownload: (language: "pt-BR" | "es") => void }) {
  const notes = book.editorial_notes?.length ?? 0
  return (
    <>
      <PageTitle eyebrow="Livro aberto">{book.name}</PageTitle>
      <Columns
        main={<Card aria-labelledby="pronto-titulo">
          <div role="status" className="rv-status-row"><StatusIcon /><CardTitle id="pronto-titulo">Seu livro está pronto</CardTitle></div>
          <p className="rv-muted">Revisado em português e traduzido para o espanhol da América Latina. Seus arquivos originais não foram alterados.</p>
          <div className="rv-stack rv-stack--sm">
            <Button variant="primary" size="lg" block className="rv-btn--start" onClick={() => onDownload("es")} disabled={busy}>
              <DownloadIcon size={20} aria-hidden="true" /><span className="rv-btn__text"><span>Baixar o livro em espanhol</span><span className="rv-btn__sub">Arquivo Word</span></span>
            </Button>
            <Button size="lg" block className="rv-btn--start" onClick={() => onDownload("pt-BR")} disabled={busy}>
              <DownloadIcon size={20} aria-hidden="true" /><span className="rv-btn__text"><span>Baixar o livro revisado em português</span><span className="rv-btn__sub rv-muted">Arquivo Word</span></span>
            </Button>
          </div>
          <p className="rv-small rv-muted">A formatação do Word foi preservada. A paginação pode mudar por causa do texto traduzido.</p>
        </Card>}
        side={<>
          {notes > 0 && <Card variant="outline" aria-labelledby="notas-titulo">
            <CardTitle id="notas-titulo">{notes === 1 ? "1 observação para você ler" : `${notes} observações para você ler`}</CardTitle>
            <p className="rv-muted">Em alguns pontos o texto original estava ambíguo. Ele foi mantido como estava, sem inventar nada, e as dúvidas ficaram anotadas.</p>
            <Button block onClick={() => go("observacoes")}>Ler as observações</Button>
          </Card>}
          <div className={cn("rv-stack", "rv-stack--sm")}>
            <Button block onClick={() => go("conferir")}>Ver o texto e as correções</Button>
            <Button block onClick={() => go("novo-livro")}>Começar outro livro</Button>
          </div>
        </>}
      />
    </>
  )
}

type StoppedProps = BookScreenProps & { onContinue: () => void; disabled: boolean }

/** pausado and parou-no-meio: saved work, nothing running. */
export function StoppedScreen({ book, busy, go, onContinue, disabled, failed }: StoppedProps & { failed: boolean }) {
  const stage = Math.min(stageOf(book.progress), 3)
  return (
    <>
      <PageTitle eyebrow="Livro aberto">{book.name}</PageTitle>
      <Columns
        main={<Card variant={failed ? "alert" : "default"} aria-labelledby="parado-titulo">
          {failed ? <>
            <div role="status" className="rv-status-row"><StatusIcon alert /><CardTitle id="parado-titulo">O trabalho parou no meio</CardTitle></div>
            <p className="rv-muted">Pode ter sido o computador desligando ou a internet caindo. O que já foi feito está salvo.</p>
          </> : <div role="status" className="rv-stack rv-stack--xs">
            <p className="ui-label rv-muted">Pausado na etapa {stage + 1} de 4</p>
            <CardTitle id="parado-titulo" main>O trabalho está pausado</CardTitle>
            <p className="rv-muted">Está tudo salvo. É só continuar quando quiser.</p>
          </div>}
          <Steps steps={steps(book.progress, false)} />
          <Button variant="primary" size="lg" block onClick={onContinue} disabled={busy || disabled}>{failed ? "Continuar de onde parou" : "Continuar"}</Button>
          {disabled && <p className="rv-small rv-muted">Disponível quando o outro livro terminar ou for pausado.</p>}
        </Card>}
        side={<>
          <FilesCard />
          <Button block onClick={() => go("conferir")}>Ver o texto e as correções</Button>
        </>}
      />
    </>
  )
}

/** precisa-de-atencao: some chunks could not be finished. */
export function AttentionScreen({ book, busy, onContinue, disabled, onOpenChunk }: StoppedProps & { onOpenChunk: (chunkId: string) => void }) {
  const problems = book.job?.problems ?? []
  const count = problems.length
  return (
    <>
      <PageTitle eyebrow="Livro aberto">{book.name}</PageTitle>
      <Columns
        main={<Card variant="alert" aria-labelledby="atencao-titulo">
          <div role="status" className="rv-status-row"><StatusIcon alert /><CardTitle id="atencao-titulo">{count === 1 ? "1 trecho precisa de atenção" : `${count} trechos precisam de atenção`}</CardTitle></div>
          <p className="rv-muted">O resto do livro está salvo. {count === 1 ? "Tente esse trecho de novo." : "Tente esses trechos de novo."} Se o aviso continuar, abra o trecho para ver o que houve.</p>
          <ul className="rv-summary">
            {problems.map((problem, index) => (
              <li key={`${problem.chunk_id}-${index}`} className="rv-summary__row">
                <span className="rv-stack rv-stack--xs">
                  <span className="rv-small rv-muted">Trecho {problem.index ?? index + 1} · na etapa “{problem.phase.toLowerCase()}”</span>
                  {problem.title && <span className="ui-strong">{problem.title}</span>}
                  <span>{problem.message}</span>
                </span>
                <TextLink onClick={() => onOpenChunk(problem.chunk_id)}>Abrir este trecho</TextLink>
              </li>
            ))}
          </ul>
          <Button variant="primary" size="lg" block onClick={onContinue} disabled={busy || disabled}>{count === 1 ? "Tentar esse trecho de novo" : "Tentar esses trechos de novo"}</Button>
        </Card>}
        side={<Card variant="outline" aria-labelledby="como-titulo">
          <CardTitle id="como-titulo">Como está o livro</CardTitle>
          <Steps steps={steps(book.progress, false)} />
          <p className="rv-muted">Os arquivos Word só ficam prontos quando todos os trechos estiverem completos.</p>
        </Card>}
      />
    </>
  )
}
