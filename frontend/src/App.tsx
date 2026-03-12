import { startTransition, useEffect, useMemo, useState } from "react"
import type { ReactNode } from "react"
import {
  CheckIcon,
  CopyIcon,
  MessageSquareWarningIcon,
  SparklesIcon,
} from "lucide-react"

import { Button } from "@/components/ui/button"
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
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"

type ReviewStatus = "pending" | "reviewing" | "ready" | "accepted" | "rejected"
type BusyAction = "loading" | "review" | "accept" | "reject" | null

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
  rejection_reason?: string
  spanish_available?: boolean
  spanish_text?: string
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

type CopyTarget = "review" | "spanish" | null

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
) {
  const wrapper = document.createElement("div")
  wrapper.innerHTML = htmlText
  const usedChangeIndexes = new Set<number>()

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
      const fragment = element.textContent?.trim() ?? ""
      const change = changes.find((candidate, index) => {
        if (usedChangeIndexes.has(index)) {
          return false
        }

        const candidateFragment =
          tone === "before" ? candidate.original_fragment : candidate.suggested_fragment
        return Boolean(candidateFragment) && candidateFragment === fragment
      }) ?? null

      const content = (
        <mark key={keyPrefix} className={highlightClass}>
          {children}
        </mark>
      )

      if (!change) {
        return content
      }

      const resolvedIndex = changes.indexOf(change)
      if (resolvedIndex >= 0) {
        usedChangeIndexes.add(resolvedIndex)
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
  const paragraphs = htmlText
    .split(/\n{2,}|\r\n\r\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)

  if (paragraphs.length === 0) {
    return renderDiffHtml(htmlText, tone, changes)
  }

  return paragraphs.map((paragraph, index) => (
    <p
      key={`diff-paragraph-${tone}-${index}`}
      className="text-justify indent-6 leading-8 [&:not(:last-child)]:mb-5"
    >
      {renderDiffHtml(paragraph, tone, changes)}
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
  const [copiedTarget, setCopiedTarget] = useState<CopyTarget>(null)

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
  const spanishText = state?.spanish_text ?? ""
  const spanishAvailable = Boolean(state?.spanish_available)
  const rejectionReason = state?.rejection_reason ?? ""

  const status = useMemo<ReviewStatus>(() => {
    if (rejectionReason && !reviewAvailable) {
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
  }, [busyAction, rejectionReason, reviewAvailable])

  const activeStatusLabel = useMemo(() => {
    if (rejectionReason && !reviewAvailable) {
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
  }, [busyAction, rejectionReason, orientation?.queue_status, reviewAvailable])

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

  async function handleReject() {
    const trimmed = rejectReason.trim()
    if (!trimmed) {
      return
    }

    setBusyAction("reject")
    setErrorMessage("")

    try {
      await requestJson("/api/simple-home/reject", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ reason: trimmed }),
      })
      setRejectOpen(false)
      setRejectReason("")
      await loadSimpleHome()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Falha ao recusar a revisão."
      startTransition(() => {
        setErrorMessage(message)
        setBusyAction(null)
      })
    }
  }

  const originalPaneContent = reviewAvailable
    ? renderDiffParagraphs(originalDiffHtml, "before", changes)
    : originalText

  const reviewContent = reviewAvailable
    ? renderDiffParagraphs(revisedDiffHtml, "after", changes)
    : "Clique em “Revisar este trecho” para gerar a proposta do Codex com base no texto original, no guia de estilo e nas decisões editoriais."

  const spanishContent = spanishAvailable
    ? spanishText
    : reviewAvailable
      ? "Gerando ou aguardando a sugestão em espanhol baseada no trecho revisado em pt-BR."
      : "A sugestão em espanhol aparece aqui logo depois que este trecho for revisado em pt-BR."

  async function handleCopy(target: Exclude<CopyTarget, null>, text: string) {
    if (!text.trim()) {
      return
    }

    try {
      await navigator.clipboard.writeText(text)
      setCopiedTarget(target)
      window.setTimeout(() => {
        setCopiedTarget((current) => (current === target ? null : current))
      }, 1800)
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Falha ao copiar o texto."
      setErrorMessage(message)
    }
  }

  return (
    <main className="min-h-screen overflow-y-auto bg-[radial-gradient(circle_at_top,_rgba(166,122,60,0.16),_transparent_35%),linear-gradient(180deg,_var(--color-background),_var(--color-ink-980))] text-foreground lg:h-[100dvh] lg:overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1680px] flex-col px-4 py-3 sm:px-6 sm:py-4 lg:h-full lg:min-h-0 lg:px-8">
        <Card className="flex min-h-0 flex-1 overflow-hidden border-border/70 bg-card/98 shadow-[0_28px_80px_rgba(4,8,14,0.24)] lg:flex-1">
          <CardHeader className="gap-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-2">
                <CardTitle className="font-serif-display text-2xl font-semibold text-[color:var(--color-paper-50)]">
                  {orientation?.current_chapter_title ?? "Carregando capítulo..."}
                </CardTitle>
                <CardDescription className="text-sm leading-6 text-[color:var(--color-paper-300)]">
                  {hasActionableChunk && orientation
                    ? `Trecho ${orientation.current_chunk_position} de ${orientation.chapter_chunk_count} neste capítulo. A sugestão em espanhol é baseada no pt-BR revisado deste mesmo trecho.`
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
                <div className="hidden h-full min-h-0 lg:grid lg:grid-cols-3 lg:grid-rows-[minmax(0,1fr)_minmax(250px,0.72fr)] lg:gap-3">
                  <DesktopPanel>
                    <ReviewPane
                      eyebrow="Trecho Original"
                      title="Trecho original"
                      content={originalPaneContent || "Carregando texto original..."}
                    />
                  </DesktopPanel>

                  <DesktopPanel>
                    <ReviewPane
                      eyebrow="Trecho Revisado"
                      title={
                        reviewAvailable
                          ? "Sugestão de revisão"
                          : "Aguardando geração da revisão"
                      }
                      content={reviewContent}
                      muted={!reviewAvailable}
                      action={
                        <CopyActionButton
                          label={copiedTarget === "review" ? "Copiado" : "Copiar"}
                          disabled={!reviewAvailable}
                          onClick={() => void handleCopy("review", revisedText)}
                        />
                      }
                    />
                  </DesktopPanel>

                  <DesktopPanel>
                    <ReviewPane
                      eyebrow="Trecho Espanhol"
                      title={
                        spanishAvailable
                          ? "Sugestão em espanhol"
                          : "Aguardando tradução"
                      }
                      content={spanishContent}
                      muted={!spanishAvailable}
                      action={
                        <CopyActionButton
                          label={copiedTarget === "spanish" ? "Copiado" : "Copiar"}
                          disabled={!spanishAvailable}
                          onClick={() => void handleCopy("spanish", spanishText)}
                        />
                      }
                    />
                  </DesktopPanel>

                  <DesktopPanel className="col-span-3">
                    <ChangesPane
                      status={status}
                      changes={changes}
                      rejectionReason={rejectionReason}
                    />
                  </DesktopPanel>
                </div>

                <div className="grid gap-3 lg:hidden">
                  <DesktopPanel>
                    <ReviewPane
                      eyebrow="Trecho Original"
                      title="Trecho original"
                      content={originalPaneContent || "Carregando texto original..."}
                    />
                  </DesktopPanel>
                  <DesktopPanel>
                    <ReviewPane
                      eyebrow="Trecho Revisado"
                      title={
                        reviewAvailable
                          ? "Sugestão de revisão"
                          : "Aguardando geração da revisão"
                      }
                      content={reviewContent}
                      muted={!reviewAvailable}
                      action={
                        <CopyActionButton
                          label={copiedTarget === "review" ? "Copiado" : "Copiar"}
                          disabled={!reviewAvailable}
                          onClick={() => void handleCopy("review", revisedText)}
                        />
                      }
                    />
                  </DesktopPanel>
                  <DesktopPanel>
                    <ReviewPane
                      eyebrow="Trecho Espanhol"
                      title={
                        spanishAvailable
                          ? "Sugestão em espanhol"
                          : "Aguardando tradução"
                      }
                      content={spanishContent}
                      muted={!spanishAvailable}
                      action={
                        <CopyActionButton
                          label={copiedTarget === "spanish" ? "Copiado" : "Copiar"}
                          disabled={!spanishAvailable}
                          onClick={() => void handleCopy("spanish", spanishText)}
                        />
                      }
                    />
                  </DesktopPanel>
                  <DesktopPanel>
                    <ChangesPane
                      status={status}
                      changes={changes}
                      rejectionReason={rejectionReason}
                    />
                  </DesktopPanel>
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
              <div className="flex w-full flex-wrap gap-3 sm:w-auto">
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
              </div>
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
                <Button
                  size="lg"
                  className="h-11 sm:w-auto"
                  onClick={handleReview}
                  disabled={busyAction === "loading" || busyAction === "review" || !hasActionableChunk}
                >
                  {busyAction === "review" ? (
                    <>
                      <Spinner className="size-4" data-icon="inline-start" />
                      Gerando nova revisão...
                    </>
                  ) : (
                    <>
                      <SparklesIcon data-icon="inline-start" />
                      Gerar nova revisão
                    </>
                  )}
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
            <Button onClick={() => void handleReject()} disabled={!rejectReason.trim() || busyAction === "reject"}>
              {busyAction === "reject" ? "Recusando..." : "Confirmar recusa"}
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
  action,
}: {
  eyebrow: string
  title: string
  content: ReactNode
  muted?: boolean
  action?: ReactNode
}) {
  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="px-4 pb-3 pt-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[color:var(--color-accent-300)]">
          {eyebrow}
        </p>
        <div className="mt-2 flex items-start justify-between gap-3">
          <h2 className="font-serif-display text-xl font-semibold text-[color:var(--color-paper-50)]">
            {title}
          </h2>
          {action}
        </div>
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
  rejectionReason,
}: {
  status: ReviewStatus
  changes: SimpleHomeChange[]
  rejectionReason: string
}) {
  const hasChanges = changes.length > 0 && (status === "ready" || status === "accepted")

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="px-4 pb-3 pt-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[color:var(--color-accent-300)]">
          Alterações
        </p>
        <h2 className="mt-2 font-serif-display text-xl font-semibold text-[color:var(--color-paper-50)]">
          Alterações da revisão em pt-BR
        </h2>
      </div>
      <Separator className="bg-border/60" />
      <div className="relative min-h-0 flex-1">
        <ScrollArea className="absolute inset-0">
          <div className="px-4 py-4 pb-10">
            {!hasChanges && !rejectionReason && (
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
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {changes.map((change) => (
                  <article
                    key={`${change.index}-${change.change_type}`}
                    className="flex h-full min-h-[220px] flex-col rounded-2xl border border-border/70 bg-background/40 p-4"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--color-accent-300)]">
                      {change.change_type}
                    </p>
                    <div className="mt-3 flex-1 space-y-2 text-sm leading-6">
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

            {rejectionReason && (
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
                    {rejectionReason || "Sem motivo registrado."}
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

function DesktopPanel({
  children,
  className = "",
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div
      className={`overflow-hidden rounded-[24px] border border-border/70 bg-[color:var(--color-panel)]/55 ${className}`.trim()}
    >
      {children}
    </div>
  )
}

function CopyActionButton({
  label,
  disabled,
  onClick,
}: {
  label: string
  disabled: boolean
  onClick: () => void
}) {
  return (
    <Button
      type="button"
      size="sm"
      variant="ghost"
      className="h-9 shrink-0 rounded-full border border-border/70 bg-background/45 px-3 text-[color:var(--color-paper-200)] hover:bg-background/65"
      disabled={disabled}
      onClick={onClick}
    >
      <CopyIcon data-icon="inline-start" className="size-4" />
      {label}
    </Button>
  )
}

export default App
