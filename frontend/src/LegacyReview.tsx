import { CheckIcon, MessageSquareWarningIcon, SparklesIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"

import { useReview } from "@/useReview"
import { renderDiffParagraphs } from "@/components/review-diff"
import { ReviewPane, ChangesPane, StatusPill, DesktopPanel, CopyActionButton } from "@/components/review-panels"

function App() {
  const { state, busyAction, errorMessage, notice, rejectOpen, setRejectOpen, rejectReason,
    setRejectReason, copiedTarget, handleReview, handleAccept, handleReject,
    handleCopy, handleTranslate, handleExport, status, activeStatusLabel, progressValue } = useReview()
  const reviewAvailable = Boolean(state?.review_available)
  const hasActionableChunk = Boolean(state?.has_actionable_chunk)
  const rejectionReason = state?.rejection_reason ?? ""
  const changes = state?.changes ?? []
  const orientation = state?.orientation
  const revisedText = state?.revised_text ?? state?.original_text ?? ""
  const spanishText = state?.spanish_text ?? ""
  const spanishAvailable = Boolean(state?.spanish_available)
  const originalPaneContent = reviewAvailable
    ? renderDiffParagraphs(state?.original_diff_html ?? "", "before", changes)
    : state?.original_text ?? ""
  const reviewContent = reviewAvailable
    ? renderDiffParagraphs(state?.revised_diff_html ?? "", "after", changes)
    : "Clique em Revisar este trecho para gerar a proposta."
  const spanishContent = spanishAvailable ? spanishText : "A prévia em espanhol aparece depois da revisão."
  return (
    <>
    <a href="#revisao" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-card focus:px-4 focus:py-2">Ir para a revisão</a>
    <main id="revisao" className="min-h-screen overflow-y-auto bg-[radial-gradient(circle_at_top,_rgba(166,122,60,0.16),_transparent_35%),linear-gradient(180deg,_var(--color-background),_var(--color-ink-980))] text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-[1680px] flex-col px-4 py-3 sm:px-6 sm:py-4 lg:px-8">
        <Card className="flex min-h-0 flex-1 overflow-hidden border-border/70 bg-card/98 shadow-[0_28px_80px_rgba(4,8,14,0.24)] lg:flex-1">
          <CardHeader className="gap-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-2">
                <h1 className="font-serif-display text-2xl font-semibold text-[color:var(--color-paper-50)]">
                  {orientation?.current_chapter_title ?? "Revisão do livro"}
                </h1>
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
                  value={!hasActionableChunk ? "Traduzir ou exportar" : reviewAvailable ? "Decidir" : "Revisar"}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.22em] text-muted-foreground">
                <span>Progresso da revisão em pt-BR</span>
                <span>{progressValue}%</span>
              </div>
              <Progress aria-label="Progresso da revisão em português" value={progressValue} className="h-2 bg-[color:var(--color-muted)]" />
            </div>

            <div className="flex flex-wrap gap-2" aria-label="Tradução e exportação">
              <Button variant="outline" disabled={busyAction !== null} onClick={() => void handleTranslate()}>Traduzir aprovados</Button>
              <Button variant="outline" disabled={busyAction !== null} onClick={() => void handleExport("pt-BR")}>Exportar PT-BR</Button>
              <Button variant="outline" disabled={busyAction !== null} onClick={() => void handleExport("es")}>Exportar espanhol</Button>
            </div>
            {notice && <p role="status" className="text-sm text-muted-foreground">{notice}</p>}
            {errorMessage && (
              <div role="alert" className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
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
                    <CheckIcon aria-hidden="true" />
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
                <div className="grid min-h-0 gap-3 lg:grid-cols-3 lg:min-h-[520px] lg:grid-rows-[minmax(280px,1fr)_minmax(200px,0.72fr)] lg:gap-3">
                  <DesktopPanel className="h-[320px] lg:h-auto">
                    <ReviewPane
                      eyebrow="Trecho Original"
                      title="Trecho original"
                      content={originalPaneContent || "Carregando texto original…"}
                    />
                  </DesktopPanel>

                  <DesktopPanel className="h-[320px] lg:h-auto">
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

                  <DesktopPanel className="h-[320px] lg:h-auto">
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

                  <DesktopPanel className="h-[400px] lg:h-auto lg:col-span-3">
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
                disabled={busyAction !== null || !hasActionableChunk}
              >
                {busyAction === "review" ? (
                  <>
                    <Spinner className="size-4" data-icon="inline-start" />
                    Revisando este trecho…
                  </>
                ) : (
                  <>
                    <SparklesIcon aria-hidden="true" data-icon="inline-start" />
                    Revisar este trecho
                  </>
                )}
              </Button>
            )}

            {(status === "ready" || status === "accepting") && (
              <div className="flex w-full flex-wrap gap-3 sm:w-auto">
                <Button
                  size="lg"
                  className="h-11 min-w-40"
                  onClick={handleAccept}
                  disabled={busyAction !== null}
                >
                  {busyAction === "accept" ? (
                    <>
                      <Spinner className="size-4" data-icon="inline-start" />
                      Aceitando…
                    </>
                  ) : (
                    <>
                      <CheckIcon aria-hidden="true" data-icon="inline-start" />
                      Aceitar
                    </>
                  )}
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="h-11 min-w-40 border-border/80 bg-transparent"
                  onClick={() => setRejectOpen(true)}
                  disabled={busyAction !== null}
                >
                  <MessageSquareWarningIcon aria-hidden="true" data-icon="inline-start" />
                  Recusar
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
                  disabled={busyAction !== null || !hasActionableChunk}
                >
                  {busyAction === "review" ? (
                    <>
                      <Spinner className="size-4" data-icon="inline-start" />
                      Gerando nova revisão…
                    </>
                  ) : (
                    <>
                      <SparklesIcon aria-hidden="true" data-icon="inline-start" />
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
              na próxima tentativa de revisão.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-3">
            <section className="grid gap-3">
              <Label htmlFor="reject-reason">Motivo da recusa</Label>
              <div className="rounded-2xl border border-border/70 bg-background/45 p-3">
                <textarea
                  id="reject-reason"
                  name="reject-reason"
                  autoComplete="off"
                  value={rejectReason}
                  onChange={(event) => setRejectReason(event.target.value)}
                  placeholder="Ex.: mudou demais a voz do autor…"
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
              {busyAction === "reject" ? "Recusando…" : "Confirmar recusa"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
    </>
  )
}


export default App
