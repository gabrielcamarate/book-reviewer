import type * as React from "react"

export type SummaryItem = { term: string; value: React.ReactNode; action?: React.ReactNode; note?: React.ReactNode }

/** "What — value" rows with an optional change link (design/components/SummaryRow.md). */
function SummaryRows({ items }: { items: SummaryItem[] }) {
  return (
    <dl className="rv-summary">
      {items.map(item => (
        <div key={item.term} className="rv-summary__row">
          <dt className="rv-summary__term">{item.term}</dt>
          <dd className="rv-summary__value">{item.value}{item.action}</dd>
          {item.note && <dd className="rv-help">{item.note}</dd>}
        </div>
      ))}
    </dl>
  )
}

export { SummaryRows }
