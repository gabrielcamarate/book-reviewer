import assert from "node:assert/strict"
import { test } from "node:test"

import { changes, segments } from "./marks.ts"

const original = "Haviam muitas conchas quando ela chegou a praia."
const revised = "Havia muitas conchas quando ela chegou à praia."
const edits = [
  { paragraph_id: "1", start: 5, end: 6, original: "m", replacement: "", reason: "Singular.", category: "gramática" },
  { paragraph_id: "1", start: 40, end: 41, original: "a", replacement: "à", reason: "Crase.", category: "gramática" },
  { paragraph_id: "2", start: 0, end: 3, original: "Ela", replacement: "Elas", reason: "Plural.", category: "gramática" },
]

test("a correction shows whole words, never loose letters", () => {
  assert.deepEqual(changes(original, revised, edits, "1").map(({ before, after, why }) => ({ before, after, why })), [
    { before: "Haviam", after: "Havia", why: "Singular." },
    { before: "a", after: "à", why: "Crase." },
  ])
})

test("marks cover the corrected words in each text", () => {
  const list = changes(original, revised, edits, "1")
  const marked = (text: string, side: "before" | "after") => segments(text, list.map(item => item[side === "before" ? "original" : "revised"])).filter(part => part.marked).map(part => part.text)
  assert.deepEqual(marked(revised, "after"), ["Havia", "à"])
  assert.deepEqual(marked(original, "before"), ["Haviam", "a"])
  assert.equal(segments(revised, list.map(item => item.revised)).map(part => part.text).join(""), revised)
})

test("several edits inside one word become one correction", () => {
  const word = [
    { paragraph_id: "3", start: 0, end: 1, original: "i", replacement: "e", reason: "Grafia.", category: "ortografia" },
    { paragraph_id: "3", start: 2, end: 3, original: "x", replacement: "s", reason: "Grafia.", category: "ortografia" },
  ]
  assert.deepEqual(changes("ixxo é", "exso é", word, "3").map(({ before, after }) => [before, after]), [["ixxo", "exso"]])
})

test("broken ranges never duplicate or drop text", () => {
  assert.equal(segments("Texto.", [{ start: 3, end: 2 }, { start: 1, end: 9 }]).map(part => part.text).join(""), "Texto.")
  assert.deepEqual(segments("Sem mudança.", []), [{ text: "Sem mudança.", marked: false }])
})
