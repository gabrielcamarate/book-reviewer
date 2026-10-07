import { useState } from "react"
import type * as React from "react"
import { ChevronLeftIcon } from "lucide-react"

import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"

type TextLinkProps = Omit<React.ComponentProps<"button">, "onClick"> & {
  variant?: "default" | "quiet" | "back"
  /** Returning a promise shows the spinner until it settles. */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => unknown
}

/** Underlined text action; "back" opens every secondary screen (design/components/Link.md). */
function TextLink({ variant = "default", type = "button", className, children, onClick, disabled, ...props }: TextLinkProps) {
  const [running, setRunning] = useState(false)
  function handle(event: React.MouseEvent<HTMLButtonElement>) {
    const result = onClick?.(event)
    if (result instanceof Promise) { setRunning(true); result.finally(() => setRunning(false)) }
  }
  return (
    <button type={type} className={cn("rv-link", variant === "quiet" && "rv-link--quiet", variant === "back" && "rv-link--back", className)} onClick={handle} disabled={disabled || running} aria-busy={running || undefined} {...props}>
      {variant === "back" && <ChevronLeftIcon size={20} aria-hidden="true" />}
      {children}
      {running && <Spinner />}
    </button>
  )
}

export { TextLink }
