import type { ReactNode } from "react"

import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"

import type { SimpleHomeChange } from "@/types"

export function formatConfidence(value: string) {
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

export function renderDiffHtml(
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
        <mark key={keyPrefix} tabIndex={change ? 0 : undefined} className={`${highlightClass} focus-visible:outline-2 focus-visible:outline-ring`}>
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

export function renderDiffParagraphs(
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

export function renderParagraphs(content: ReactNode) {
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
