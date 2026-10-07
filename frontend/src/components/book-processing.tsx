import { AlertCircleIcon, CheckIcon } from "lucide-react"
import { TextLink } from "@/components/ui/link"
import { ProgressBar } from "./ui/progress"
import { Spinner } from "./ui/spinner"
import type { BookDetail } from "@/book-types"

export function BookProgress({ book }: { book: BookDetail }) {
  const p = book.progress
  const stages = [
    ["Propostas em português", p.draft_paragraphs ?? p.approved_paragraphs, p.draft_percent ?? p.review_percent],
    ["Português aprovado", p.approved_paragraphs, p.review_percent],
    ["Tradução em espanhol", p.translated_paragraphs, p.translation_percent],
    ["Espanhol revisado", p.checked_paragraphs, p.checked_percent],
  ] as const
  return <div className="progress-area" aria-label="Progresso salvo do livro">{stages.map(([label, count, percent]) => <div className="progress-row" key={label}>
    <div><span>{label}</span><strong>{count.toLocaleString("pt-BR")} / {p.total_paragraphs.toLocaleString("pt-BR")} parágrafos</strong></div>
    <ProgressBar value={percent} label={label} />
  </div>)}</div>
}

export function BookJobStatus({ book, onInspect }: { book: BookDetail; onInspect: (chunkId: string) => void }) {
  const job = book.job
  if (!job) return null
  const running = ["running", "stopping"].includes(job.status)
  const attention = ["needs_attention", "failed", "interrupted"].includes(job.status)
  const outdated = job.task === "automatic" && job.status === "completed" && !book.automatic_result
  const elapsed = Math.floor((job.elapsed_seconds ?? 0) / 60)
  const label = job.task === "automatic" ? job.phase ?? "Preparando o processamento" : job.task === "review" ? "Revisão do português" : "Tradução para espanhol"
  return <>
    <div className="job-status" data-attention={attention} role="status">
      {running ? <Spinner /> : attention ? <AlertCircleIcon aria-hidden="true" /> : <CheckIcon aria-hidden="true" />}
      <div><strong>{job.status === "needs_attention" ? "Há trechos para conferir" : job.status === "failed" || job.status === "interrupted" ? "Processamento interrompido" : job.status === "paused" ? "Processamento pausado" : job.status === "completed" ? job.task === "automatic" ? "Processamento concluído" : "Lote concluído" : label}</strong>
        <p>{outdated ? "O conteúdo mudou. Continue para revisar e preparar os arquivos atuais." : job.message}</p>
        <p className="job-count">{job.task === "automatic" ? `${book.progress.checked_paragraphs.toLocaleString("pt-BR")} de ${book.progress.total_paragraphs.toLocaleString("pt-BR")} parágrafos passaram pela revisão do espanhol.` : `${job.processed} de ${job.total} trechos processados.`}
          {running && job.phase_total ? ` Nesta etapa: ${job.phase_attempted ?? job.phase_processed ?? 0} de ${job.phase_total} trechos conferidos.` : ""}{elapsed > 0 ? ` Tempo nesta execução: ${elapsed} min.` : ""}</p>
      </div>
    </div>
    {Boolean(job.problems?.length) && <section className="processing-problems" aria-labelledby="problems-heading">
      <h3 id="problems-heading">Trechos que precisam de atenção ({job.problems!.length})</h3>
      <p>O progresso dos outros trechos foi salvo. Você pode tentar os pendentes novamente ou conferir cada um pelo modo manual.</p>
      <ul>{job.problems!.map((problem, index) => <li key={`${problem.chunk_id}-${index}`}>
        <TextLink onClick={() => onInspect(problem.chunk_id)}>Conferir trecho {problem.index ?? ""}: {problem.title ?? "trecho pendente"}</TextLink>
        <span>{problem.phase}</span><p>{problem.message}</p>
      </li>)}</ul>
    </section>}
  </>
}
