import type * as React from "react"
import { CheckIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { ProgressBar } from "@/components/ui/progress"
import { Spinner } from "@/components/ui/spinner"

export type Step = { title: string; percent: number; state: "done" | "current" | "waiting"; detail?: React.ReactNode; action?: React.ReactNode; hideStatus?: boolean; working?: boolean }

/** The book's stages and where each one is (design/components/Steps.md). */
function Steps({ steps }: { steps: Step[] }) {
  return (
    <ol className="rv-steps">
      {steps.map((step, index) => (
        <li key={step.title} className={cn("rv-step", step.state === "done" && "rv-step--done", step.state === "current" && "rv-step--current")}>
          <span className="rv-step__mark" aria-hidden="true">{step.state === "done" ? <CheckIcon size={18} strokeWidth={3} /> : step.working ? <Spinner size={18} /> : index + 1}</span>
          <div className="rv-step__body">
            <span className="rv-step__head">
              <span className="rv-step__title">{step.title}</span>
              {step.detail && <span className="rv-small rv-muted">{step.detail}</span>}
            </span>
            {step.state !== "done" && (step.state === "current" || step.percent > 0) && <ProgressBar value={step.percent} label={step.title} neutral={step.state !== "current"} />}
            {step.action}
          </div>
          {!step.hideStatus && <span className="rv-step__status">{step.state === "done" ? "Concluído" : step.state === "current" || step.percent > 0 ? `${Math.round(step.percent)}%` : null}</span>}
        </li>
      ))}
    </ol>
  )
}

export { Steps }
