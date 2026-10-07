import { Button } from "@/components/ui/button"
import { StatusIcon } from "@/components/ui/notice"
import { Loading } from "@/components/ui/spinner"

/** carregando: the list or a book is opening. */
export function LoadingScreen({ book }: { book: boolean }) {
  return <Loading>{book ? "Abrindo o livro…" : "Abrindo seus livros…"}</Loading>
}

/** erro: the local server did not answer. */
export function ErrorScreen({ onRetry, busy, mobile }: { onRetry: () => void; busy: boolean; mobile: boolean }) {
  return (
    <div className="rv-message">
      <StatusIcon alert />
      <h1 className={mobile ? "title-page-mobile" : "title-reading"}>Não foi possível abrir seus livros</h1>
      <p className="rv-muted">O Revisor parece estar fechado neste computador. Abra o Revisor de novo e depois toque em “Tentar de novo”. Nada do que você já fez foi perdido.</p>
      <Button variant="primary" size="lg" block={mobile} onClick={onRetry} disabled={busy}>Tentar de novo</Button>
      <p className="rv-small rv-muted">Se continuar assim, peça ajuda a quem instalou o Revisor.</p>
    </div>
  )
}
