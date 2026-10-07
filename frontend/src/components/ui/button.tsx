import { useState } from "react"
import type * as React from "react"

import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"

type ButtonProps = Omit<React.ComponentProps<"button">, "onClick"> & {
  variant?: "primary" | "secondary"
  size?: "default" | "lg"
  block?: boolean
  /** Returning a promise shows the spinner in place of the icon until it settles. */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => unknown
}

/** Action with visible text (design/components/Button.md). One primary per screen. */
function Button({ variant = "secondary", size = "default", block = false, type = "button", className, onClick, disabled, children, ...props }: ButtonProps) {
  const [running, setRunning] = useState(false)
  function handle(event: React.MouseEvent<HTMLButtonElement>) {
    const result = onClick?.(event)
    if (result instanceof Promise) {
      setRunning(true)
      result.finally(() => setRunning(false))
    }
  }
  return (
    <button
      type={type}
      className={cn("rv-btn", variant === "primary" && "rv-btn--primary", size === "lg" && "rv-btn--lg", block && "rv-btn--block", className)}
      onClick={handle}
      disabled={disabled || running}
      aria-busy={running || undefined}
      {...props}
    >
      {running && <Spinner />}
      {children}
    </button>
  )
}

export { Button }
