import type * as React from "react"

import { cn } from "@/lib/utils"
import { useIsMobile } from "@/lib/viewport"

/** "Livro aberto" eyebrow and the page title, one per screen. */
export function PageTitle({ eyebrow, children, action }: { eyebrow?: string; children: React.ReactNode; action?: React.ReactNode }) {
  const mobile = useIsMobile()
  return (
    <div className={cn("rv-page-title", action && "rv-page-title--row")}>
      <div className="rv-page-title">
        {eyebrow && <p className="rv-small rv-muted">{eyebrow}</p>}
        <h1 className={mobile ? "title-page-mobile" : "title-page"}>{children}</h1>
      </div>
      {action}
    </div>
  )
}

/** Main card on the left (3) and support on the right (2); one column on phones. */
export function Columns({ main, side }: { main: React.ReactNode; side?: React.ReactNode }) {
  return (
    <div className="rv-columns">
      <div className="rv-columns__main rv-stack">{main}</div>
      {side && <div className="rv-columns__side rv-stack">{side}</div>}
    </div>
  )
}

export function CardTitle({ id, main = false, children }: { id?: string; main?: boolean; children: React.ReactNode }) {
  const mobile = useIsMobile()
  return <h2 id={id} className={main && !mobile ? "title-card" : "title-section"}>{children}</h2>
}

export function NumberedList({ items }: { items: string[] }) {
  return (
    <ol className="rv-numbered">
      {items.map((item, index) => <li key={item}><span className="rv-step__mark" aria-hidden="true">{index + 1}</span><span>{item}</span></li>)}
    </ol>
  )
}
