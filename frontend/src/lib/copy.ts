// Fixed texts shared by several screens (design/screens).

export const WHAT_IT_DOES = [
  "Corrige os erros do português, sem mudar o seu estilo.",
  "Confere cada correção antes de aplicar.",
  "Traduz para o espanhol da América Latina.",
  "Revisa o espanhol comparando com o português.",
]

export const STAGE_NAMES = ["Revisar o português", "Conferir e aplicar as correções", "Traduzir para o espanhol", "Revisar o espanhol"]

export function scopeLabel(scope: "whole" | "sections", count: number) {
  if (scope === "whole") return "O livro inteiro"
  return count === 1 ? "1 capítulo" : `${count} capítulos`
}

export function termsLabel(count: number) {
  return count === 0 ? "Nenhum termo" : count === 1 ? "1 termo" : `${count} termos`
}
