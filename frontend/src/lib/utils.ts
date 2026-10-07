/** Join the class names that apply, skipping false, null and undefined. */
export function cn(...names: (string | false | null | undefined)[]) {
  return names.filter(Boolean).join(" ")
}
