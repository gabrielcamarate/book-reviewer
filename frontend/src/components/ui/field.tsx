import type * as React from "react"

import { cn } from "@/lib/utils"

type FieldProps = {
  id: string
  label: React.ReactNode
  optional?: boolean
  help?: React.ReactNode
  error?: React.ReactNode
  children: React.ReactNode
}

/** Visible label, control, then help or error (design/components/Field.md). */
function Field({ id, label, optional = false, help, error, children }: FieldProps) {
  return (
    <div className="rv-field">
      <label className="rv-label" htmlFor={id}>{label}{optional && <span className="rv-label__optional"> (opcional)</span>}</label>
      {children}
      {error ? <p className="rv-error" role="alert" id={`${id}-error`}>{error}</p> : help ? <p className="rv-help" id={`${id}-help`}>{help}</p> : null}
    </div>
  )
}

function Input({ className, ...props }: React.ComponentProps<"input">) {
  return <input className={cn("rv-input", className)} {...props} />
}

function Textarea({ book = false, className, ...props }: React.ComponentProps<"textarea"> & { book?: boolean }) {
  return <textarea className={cn("rv-textarea", book && "rv-textarea--book", className)} {...props} />
}

export { Field, Input, Textarea }
