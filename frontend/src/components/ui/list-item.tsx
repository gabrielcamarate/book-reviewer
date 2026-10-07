import type * as React from "react"

type ListItemProps = Omit<React.ComponentProps<"button">, "title"> & {
  index: number
  title: React.ReactNode
  note?: React.ReactNode
  meta: React.ReactNode
  current?: boolean
}

/** One clickable row of a list of chunks (design/components/ListItem.md). */
function ListItem({ index, title, note, meta, current = false, type = "button", ...props }: ListItemProps) {
  return (
    <button type={type} className="rv-item" aria-current={current ? "true" : undefined} {...props}>
      <span className="rv-item__index">{index}</span>
      <span className="rv-item__body"><span className="rv-item__title">{title}</span>{note && <span className="rv-item__note">{note}</span>}</span>
      <span className="rv-item__meta">{meta}</span>
    </button>
  )
}

export { ListItem }
