import { BookOpenIcon } from "lucide-react"

import { SegmentedControl } from "@/components/ui/segmented-control"
import { setTheme, useTheme, type Theme } from "@/lib/theme"

export type Area = "book" | "books" | "options"

type NavProps = { current: Area | null; onNavigate: (area: Area) => void }

function Brand() {
  return <div className="rv-brand"><BookOpenIcon size={28} strokeWidth={1.8} aria-hidden="true" /><span>Revisor</span></div>
}

/** Desktop header: brand, the two fixed destinations and the theme (design/components/AppHeader.md). */
function AppHeader({ current, onNavigate }: NavProps) {
  const theme = useTheme()
  return (
    <header className="rv-header">
      <Brand />
      <nav className="rv-nav" aria-label="Principal">
        <button type="button" className="rv-nav__link" aria-current={current === "books" ? "page" : undefined} onClick={() => onNavigate("books")}>Meus livros</button>
        <button type="button" className="rv-nav__link" aria-current={current === "options" ? "page" : undefined} onClick={() => onNavigate("options")}>Mais opções</button>
        <SegmentedControl<Theme> label="Tema" variant="sm" value={theme} onChange={setTheme} options={[{ value: "dark", label: "Escuro" }, { value: "light", label: "Claro" }]} />
      </nav>
    </header>
  )
}

/** Phone header: the brand only; navigation lives in the TabBar. */
function MobileHeader() {
  return <header className="rv-header rv-header--mobile"><Brand /></header>
}

export { AppHeader, MobileHeader }
