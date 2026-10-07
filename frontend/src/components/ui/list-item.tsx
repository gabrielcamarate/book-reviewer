import { useState } from "react"
import type * as React from "react"

import { Spinner } from "@/components/ui/spinner"

type ListItemProps = Omit<React.ComponentProps<"button">, "title" | "onClick"> & {
  onClick?: () => unknown
  index: number
  title: React.ReactNode
  note?: React.ReactNode
  meta: React.ReactNode
  current?: boolean
}

/** One clickable row of a list of chunks (design/components/ListItem.md). */
function ListItem({ index, title, note, meta, current = false, type = "button", onClick, ...props }: ListItemProps) {
  const [running, setRunning] = useState(false)
  function handle() {
    const result = onClick?.()
    if (result instanceof Promise) { setRunning(true); result.finally(() => setRunning(false)) }
  }
  return (
    <button type={type} className="rv-item" aria-current={current ? "true" : undefined} aria-busy={running || undefined} onClick={handle} {...props}>
      <span className="rv-item__index">{index}</span>
      <span className="rv-item__body"><span className="rv-item__title">{title}</span>{note && <span className="rv-item__note">{note}</span>}</span>
      <span className="rv-item__meta">{running ? <Spinner /> : meta}</span>
    </button>
  )
}

export { ListItem }
