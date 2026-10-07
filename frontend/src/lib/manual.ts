import { useSyncExternalStore } from "react"

// "Aprovar as correções à mão" is a per-book preference kept in this browser.
const key = (bookId: string) => `revisor-manual-${bookId}`
const listeners = new Set<() => void>()
const session = new Map<string, boolean>()

function read(bookId: string) {
  if (session.has(bookId)) return session.get(bookId)!
  try { return localStorage.getItem(key(bookId)) === "1" } catch { return false }
}

export function setManual(bookId: string, on: boolean) {
  try {
    if (on) localStorage.setItem(key(bookId), "1")
    else localStorage.removeItem(key(bookId))
    session.delete(bookId)
  } catch {
    session.set(bookId, on)
  }
  listeners.forEach(listener => listener())
}

export function useManual(bookId: string | null) {
  return useSyncExternalStore(listener => { listeners.add(listener); return () => listeners.delete(listener) }, () => (bookId ? read(bookId) : false))
}
