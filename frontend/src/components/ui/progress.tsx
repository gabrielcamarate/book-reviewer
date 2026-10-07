import { cn } from "@/lib/utils"

type ProgressBarProps = { value: number; label: string; neutral?: boolean; className?: string }

/** 10px bar; the same value is always written beside it (design/components/ProgressBar.md). */
function ProgressBar({ value, label, neutral = false, className }: ProgressBarProps) {
  const percent = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className={cn("rv-progress", neutral && "rv-progress--neutral", className)} role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}>
      <div className="rv-progress__bar" style={{ width: `${percent}%` }} />
    </div>
  )
}

export { ProgressBar }
