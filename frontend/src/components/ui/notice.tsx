import type * as React from "react"
import { CheckIcon } from "lucide-react"

import { cn } from "@/lib/utils"

/** Band with the fact, what to do and an optional action (design/components/Notice.md). */
function Notice({ plain = false, children, action }: { plain?: boolean; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className={cn("rv-notice", plain && "rv-notice--plain")} role="status">
      <p className="rv-notice__text">{children}</p>
      {action}
    </div>
  )
}

/** 56px circle that opens the "ready" or "attention" card. */
function StatusIcon({ alert = false }: { alert?: boolean }) {
  return (
    <span className={cn("rv-status-icon", alert && "rv-status-icon--alert")} aria-hidden="true">
      {alert ? <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M12 6v8" /><path d="M12 18h.01" /></svg>
        : <CheckIcon size={30} strokeWidth={3} />}
    </span>
  )
}

export { Notice, StatusIcon }
