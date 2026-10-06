import type { ReactNode } from "react"
import { CopyIcon, MessageSquareWarningIcon, SparklesIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

import type { SimpleHomeChange, ReviewStatus } from "@/types"
import { renderParagraphs, renderDiffHtml, formatConfidence } from "./review-diff"

export function ReviewPane({
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

export function ChangesPane({
  status,
  changes,
  rejectionReason,
}: {
  status: ReviewStatus
  changes: SimpleHomeChange[]
  rejectionReason: string
}) {
  const hasChanges = changes.length > 0 && (status === "ready" || status === "accepting")

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
                    <SparklesIcon aria-hidden="true" />
                  </EmptyMedia>
                  <EmptyTitle>{status === "ready" ? "Nenhuma correção sugerida" : "Nenhuma alteração disponível ainda"}</EmptyTitle>
                  <EmptyDescription>
                    {status === "ready" ? "O trecho pode ser aprovado sem alterações." : "Quando você pedir a revisão, esta coluna vai explicar cada ajuste sugerido e a confiança do modelo."}
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

            {rejectionReason && status === "rejected" && (
              <Empty className="border-border/70 bg-background/35">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <MessageSquareWarningIcon aria-hidden="true" />
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

export function StatusPill({ label, value }: { label: string; value: string }) {
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

export function DesktopPanel({
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

export function CopyActionButton({
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
      <CopyIcon aria-hidden="true" data-icon="inline-start" className="size-4" />
      {label}
    </Button>
  )
}
