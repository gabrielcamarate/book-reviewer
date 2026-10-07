import type * as React from "react"
import { Dialog as DialogPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"
import { useIsMobile } from "@/lib/viewport"

type ConfirmDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: React.ReactNode
  confirm: React.ReactNode
  cancel: React.ReactNode
}

/** The app's only window: confirm a decision that affects many chunks (design/components/Dialog.md). */
function ConfirmDialog({ open, onOpenChange, title, description, confirm, cancel }: ConfirmDialogProps) {
  const mobile = useIsMobile()
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="rv-scrim rv-scrim--overlay">
          <DialogPrimitive.Content className="rv-dialog">
            <DialogPrimitive.Title className="title-card">{title}</DialogPrimitive.Title>
            <DialogPrimitive.Description className="rv-muted">{description}</DialogPrimitive.Description>
            <div className={cn("rv-actions", mobile && "rv-actions--stack")}>{confirm}{cancel}</div>
          </DialogPrimitive.Content>
        </DialogPrimitive.Overlay>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

export { ConfirmDialog }
