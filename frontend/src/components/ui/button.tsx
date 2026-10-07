import type * as React from "react"

import { cn } from "@/lib/utils"

type ButtonProps = React.ComponentProps<"button"> & {
  variant?: "primary" | "secondary"
  size?: "default" | "lg"
  block?: boolean
}

/** Action with visible text (design/components/Button.md). One primary per screen. */
function Button({ variant = "secondary", size = "default", block = false, type = "button", className, ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn("rv-btn", variant === "primary" && "rv-btn--primary", size === "lg" && "rv-btn--lg", block && "rv-btn--block", className)}
      {...props}
    />
  )
}

export { Button }
