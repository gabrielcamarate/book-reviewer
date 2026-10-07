import { useRef } from "react"
import { FileTextIcon, UploadIcon } from "lucide-react"

type FilePickerProps = {
  id: string
  file: File | null
  onChange: (file: File | null) => void
  title?: string
  hint?: string
  error?: string | null
  disabled?: boolean
}

/** Word file chooser without the browser's own control (design/components/FilePicker.md). */
function FilePicker({ id, file, onChange, title = "Escolher arquivo Word", hint = "Arquivo .docx de até 32 MB", error, disabled }: FilePickerProps) {
  const input = useRef<HTMLInputElement>(null)
  return (
    <div className="rv-field">
      <input ref={input} id={id} type="file" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" hidden
        onChange={event => { onChange(event.target.files?.[0] ?? null); event.target.value = "" }} />
      {file ? (
        <div className="rv-file">
          <div className="rv-file__info">
            <FileTextIcon size={28} aria-hidden="true" />
            <div><div className="rv-file__name">{file.name}</div><div className="rv-help">Arquivo escolhido</div></div>
          </div>
          <button type="button" className="rv-link rv-link--quiet" onClick={() => input.current?.click()} disabled={disabled}>Trocar arquivo</button>
        </div>
      ) : (
        <button type="button" className="rv-filepicker" onClick={() => input.current?.click()} disabled={disabled} aria-describedby={error ? `${id}-error` : undefined}>
          <span className="rv-filepicker__title"><UploadIcon size={24} aria-hidden="true" />{title}</span>
          <span className="rv-filepicker__hint">{hint}</span>
        </button>
      )}
      {error ? <p className="rv-error" role="alert" id={`${id}-error`}>{error}</p> : <p className="rv-help">Seu arquivo original não é alterado. O Revisor trabalha em uma cópia.</p>}
    </div>
  )
}

export { FilePicker }
