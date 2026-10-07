import type * as React from "react"

import { cn } from "@/lib/utils"

type InputProps = Omit<React.ComponentProps<"input">, "type" | "title">

/** Checkbox with a sentence beside it (design/components/Choice.md). */
function Check({ children, className, ...props }: InputProps & { children: React.ReactNode }) {
  return <label className={cn("rv-check", className)}><input type="checkbox" {...props} />{children}</label>
}

type ChoiceProps = InputProps & {
  type?: "radio" | "checkbox"
  title: React.ReactNode
  text?: React.ReactNode
  row?: boolean
}

/** Option card (radio) or chapter row (checkbox) inside one large label. */
function Choice({ type = "radio", title, text, row = false, checked, className, ...props }: ChoiceProps) {
  return (
    <label className={cn("rv-choice", row && "rv-choice--row", checked && !row && "rv-choice--checked", className)}>
      <input type={type} checked={checked} {...props} />
      {row ? <><span className="rv-choice__title">{title}</span>{text && <span className="rv-choice__text">{text}</span>}</>
        : <span><span className="rv-choice__title">{title}</span>{text && <span className="rv-choice__text">{text}</span>}</span>}
    </label>
  )
}

export { Check, Choice }
