import { startTransition, useEffect, useMemo, useState } from "react"
import type { ReactNode } from "react"
import {
  BookOpenTextIcon,
  CheckIcon,
  FilePenLineIcon,
  LanguagesIcon,
  MessageSquareWarningIcon,
  SparklesIcon,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { ButtonGroup } from "@/components/ui/button-group"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"

type ReviewStatus = "pending" | "reviewing" | "ready" | "accepted" | "rejected"
type BusyAction = "loading" | "review" | "accept" | null

type SimpleHomeChange = {
  index: number
  change_type: string
  reason: string
  confidence: string
  original_text: string
  suggested_text: string
  original_html: string
  suggested_html: string
  original_fragment: string
  suggested_fragment: string
}

type SimpleHomeState = {
  has_actionable_chunk: boolean
  chunk?: {
    id: string
  }
  orientation?: {
    current_chapter_title: string
    remaining_chapter_count: number
    current_chunk_position: number
    chapter_chunk_count: number
    remaining_actionable_chunk_count: number
    queue_status: string
  }
  original_text?: string
  revised_text?: string
  original_diff_html?: string
  revised_diff_html?: string
  review_available?: boolean
  changes?: SimpleHomeChange[]
  summary?: {
    pending_copyedit_count?: number
    awaiting_approval_count?: number
    ready_for_style_count?: number
    awaiting_style_approval_count?: number
    ready_for_translation_count?: number
    translated_count?: number
  }
}

function formatConfidence(value: string) {
  const normalized = Number.parseFloat(value)
  if (Number.isNaN(normalized)) {
    return value
  }
  return `${Math.round(normalized * 100)}%`
}

function getUnicodeLabel(character: string) {
  return `U+${character.codePointAt(0)?.toString(16).toUpperCase().padStart(4, "0") ?? "0000"}`
}

function buildCharacterHints(change: SimpleHomeChange) {
  const originalChars = Array.from(change.original_fragment || "")
  const suggestedChars = Array.from(change.suggested_fragment || "")

  if (
    originalChars.length !== suggestedChars.length ||
    originalChars.length === 0 ||
    originalChars.length > 3
  ) {
    return []
  }

  return originalChars
    .map((character, index) => {
      const replacement = suggestedChars[index]
      if (character === replacement) {
        return null
      }
      return {
        before: character,
        beforeCode: getUnicodeLabel(character),
        after: replacement,
        afterCode: getUnicodeLabel(replacement),
      }
    })
    .filter(Boolean) as Array<{
    before: string
    beforeCode: string
    after: string
    afterCode: string
  }>
}

function renderHoverDetails(change: SimpleHomeChange) {
  const characterHints = buildCharacterHints(change)

  return (
    <div className="grid gap-3">
      <div className="grid gap-2">
        <div className="grid gap-1">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-red-200/90">
            Antes
          </p>
          <div className="rounded-lg border border-red-400/25 bg-red-500/10 px-3 py-2 text-sm leading-6 text-red-50">
            {change.original_fragment || change.original_text}
          </div>
        </div>
        <div className="grid gap-1">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-emerald-200/90">
            Depois
          </p>
          <div className="rounded-lg border border-emerald-400/25 bg-emerald-500/10 px-3 py-2 text-sm leading-6 text-emerald-50">
            {change.suggested_fragment || change.suggested_text}
          </div>
        </div>
      </div>

      {characterHints.length > 0 && (
        <div className="grid gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[color:var(--color-accent-300)]">
            Caractere alterado
          </p>
          <div className="grid gap-2">
            {characterHints.map((hint) => (
              <div
                key={`${hint.beforeCode}-${hint.afterCode}`}
                className="flex items-center justify-between gap-3 rounded-lg border border-border/70 bg-background/70 px-3 py-2"
              >
                <div className="flex min-w-0 items-center gap-2">
                  <span className="rounded bg-red-500/15 px-2 py-1 font-mono text-sm text-red-100">
                    {hint.before}
                  </span>
                  <span className="truncate font-mono text-xs text-muted-foreground">
                    {hint.beforeCode}
                  </span>
                </div>
                <span className="text-muted-foreground">→</span>
                <div className="flex min-w-0 items-center gap-2">
                  <span className="rounded bg-emerald-500/15 px-2 py-1 font-mono text-sm text-emerald-100">
                    {hint.after}
                  </span>
                  <span className="truncate font-mono text-xs text-muted-foreground">
                    {hint.afterCode}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function renderDiffHtml(
  htmlText: string,
  tone: "before" | "after",
  changes: SimpleHomeChange[] = [],
  counter: { value: number } = { value: 0 },
) {
  const wrapper = document.createElement("div")
  wrapper.innerHTML = htmlText

  const highlightClass =
    tone === "before"
      ? "rounded-md bg-red-500/18 px-1 py-0.5 text-red-100 ring-1 ring-red-400/30"
      : "rounded-md bg-emerald-500/18 px-1 py-0.5 text-emerald-100 ring-1 ring-emerald-400/30"
  const walk = (node: ChildNode, keyPrefix: string): ReactNode => {
    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent
    }

    if (node.nodeType !== Node.ELEMENT_NODE) {
      return null
    }

    const element = node as HTMLElement
    const children = Array.from(element.childNodes).map((child, index) =>
      walk(child, `${keyPrefix}-${index}`),
    )

    if (element.classList.contains("diff-added") || element.classList.contains("diff-removed")) {
      const change = changes[counter.value] ?? null
      counter.value += 1

      const content = (
        <mark key={keyPrefix} className={highlightClass}>
          {children}
        </mark>
      )

      if (!change) {
        return content
      }

      return (
        <HoverCard key={keyPrefix} openDelay={120} closeDelay={80}>
          <HoverCardTrigger asChild>{content}</HoverCardTrigger>
          <HoverCardContent
            align="start"
            side="top"
            className="w-[min(26rem,calc(100vw-2rem))] border border-border/70 bg-card/98 p-3 shadow-[0_20px_50px_rgba(4,8,14,0.36)]"
          >
            {renderHoverDetails(change)}
          </HoverCardContent>
        </HoverCard>
      )
    }

    return (
      <span key={keyPrefix}>
        {children}
      </span>
    )
  }

  return Array.from(wrapper.childNodes).map((node, index) => walk(node, `diff-${index}`))
}

function renderDiffParagraphs(
  htmlText: string,
  tone: "before" | "after",
  changes: SimpleHomeChange[] = [],
) {
  const counter = { value: 0 }
  const paragraphs = htmlText
    .split(/\n{2,}|\r\n\r\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)

  if (paragraphs.length === 0) {
    return renderDiffHtml(htmlText, tone, changes, counter)
  }

  return paragraphs.map((paragraph, index) => (
    <p
      key={`diff-paragraph-${tone}-${index}`}
      className="text-justify indent-6 leading-8 [&:not(:last-child)]:mb-5"
    >
      {renderDiffHtml(paragraph, tone, changes, counter)}
    </p>
  ))
}

function renderParagraphs(content: ReactNode) {
  if (typeof content !== "string") {
    return content
  }

  const paragraphs = content
    .split(/\n{2,}|\r\n\r\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)

  if (paragraphs.length === 0) {
    return content
  }

  return paragraphs.map((paragraph, index) => (
    <p
      key={`paragraph-${index}`}
      className="text-justify indent-6 leading-8 [&:not(:last-child)]:mb-5"
    >
      {paragraph}
    </p>
  ))
}

async function requestJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    headers: {
      "Content-Type": "application/json",
    },
    ...init,
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || "Falha ao carregar dados.")
  }

  return (await response.json()) as T
}

function App() {
  const [state, setState] = useState<SimpleHomeState | null>(null)
  const [busyAction, setBusyAction] = useState<BusyAction>("loading")
  const [errorMessage, setErrorMessage] = useState("")
  const [rejectOpen, setRejectOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState("")
  const [lastRejectedReason, setLastRejectedReason] = useState("")

  async function loadSimpleHome() {
    setBusyAction("loading")
    setErrorMessage("")

    try {
      const payload = await requestJson<SimpleHomeState>("/api/simple-home")
      startTransition(() => {
        setState(payload)
        setBusyAction(null)
      })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Falha ao carregar a revisão."
      startTransition(() => {
        setErrorMessage(message)
        setBusyAction(null)
      })
    }
  }

  useEffect(() => {
    void loadSimpleHome()
  }, [])

  const reviewAvailable = Boolean(state?.review_available)
  const hasActionableChunk = Boolean(state?.has_actionable_chunk)
  const changes = state?.changes ?? []
  const orientation = state?.orientation
  const originalText = state?.original_text ?? ""
  const revisedText = state?.revised_text ?? originalText
  const originalDiffHtml = state?.original_diff_html ?? originalText
  const revisedDiffHtml = state?.revised_diff_html ?? revisedText

  const status = useMemo<ReviewStatus>(() => {
    if (lastRejectedReason) {
      return "rejected"
    }
    if (busyAction === "review") {
      return "reviewing"
    }
    if (busyAction === "accept") {
      return "accepted"
    }
    if (reviewAvailable) {
      return "ready"
    }
    return "pending"
  }, [busyAction, lastRejectedReason, reviewAvailable])

  const activeStatusLabel = useMemo(() => {
    if (lastRejectedReason) {
      return "Revisão recusada"
    }
    if (busyAction === "review") {
      return "Revisando trecho"
    }
    if (busyAction === "accept") {
      return "Consolidando revisão"
    }

    switch (orientation?.queue_status) {
      case "awaiting_approval":
        return "Aguardando decisão"
      case "pending_copyedit":
        return "Aguardando revisão"
      default:
        return reviewAvailable ? "Aguardando decisão" : "Aguardando revisão"
    }
  }, [busyAction, lastRejectedReason, orientation?.queue_status, reviewAvailable])

  const progressValue = useMemo(() => {
    const summary = state?.summary
    if (!summary) {
      return reviewAvailable ? 22 : 14
    }

    const total =
      (summary.pending_copyedit_count ?? 0) +
      (summary.awaiting_approval_count ?? 0) +
      (summary.ready_for_style_count ?? 0) +
      (summary.awaiting_style_approval_count ?? 0) +
      (summary.ready_for_translation_count ?? 0) +
      (summary.translated_count ?? 0)

    if (total <= 0) {
      return reviewAvailable ? 22 : 14
    }

    const completed = (summary.ready_for_style_count ?? 0) + (summary.awaiting_style_approval_count ?? 0) + (summary.ready_for_translation_count ?? 0) + (summary.translated_count ?? 0)
    return Math.max(6, Math.min(100, Math.round((completed / total) * 100)))
  }, [reviewAvailable, state?.summary])

  async function handleReview() {
    setBusyAction("review")
    setErrorMessage("")
    setLastRejectedReason("")

    try {
      await requestJson("/api/simple-home/review", { method: "POST" })
      await loadSimpleHome()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Falha ao revisar o trecho."
      startTransition(() => {
        setErrorMessage(message)
        setBusyAction(null)
      })
    }
  }

  async function handleAccept() {
    setBusyAction("accept")
    setErrorMessage("")
    setLastRejectedReason("")

    try {
      await requestJson("/api/simple-home/accept", { method: "POST" })
      await loadSimpleHome()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Falha ao aceitar a revisão."
      startTransition(() => {
        setErrorMessage(message)
        setBusyAction(null)
      })
    }
  }

  function handleReject() {
    const trimmed = rejectReason.trim()
    setLastRejectedReason(trimmed)
    setRejectOpen(false)
    setRejectReason("")
    setBusyAction(null)
  }

  const originalPaneContent = reviewAvailable
    ? renderDiffParagraphs(originalDiffHtml, "before", changes)
    : originalText

  const reviewContent = reviewAvailable
    ? renderDiffParagraphs(revisedDiffHtml, "after", changes)
    : "Clique em “Revisar este trecho” para gerar a proposta do Codex com base no texto original, no guia de estilo e nas decisões editoriais."

  return (
    <main className="min-h-screen overflow-y-auto bg-[radial-gradient(circle_at_top,_rgba(166,122,60,0.16),_transparent_35%),linear-gradient(180deg,_var(--color-background),_var(--color-ink-980))] text-foreground lg:h-[100dvh] lg:overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1680px] flex-col px-4 py-3 sm:px-6 sm:py-4 lg:h-full lg:min-h-0 lg:px-8">
        <Card className="border-border/70 bg-card/95 shadow-[0_30px_90px_rgba(4,8,14,0.34)]">
          <CardHeader className="gap-4">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[color:var(--color-accent-300)]">
                  Modo simples
                </p>
                <div className="space-y-1">
                  <CardTitle className="font-serif-display text-3xl font-semibold tracking-[0.01em] text-[color:var(--color-paper-50)] sm:text-4xl">
                    eXilados da Terra
                  </CardTitle>
                  <CardDescription className="max-w-3xl text-sm leading-6 text-[color:var(--color-paper-300)]">
                    Um trecho por vez. Ler, comparar e decidir sem excesso de
                    informação.
                  </CardDescription>
                </div>
              </div>

              <nav
                aria-label="Navegação principal"
                className="flex flex-wrap items-center gap-2"
              >
                <Button variant="default" className="min-w-36 justify-center">
                  <BookOpenTextIcon data-icon="inline-start" />
                  Revisar PT-BR
                </Button>
                <Button
                  variant="outline"
                  className="min-w-36 justify-center border-border/70 bg-transparent"
                >
                  <LanguagesIcon data-icon="inline-start" />
                  Revisar Espanhol
                </Button>
                <Button
                  variant="ghost"
                  className="min-w-40 justify-center text-muted-foreground"
                >
                  <FilePenLineIcon data-icon="inline-start" />
                  Revisão Avançada
                </Button>
              </nav>
            </div>
          </CardHeader>
        </Card>

        <Card className="mt-4 flex min-h-0 flex-1 overflow-hidden border-border/70 bg-card/98 shadow-[0_28px_80px_rgba(4,8,14,0.24)] lg:flex-1">
          <CardHeader className="gap-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-2">
                <CardTitle className="font-serif-display text-2xl font-semibold text-[color:var(--color-paper-50)]">
                  {orientation?.current_chapter_title ?? "Carregando capítulo..."}
                </CardTitle>
                <CardDescription className="text-sm leading-6 text-[color:var(--color-paper-300)]">
                  {hasActionableChunk && orientation
                    ? `Trecho ${orientation.current_chunk_position} de ${orientation.chapter_chunk_count} neste capítulo. A revisão em espanhol só aparece depois da aprovação em português.`
                    : "Quando houver um trecho disponível, ele aparecerá aqui automaticamente."}
                </CardDescription>
              </div>

              <div className="grid gap-3 text-sm text-[color:var(--color-paper-200)] sm:grid-cols-2 xl:grid-cols-4 xl:min-w-[760px]">
                <StatusPill
                  label="Capítulos faltantes"
                  value={String(orientation?.remaining_chapter_count ?? "—")}
                />
                <StatusPill
                  label="Trechos restantes"
                  value={String(orientation?.remaining_actionable_chunk_count ?? "—")}
                />
                <StatusPill label="Status atual" value={activeStatusLabel} />
                <StatusPill
                  label="Próximo passo"
                  value={reviewAvailable ? "Decidir" : "Revisar"}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.22em] text-muted-foreground">
                <span>Progresso geral do manuscrito</span>
                <span>{progressValue}%</span>
              </div>
              <Progress value={progressValue} className="h-2 bg-[color:var(--color-muted)]" />
            </div>

            {errorMessage && (
              <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                {errorMessage}
              </div>
            )}
          </CardHeader>

          <Separator className="bg-border/70" />

          <CardContent className="flex min-h-0 flex-1 flex-col overflow-hidden py-4">
            {!hasActionableChunk && busyAction !== "loading" ? (
              <Empty className="mx-auto my-auto max-w-xl border-border/70 bg-background/35">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <CheckIcon />
                  </EmptyMedia>
                  <EmptyTitle>Nenhum trecho pendente agora</EmptyTitle>
                  <EmptyDescription>
                    Quando a fila editorial voltar a ter um trecho acionável, ele vai
                    aparecer aqui automaticamente.
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : (
              <div className="min-h-0 flex-1 overflow-hidden">
                <div className="hidden h-full min-h-0 lg:block">
                  <ResizablePanelGroup
                    orientation="horizontal"
                    className="h-full min-h-0 rounded-[24px] border border-border/70 bg-[color:var(--color-panel)]/55"
                  >
                    <ResizablePanel
                      defaultSize={39}
                      minSize={25}
                      className="min-h-0 overflow-hidden"
                    >
                      <ReviewPane
                        eyebrow="Original"
                        title="Trecho do manuscrito"
                        content={originalPaneContent || "Carregando texto original..."}
                      />
                    </ResizablePanel>

                    <ResizableHandle withHandle className="bg-border/70" />

                    <ResizablePanel
                      defaultSize={39}
                      minSize={25}
                      className="min-h-0 overflow-hidden"
                    >
                      <ReviewPane
                        eyebrow="Revisado"
                        title={
                          reviewAvailable
                            ? "Sugestão de revisão"
                            : "Aguardando geração da revisão"
                        }
                        content={reviewContent}
                        muted={!reviewAvailable}
                      />
                    </ResizablePanel>

                    <ResizableHandle withHandle className="bg-border/70" />

                    <ResizablePanel
                      defaultSize={22}
                      minSize={18}
                      className="min-h-0 overflow-hidden"
                    >
                      <ChangesPane
                        status={status}
                        changes={changes}
                        lastRejectedReason={lastRejectedReason}
                      />
                    </ResizablePanel>
                  </ResizablePanelGroup>
                </div>

                <div className="grid gap-3 lg:hidden">
                  <MobilePanel>
                    <ReviewPane
                      eyebrow="Original"
                      title="Trecho do manuscrito"
                      content={originalPaneContent || "Carregando texto original..."}
                    />
                  </MobilePanel>
                  <MobilePanel>
                    <ReviewPane
                      eyebrow="Revisado"
                      title={
                        reviewAvailable
                          ? "Sugestão de revisão"
                          : "Aguardando geração da revisão"
                      }
                      content={reviewContent}
                      muted={!reviewAvailable}
                    />
                  </MobilePanel>
                  <MobilePanel>
                    <ChangesPane
                      status={status}
                      changes={changes}
                      lastRejectedReason={lastRejectedReason}
                    />
                  </MobilePanel>
                </div>
              </div>
            )}
          </CardContent>

          <Separator className="bg-border/70" />

          <div className="flex flex-col gap-3 px-4 py-4 sm:px-6">
            {(status === "pending" || status === "reviewing") && (
              <Button
                size="lg"
                className="h-11 w-full sm:w-auto"
                onClick={handleReview}
                disabled={busyAction === "loading" || busyAction === "review" || !hasActionableChunk}
              >
                {busyAction === "review" ? (
                  <>
                    <Spinner className="size-4" data-icon="inline-start" />
                    Revisando este trecho...
                  </>
                ) : (
                  <>
                    <SparklesIcon data-icon="inline-start" />
                    Revisar este trecho
                  </>
                )}
              </Button>
            )}

            {status === "ready" && (
              <ButtonGroup className="w-full flex-wrap gap-3 sm:w-auto">
                <Button
                  size="lg"
                  className="h-11 min-w-40"
                  onClick={handleAccept}
                  disabled={busyAction === "accept"}
                >
                  {busyAction === "accept" ? (
                    <>
                      <Spinner className="size-4" data-icon="inline-start" />
                      Aceitando...
                    </>
                  ) : (
                    <>
                      <CheckIcon data-icon="inline-start" />
                      Aceitar
                    </>
                  )}
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="h-11 min-w-40 border-border/80 bg-transparent"
                  onClick={() => setRejectOpen(true)}
                >
                  <MessageSquareWarningIcon data-icon="inline-start" />
                  Recusar
                </Button>
              </ButtonGroup>
            )}

            {status === "accepted" && (
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-[color:var(--color-paper-200)]">
                  Revisão aceita. O próximo trecho pendente vai aparecer
                  automaticamente depois do recarregamento do estado.
                </p>
                <Button
                  size="lg"
                  variant="outline"
                  className="h-11 border-border/80 bg-transparent"
                  onClick={() => void loadSimpleHome()}
                >
                  Atualizar tela
                </Button>
              </div>
            )}

            {status === "rejected" && (
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-[color:var(--color-paper-200)]">
                  A revisão foi recusada. O próximo passo será gerar uma nova
                  proposta usando o motivo informado.
                </p>
                <Button size="lg" className="h-11 sm:w-auto" onClick={handleReview}>
                  <SparklesIcon data-icon="inline-start" />
                  Gerar nova revisão
                </Button>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent className="border-border/70 bg-card text-foreground">
          <DialogHeader>
            <DialogTitle>Recusar revisão</DialogTitle>
            <DialogDescription>
              Explique em poucas palavras o que não agradou. Esse motivo será usado
              no futuro para gerar uma nova proposta melhor.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-3">
            <section className="grid gap-3">
              <Label htmlFor="reject-reason">Motivo da recusa</Label>
              <div className="rounded-2xl border border-border/70 bg-background/45 p-3">
                <textarea
                  id="reject-reason"
                  value={rejectReason}
                  onChange={(event) => setRejectReason(event.target.value)}
                  placeholder="Ex.: mudou demais a voz do autor"
                  className="min-h-28 w-full resize-none rounded-xl border border-input bg-background/60 px-3 py-3 text-sm leading-6 text-foreground outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                />
                <p className="mt-2 text-xs leading-5 text-muted-foreground">
                  Esse texto será usado como contexto para a próxima tentativa de
                  revisão.
                </p>
              </div>
            </section>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              className="border-border/80 bg-transparent"
              onClick={() => setRejectOpen(false)}
            >
              Cancelar
            </Button>
            <Button onClick={handleReject} disabled={!rejectReason.trim()}>
              Confirmar recusa
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  )
}

function ReviewPane({
  eyebrow,
  title,
  content,
  muted = false,
}: {
  eyebrow: string
  title: string
  content: ReactNode
  muted?: boolean
}) {
  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="px-4 pb-3 pt-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[color:var(--color-accent-300)]">
          {eyebrow}
        </p>
        <h2 className="mt-2 font-serif-display text-xl font-semibold text-[color:var(--color-paper-50)]">
          {title}
        </h2>
      </div>
      <Separator className="bg-border/60" />
      <div className="relative min-h-0 flex-1">
        <ScrollArea className="absolute inset-0">
          <div className="px-4 py-4 pb-10">
            <div
              className={
                muted
                  ? "text-base leading-8 text-muted-foreground"
                  : "text-base leading-8 text-[color:var(--color-paper-100)]"
              }
            >
              {renderParagraphs(content)}
            </div>
          </div>
        </ScrollArea>
      </div>
    </section>
  )
}

function ChangesPane({
  status,
  changes,
  lastRejectedReason,
}: {
  status: ReviewStatus
  changes: SimpleHomeChange[]
  lastRejectedReason: string
}) {
  const hasChanges = changes.length > 0 && (status === "ready" || status === "accepted")

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="px-4 pb-3 pt-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[color:var(--color-accent-300)]">
          Alterações
        </p>
        <h2 className="mt-2 font-serif-display text-xl font-semibold text-[color:var(--color-paper-50)]">
          O que mudou
        </h2>
      </div>
      <Separator className="bg-border/60" />
      <div className="relative min-h-0 flex-1">
        <ScrollArea className="absolute inset-0">
          <div className="px-4 py-4 pb-10">
            {!hasChanges && status !== "rejected" && (
              <Empty className="border-border/70 bg-background/35">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <SparklesIcon />
                  </EmptyMedia>
                  <EmptyTitle>Nenhuma alteração disponível ainda</EmptyTitle>
                  <EmptyDescription>
                    Quando você pedir a revisão, esta coluna vai explicar cada ajuste
                    sugerido e a confiança do modelo.
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            )}

            {hasChanges && (
              <div className="space-y-3">
                {changes.map((change) => (
                  <article
                    key={`${change.index}-${change.change_type}`}
                    className="rounded-2xl border border-border/70 bg-background/40 p-4"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--color-accent-300)]">
                      {change.change_type}
                    </p>
                    <div className="mt-3 space-y-2 text-sm leading-6">
                      <p className="text-muted-foreground">
                        <strong className="text-[color:var(--color-paper-200)]">
                          Antes:
                        </strong>{" "}
                        {renderDiffHtml(change.original_html, "before")}
                      </p>
                      <p className="text-[color:var(--color-paper-100)]">
                        <strong className="text-[color:var(--color-paper-200)]">
                          Depois:
                        </strong>{" "}
                        {renderDiffHtml(change.suggested_html, "after")}
                      </p>
                      <p className="text-muted-foreground">{change.reason}</p>
                    </div>
                    <p className="mt-3 text-xs uppercase tracking-[0.2em] text-[color:var(--color-paper-300)]">
                      Confiança {formatConfidence(change.confidence)}
                    </p>
                  </article>
                ))}
              </div>
            )}

            {status === "rejected" && (
              <Empty className="border-border/70 bg-background/35">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <MessageSquareWarningIcon />
                  </EmptyMedia>
                  <EmptyTitle>Revisão recusada</EmptyTitle>
                  <EmptyDescription>
                    O motivo abaixo será usado para pedir uma nova proposta de revisão.
                  </EmptyDescription>
                </EmptyHeader>
                <EmptyContent className="items-start rounded-2xl border border-border/70 bg-background/45 p-4 text-left">
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--color-accent-300)]">
                    Motivo salvo
                  </p>
                  <p className="text-sm leading-6 text-[color:var(--color-paper-100)]">
                    {lastRejectedReason || "Sem motivo registrado."}
                  </p>
                </EmptyContent>
              </Empty>
            )}
          </div>
        </ScrollArea>
      </div>
    </section>
  )
}

function StatusPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-h-[86px] rounded-2xl border border-border/70 bg-background/40 px-4 py-3">
      <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-3 text-base leading-6 font-semibold text-[color:var(--color-paper-100)]">
        {value}
      </p>
    </div>
  )
}

function MobilePanel({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-border/70 bg-[color:var(--color-panel)]/55">
      {children}
    </div>
  )
}

export default App
