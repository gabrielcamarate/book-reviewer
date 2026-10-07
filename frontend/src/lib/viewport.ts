import { useSyncExternalStore } from "react"

// Phone layout below 768px: tab bar, single column, stacked buttons (design/README.md, "Estrutura das telas").
export const MOBILE_QUERY = "(max-width: 767px)"

function subscribe(listener: () => void) {
  const query = window.matchMedia(MOBILE_QUERY)
  query.addEventListener("change", listener)
  return () => query.removeEventListener("change", listener)
}

export function useIsMobile() {
  return useSyncExternalStore(subscribe, () => window.matchMedia(MOBILE_QUERY).matches)
}
