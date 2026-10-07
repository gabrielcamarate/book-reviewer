import type { BookChunk } from "../book-types"

type Edit = NonNullable<BookChunk["edits"]>[number]
type Range = { start: number; end: number }
export type Segment = { text: string; marked: boolean }
export type Change = { before: string; after: string; why: string; original: Range; revised: Range }

const WORD = /[\p{L}\p{N}]/u

function widen(text: string, start: number, end: number): Range {
  while (start > 0 && WORD.test(text[start - 1])) start--
  while (end < text.length && WORD.test(text[end])) end++
  return { start, end }
}

/** Each correction of a paragraph widened to whole words, in the original and in the revised text. */
export function changes(original: string, revised: string, edits: Edit[], paragraphId: string | number): Change[] {
  let offset = 0
  const list: Change[] = []
  for (const edit of edits.filter(item => String(item.paragraph_id) === String(paragraphId) && item.start !== undefined).sort((a, b) => a.start! - b.start!)) {
    const before = widen(original, edit.start!, edit.start! + edit.original.length)
    const afterStart = edit.start! + offset
    const after = widen(revised, afterStart, afterStart + edit.replacement.length)
    offset += edit.replacement.length - edit.original.length
    const last = list[list.length - 1]
    if (last && before.start < last.original.end) {
      last.original.end = Math.max(last.original.end, before.end)
      last.revised.end = Math.max(last.revised.end, after.end)
      last.before = original.slice(last.original.start, last.original.end)
      last.after = revised.slice(last.revised.start, last.revised.end)
      continue
    }
    list.push({ before: original.slice(before.start, before.end), after: revised.slice(after.start, after.end), why: edit.reason, original: before, revised: after })
  }
  return list
}

/** Split text into plain and marked parts; invalid or overlapping ranges are ignored. */
export function segments(text: string, ranges: Range[]): Segment[] {
  const parts: Segment[] = []
  let cursor = 0
  for (const range of [...ranges].sort((a, b) => a.start - b.start)) {
    if (range.start < cursor || range.end <= range.start || range.end > text.length) continue
    if (range.start > cursor) parts.push({ text: text.slice(cursor, range.start), marked: false })
    parts.push({ text: text.slice(range.start, range.end), marked: true })
    cursor = range.end
  }
  if (cursor < text.length || !parts.length) parts.push({ text: text.slice(cursor), marked: false })
  return parts
}
