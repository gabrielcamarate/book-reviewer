import { useSyncExternalStore } from "react"

export type Theme = "dark" | "light"
export type ThemeChoice = Theme | "system"
export type TextSize = "normal" | "large" | "larger"

// Same keys and rules as the inline script in index.html, which applies them before the first paint.
const THEME_KEY = "revisor-theme"
const SIZE_KEY = "revisor-text-size"
const listeners = new Set<() => void>()
const systemQuery = () => window.matchMedia("(prefers-color-scheme: light)")

function read(key: string) {
  try { return localStorage.getItem(key) } catch { return null }
}

function write(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
    return true
  } catch {
    return false
  }
}

let session: { theme?: ThemeChoice; size?: TextSize } = {}

function themeChoice(): ThemeChoice {
  const value = session.theme ?? read(THEME_KEY)
  return value === "dark" || value === "light" ? value : "system"
}

function textSize(): TextSize {
  const value = session.size ?? read(SIZE_KEY)
  return value === "large" || value === "larger" ? value : "normal"
}

function apply() {
  const root = document.documentElement
  const choice = themeChoice()
  root.dataset.theme = choice === "system" ? (systemQuery().matches ? "light" : "dark") : choice
  root.dataset.textSize = textSize()
  const meta = document.querySelector('meta[name="theme-color"]')
  meta?.setAttribute("content", getComputedStyle(root).getPropertyValue("--background").trim())
  listeners.forEach(listener => listener())
}

export function setTheme(choice: ThemeChoice) {
  // Without storage the choice lasts until the page closes.
  session = { ...session, theme: write(THEME_KEY, choice === "system" ? null : choice) ? undefined : choice }
  apply()
}

export function setTextSize(size: TextSize) {
  session = { ...session, size: write(SIZE_KEY, size === "normal" ? null : size) ? undefined : size }
  apply()
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

/** The theme in effect, dark or light. */
export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, () => document.documentElement.dataset.theme === "light" ? "light" : "dark")
}

/** What the person chose, including following the device. */
export function useThemeChoice(): ThemeChoice {
  return useSyncExternalStore(subscribe, themeChoice)
}

export function useTextSize(): TextSize {
  return useSyncExternalStore(subscribe, textSize)
}

export function startTheme() {
  apply()
  systemQuery().addEventListener("change", () => { if (themeChoice() === "system") apply() })
}
