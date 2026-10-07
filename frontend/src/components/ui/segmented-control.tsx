import { cn } from "@/lib/utils"

type Option<T extends string> = { value: T; label: string }

type SegmentedControlProps<T extends string> = {
  label: string
  options: Option<T>[]
  value: T
  onChange: (value: T) => void
  variant?: "default" | "sm" | "block" | "stack"
  className?: string
}

/** Two or three options, one pressed; changes what the screen shows (design/components/SegmentedControl.md). */
function SegmentedControl<T extends string>({ label, options, value, onChange, variant = "default", className }: SegmentedControlProps<T>) {
  return (
    <div role="group" aria-label={label} className={cn("rv-segmented", variant !== "default" && `rv-segmented--${variant}`, className)}>
      {options.map(option => (
        <button key={option.value} type="button" className="rv-segmented__item" aria-pressed={option.value === value} onClick={() => onChange(option.value)}>
          {option.label}
        </button>
      ))}
    </div>
  )
}

export { SegmentedControl }
