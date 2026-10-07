import { BookOpenIcon, ListIcon, SlidersHorizontalIcon } from "lucide-react"

import type { Area } from "@/components/ui/app-header"

const TABS = [
  { area: "book", label: "Livro", Icon: BookOpenIcon },
  { area: "books", label: "Meus livros", Icon: ListIcon },
  { area: "options", label: "Opções", Icon: SlidersHorizontalIcon },
] as const

/** Phone bottom bar with the three areas spelled out (design/components/TabBar.md). */
function TabBar({ current, onNavigate }: { current: Area | null; onNavigate: (area: Area) => void }) {
  return (
    <nav className="rv-tabbar" aria-label="Principal">
      {TABS.map(({ area, label, Icon }) => (
        <button key={area} type="button" className="rv-tabbar__item" aria-current={current === area ? "page" : undefined} onClick={() => onNavigate(area)}>
          <Icon size={22} aria-hidden="true" />{label}
        </button>
      ))}
    </nav>
  )
}

export { TabBar }
