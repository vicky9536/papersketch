import { useMemo, useState } from "react"
import { Badge } from "@openai/apps-sdk-ui/components/Badge"
import { Button } from "@openai/apps-sdk-ui/components/Button"
import { Download, Sparkle } from "@openai/apps-sdk-ui/components/Icon"

import { parsePaperSketchMarkdown } from "../lib/parsePaperSketch"
import { composeSketchFromToolOutput } from "../lib/composeSketchFromMarkdown"

type ToolOutput = {
  summary?: string
  version?: string
  modelInfo?: string

  // NEW: PDF download fields
  pdfUrl?: string
  pdfFilename?: string
}

async function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)

  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.rel = "noopener"
  a.style.display = "none"

  document.body.appendChild(a)
  a.click()

  setTimeout(() => {
    a.remove()
    URL.revokeObjectURL(url)
  }, 1000)
}


export function PaperSketchInlineCard(props: { data: ToolOutput }) {
  const { data } = props

  const parsed = useMemo(() => parsePaperSketchMarkdown(data.summary ?? ""), [data.summary])
  const title = parsed.title ?? "PaperSketch summary"
  const authors = parsed.authors?.slice(0, 2)?.join(", ") ?? ""
  const hasImages = parsed.images.length > 0

  // A short preview line (keep inline card light)
  const preview =
    parsed.plainPreview ||
    "Summary generated. Open the sketch to see a visual overview and key points."

  const [downloading, setDownloading] = useState(false)
  const [note, setNote] = useState<string | null>(null)

  const onDownloadSketch = async () => {
    setNote(null)
    setDownloading(true)

    try {
      // 1) Prefer server-generated PDF via pdfUrl
        if (data.pdfUrl) {
            setNote("Opening PDF…")
            const absoluteUrl = new URL(data.pdfUrl, window.location.href).toString()
            window.open(absoluteUrl, "_blank", "noopener,noreferrer")
            setNote("Opened PDF download.")
            return
        }


      // 2) Fallback: existing PNG sketch behavior
      setNote("Preparing sketch…")

      const blob = await composeSketchFromToolOutput({
        summary: data.summary ?? "",
      })

      if (!(blob instanceof Blob)) {
        setNote("Error: sketch generator did not return a Blob.")
        return
      }

      if (blob.size === 0) {
        setNote("Error: sketch Blob is empty.")
        return
      }

      setNote(`Sketch ready (${Math.round(blob.size / 1024)} KB). Downloading…`)
      await downloadBlob(blob, "papersketch.png")
      setNote("Downloaded sketch.")
    } catch (e) {
      console.error(e)
      setNote("Download failed. See console.")
    } finally {
      setDownloading(false)
    }
  }

  const onRefineInChat = async () => {
    await window.openai?.sendFollowUpMessage?.({
      prompt:
        "Rewrite the summary into: 1 sentence TL;DR, 5 bullet key points, 3 contributions, 2 limitations. Keep it faithful.",
    })
  }

  return (
    <div className="w-full max-w-[560px] rounded-2xl border border-default bg-surface shadow-lg p-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-secondary text-sm">PaperSketch</p>
          <h2 className="mt-1 heading-lg truncate">{title}</h2>

          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-secondary">
            {authors && (
              <span className="truncate">
                {authors}
                {parsed.authors && parsed.authors.length > 2 ? " et al." : ""}
              </span>
            )}
            {(data.modelInfo || data.version) && (
              <span className="text-tertiary">
                {data.modelInfo ? data.modelInfo : ""}
                {data.modelInfo && data.version ? " · " : ""}
                {data.version ? `v${data.version}` : ""}
              </span>
            )}
          </div>
        </div>

        <Badge color={hasImages ? "discovery" : "info"}>
          {hasImages ? `${parsed.images.length} figs` : "Text"}
        </Badge>
      </div>

      {/* Preview */}
      <div className="mt-3 rounded-xl bg-surface-secondary p-3">
        <div className="flex items-center gap-2">
          <Sparkle className="size-4 text-secondary" />
          <p className="text-sm text-secondary">Preview</p>
        </div>
        <p className="mt-1 text-sm">
          {preview.length > 300 ? preview.slice(0, 300) + "…" : preview}
        </p>
      </div>

      {/* Note */}
      {note && <p className="mt-3 text-sm text-secondary">{note}</p>}

      {/* Actions: keep it to 2 */}
      <div className="mt-4 flex items-center justify-end gap-2">
        <Button color="secondary" variant="outline" onClick={onRefineInChat}>
          Refine
        </Button>

        <Button
          color="secondary"
          variant="solid"
          onClick={onDownloadSketch}
          disabled={downloading || !data.summary}
        >
          <Download className="size-4" />
          {downloading ? "Building…" : "Download sketch"}
        </Button>
      </div>
    </div>
  )
}