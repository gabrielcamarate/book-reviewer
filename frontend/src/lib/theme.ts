import { useSyncExternalStore } from "react"

export type Theme = "dark" | "light"

// Same key and rule as the inline script in index.html, which applies the theme before the first paint.
const STORAGE_KEY = "revisor-theme"
const listeners = new Set<() => void>()
const systemQuery = () => window.matchMedia("(prefers-color-scheme: light)")

function storedTheme(): Theme | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === "dark" || value === "light" ? value : null
  } catch {
    return null
  }
}

function currentTheme(): Theme {
  return storedTheme() ?? (systemQuery().matches ? "light" : "dark")
}

function applyTheme() {
  const root = document.documentElement
  root.dataset.theme = currentTheme()
  const meta = document.querySelector('meta[name="theme-color"]')
  meta?.setAttribute("content", getComputedStyle(root).getPropertyValue("--background").trim())
  listeners.forEach(listener => listener())
}

export function setTheme(theme: Theme) {
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Without storage the choice lasts until the page closes.
    document.documentElement.dataset.theme = theme
    listeners.forEach(listener => listener())
    return
  }
  applyTheme()
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, () => document.documentElement.dataset.theme === "light" ? "light" : "dark")
}

export function startTheme() {
  applyTheme()
  systemQuery().addEventListener("change", () => { if (!storedTheme()) applyTheme() })
}
