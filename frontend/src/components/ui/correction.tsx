import { useState } from "react"
import type * as React from "react"
import { ChevronDownIcon, ChevronUpIcon } from "lucide-react"

import { useIsMobile } from "@/lib/viewport"

export type CorrectionItem = { before: string; after: string; why: string }

function corrections(count: number) {
  return count === 1 ? "1 correção" : `${count} correções`
}

/** A book paragraph with its corrections attached (design/components/Correction.md). */
function CorrectedParagraph({ text, items }: { text: React.ReactNode; items: CorrectionItem[] }) {
  const mobile = useIsMobile()
  const [open, setOpen] = useState(false)
  // Most paragraphs carry one reason for all of their corrections: show it once, after the list.
  const shared = items.length > 1 && items.every(item => item.why === items[0].why)
  const change = (item: CorrectionItem) => <span className="rv-correction__change"><del>{item.before || "—"}</del><span className="rv-correction__arrow" aria-hidden="true">→</span><ins>{item.after || "—"}</ins></span>
  const list = (
    <div className="rv-para__notes">
      <ul className={shared ? "rv-correction-list" : "rv-para__notes"}>
        {items.map((item, index) => (
          <li key={index} className="rv-correction">
            {change(item)}
            {!shared && <span className="rv-correction__why">{item.why}</span>}
          </li>
        ))}
      </ul>
      {shared && <p className="rv-correction__why">{items[0].why}</p>}
    </div>
  )
  return (
    <div className="rv-para">
      <p className={mobile ? "rv-para__text book-text-mobile" : "rv-para__text book-text"}>{text}</p>
      {!items.length ? (!mobile && <p className="rv-para__notes rv-muted">Sem correções neste parágrafo.</p>)
        : !mobile ? list : (
          <div className="rv-para__notes">
            <button type="button" className="rv-disclosure" aria-expanded={open} onClick={() => setOpen(!open)}>
              {open ? `${corrections(items.length)} neste parágrafo` : items.length === 1 ? "Ver a correção" : `Ver as ${items.length} correções`}
              {open ? <ChevronUpIcon size={20} aria-hidden="true" /> : <ChevronDownIcon size={20} aria-hidden="true" />}
            </button>
            {open && list}
          </div>
        )}
    </div>
  )
}

export { CorrectedParagraph }
