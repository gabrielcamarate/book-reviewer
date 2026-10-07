import type * as React from "react"
import { ChevronLeftIcon } from "lucide-react"

import { cn } from "@/lib/utils"

type TextLinkProps = React.ComponentProps<"button"> & { variant?: "default" | "quiet" | "back" }

/** Underlined text action; "back" opens every secondary screen (design/components/Link.md). */
function TextLink({ variant = "default", type = "button", className, children, ...props }: TextLinkProps) {
  return (
    <button type={type} className={cn("rv-link", variant === "quiet" && "rv-link--quiet", variant === "back" && "rv-link--back", className)} {...props}>
      {variant === "back" && <ChevronLeftIcon size={20} aria-hidden="true" />}
      {children}
    </button>
  )
}

export { TextLink }
