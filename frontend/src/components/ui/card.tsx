import type * as React from "react"

import { cn } from "@/lib/utils"
import { useIsMobile } from "@/lib/viewport"

type CardProps = React.ComponentProps<"section"> & { variant?: "default" | "outline" | "alert" | "current" }

/** Groups one subject of a screen; never nested (design/components/Card.md). */
function Card({ variant = "default", className, ...props }: CardProps) {
  const mobile = useIsMobile()
  return <section className={cn("rv-card", variant !== "default" && `rv-card--${variant}`, mobile && "rv-card--mobile", className)} {...props} />
}

export { Card }
