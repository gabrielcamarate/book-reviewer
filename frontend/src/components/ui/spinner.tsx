import { cn } from "@/lib/utils"

/** Spinning arc; always with a sentence (design/components/Spinner.md). */
function Spinner({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg className={cn("rv-spinner", className)} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={size > 24 ? 2.4 : 2.6} strokeLinecap="round" aria-hidden="true">
      <path d="M21 12a9 9 0 1 1-6.2-8.6" />
    </svg>
  )
}

/** Whole-screen loading state with what is being opened. */
function Loading({ children }: { children: string }) {
  return <div className="rv-loading" role="status"><Spinner size={48} /><span>{children}</span></div>
}

export { Spinner, Loading }
