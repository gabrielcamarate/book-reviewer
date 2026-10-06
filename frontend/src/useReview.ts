import { useCallback, useEffect, useRef, useState } from "react"
import type { BusyAction, CopyTarget, ReviewStatus, SimpleHomeState } from "./types"

async function requestJson<T>(path: string, data?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    method: data === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data), signal,
  })
  const payload = await response.json()
  if (!response.ok) throw new Error(payload.error || "A operação não foi concluída.")
  return payload as T
}

export function useReview() {
  const [state, setState] = useState<SimpleHomeState | null>(null)
  const [busyAction, setBusyAction] = useState<BusyAction>("loading")
  const [errorMessage, setErrorMessage] = useState("")
  const [notice, setNotice] = useState("")
  const [rejectOpen, setRejectOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState("")
  const [copiedTarget, setCopiedTarget] = useState<CopyTarget>(null)
  const copyTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const loadSimpleHome = useCallback(async (signal?: AbortSignal) => {
    setBusyAction("loading")
    try {
      setState(await requestJson<SimpleHomeState>("/api/simple-home", undefined, signal))
      setErrorMessage("")
    } catch (error) {
      if (!signal?.aborted) setErrorMessage(error instanceof Error ? error.message : "Falha ao carregar a revisão.")
    } finally { if (!signal?.aborted) setBusyAction(null) }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void loadSimpleHome(controller.signal)
    return () => {
      controller.abort()
      if (copyTimer.current) clearTimeout(copyTimer.current)
    }
  }, [loadSimpleHome])

  async function act<T>(action: BusyAction, path: string, data: unknown): Promise<T | undefined> {
    setBusyAction(action); setErrorMessage(""); setNotice("")
    try {
      const result = await requestJson<T>(path, data)
      setState(await requestJson<SimpleHomeState>("/api/simple-home"))
      return result
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "A operação falhou.") }
    finally { setBusyAction(null) }
  }

  const chunk = { chunk_id: state?.chunk?.id }
  const handleReview = () => act("review", "/api/simple-home/review", chunk)
  const handleAccept = () => act("accept", "/api/simple-home/accept", chunk)
  async function handleReject() {
    if (!rejectReason.trim()) return
    const result = await act("reject", "/api/simple-home/reject", { ...chunk, reason: rejectReason.trim() })
    if (result) { setRejectOpen(false); setRejectReason("") }
  }
  async function handleTranslate() {
    const result = await act<{ processed_count: number; failed_count: number }>("translate", "/api/translate", {})
    if (result) setNotice(`${result.processed_count} trecho(s) traduzido(s).${result.failed_count ? " Houve falhas; o progresso foi salvo." : ""}`)
  }
  async function handleExport(language: "pt-BR" | "es") {
    const result = await act<{ download_url: string }>("export", "/api/export", { language })
    if (result) { setNotice("Arquivo gerado. O download vai começar."); window.location.assign(result.download_url) }
  }
  async function handleCopy(target: Exclude<CopyTarget, null>, text: string) {
    try {
      await navigator.clipboard.writeText(text); setCopiedTarget(target)
      if (copyTimer.current) clearTimeout(copyTimer.current)
      copyTimer.current = setTimeout(() => setCopiedTarget(null), 1800)
    } catch { setErrorMessage("Não foi possível copiar o texto.") }
  }

  const reviewAvailable = Boolean(state?.review_available)
  const rejected = Boolean(state?.rejection_reason) && !reviewAvailable
  const status: ReviewStatus = rejected ? "rejected" : busyAction === "review" ? "reviewing"
    : busyAction === "accept" ? "accepting" : reviewAvailable ? "ready" : "pending"
  const activeStatusLabel = busyAction === "translate" ? "Traduzindo aprovados"
    : busyAction === "export" ? "Gerando arquivo" : rejected ? "Revisão recusada"
    : busyAction === "review" ? "Revisando trecho" : busyAction === "accept" ? "Consolidando revisão"
    : reviewAvailable ? "Aguardando decisão" : state && !state.has_actionable_chunk ? "Revisão concluída" : "Aguardando revisão"
  const summary = state?.summary
  const completed = (summary?.approved_count ?? 0) + (summary?.translated_count ?? 0) + (summary?.reference_count ?? 0)
  const progressValue = summary?.total_chunks ? Math.round(completed / summary.total_chunks * 100) : 0

  return { state, busyAction, errorMessage, notice, rejectOpen, setRejectOpen, rejectReason,
    setRejectReason, copiedTarget, loadSimpleHome, handleReview, handleAccept, handleReject,
    handleCopy, handleTranslate, handleExport, status, activeStatusLabel, progressValue }
}
