export type ReviewStatus = "pending" | "reviewing" | "ready" | "accepting" | "rejected"
export type BusyAction = "loading" | "review" | "accept" | "reject" | "translate" | "export" | null

export type SimpleHomeChange = {
  index: number
  change_type: string
  reason: string
  confidence: string
  original_text: string
  suggested_text: string
  original_html: string
  suggested_html: string
  original_fragment: string
  suggested_fragment: string
}

export type SimpleHomeState = {
  has_actionable_chunk: boolean
  chunk?: {
    id: string
  }
  orientation?: {
    current_chapter_title: string
    remaining_chapter_count: number
    current_chunk_position: number
    chapter_chunk_count: number
    remaining_actionable_chunk_count: number
    queue_status: string
  }
  original_text?: string
  revised_text?: string
  original_diff_html?: string
  revised_diff_html?: string
  review_available?: boolean
  rejection_reason?: string
  spanish_available?: boolean
  spanish_text?: string
  changes?: SimpleHomeChange[]
  summary?: {
    total_chunks?: number
    approved_count?: number
    reference_count?: number
    pending_copyedit_count?: number
    awaiting_approval_count?: number
    translated_count?: number
  }
}

export type CopyTarget = "review" | "spanish" | null
