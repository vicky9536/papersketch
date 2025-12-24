import { Badge } from "@openai/apps-sdk-ui/components/Badge"
import { Button } from "@openai/apps-sdk-ui/components/Button"
import { Sparkle, ExternalLink } from "@openai/apps-sdk-ui/components/Icon"

type SummaryBlock = { label: string; text: string }

export type PaperSketchToolOutput = {
  paper?: {
    title?: string
    authors?: string[]
    year?: number
    venue?: string
    url?: string
  }
  tldr?: string
  key_takeaways?: string[]
  summary_blocks?: SummaryBlock[] // you can show more in fullscreen later
  generated_image_url?: string
}

function safeArray<T>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : []
}

export function PaperSketchInlineCard(props: { data: PaperSketchToolOutput }) {
  const { data } = props
  const title = data.paper?.title ?? "Paper summary"
  const authors = safeArray<string>(data.paper?.authors).slice(0, 3)
  const year = data.paper?.year
  const venue = data.paper?.venue
  const url = data.paper?.url

  const takeaways = safeArray<string>(data.key_takeaways).slice(0, 4)
  const tldr = data.tldr ?? ""

  const onOpenPaper = () => {
    if (!url) return
    window.open(url, "_blank", "noopener,noreferrer")
  }

  const onRefineSummary = async () => {
    // Keep actions minimal (inline card rule: max 2 primary actions). :contentReference[oaicite:4]{index=4}
    await window.openai?.sendFollowUpMessage?.({
      prompt:
        "Refine the summary: keep it accurate, add 3 key contributions, 2 limitations, and a 1-sentence TL;DR.",
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
            {authors.length > 0 && (
              <span className="truncate">
                {authors.join(", ")}
                {safeArray<string>(data.paper?.authors).length > 3 ? " et al." : ""}
              </span>
            )}
            {(venue || year) && (
              <span className="text-tertiary">
                {venue ? venue : ""}
                {venue && year ? " · " : ""}
                {year ? year : ""}
              </span>
            )}
          </div>
        </div>

        <Badge color="secondary">Summary</Badge>
      </div>

      {/* Body */}
      {tldr && (
        <div className="mt-3 rounded-xl bg-surface-secondary p-3">
          <p className="text-sm text-secondary">TL;DR</p>
          <p className="mt-1 text-sm">{tldr}</p>
        </div>
      )}

      {/* Image preview (optional) */}
      {data.generated_image_url && (
        <div className="mt-3 overflow-hidden rounded-xl border border-default bg-surface">
          {/* Keep aspect ratio stable; avoid internal scrolling. :contentReference[oaicite:5]{index=5} */}
          <img
            src={data.generated_image_url}
            alt="Generated visual summary"
            className="block w-full h-auto"
          />
        </div>
      )}

      {/* Key takeaways */}
      {takeaways.length > 0 && (
        <div className="mt-3">
          <div className="flex items-center gap-2">
            <Sparkle className="size-4 text-secondary" />
            <p className="text-sm text-secondary">Key takeaways</p>
          </div>
          <ul className="mt-2 list-disc pl-5 text-sm space-y-1">
            {takeaways.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions (rule: max two) */}
      <div className="mt-4 flex items-center justify-end gap-2">
        {url && (
          <Button color="secondary" variant="outline" onClick={onOpenPaper}>
            <ExternalLink className="size-4" />
            Open paper
        </Button>
        )}
        <Button color="secondary" variant="solid" onClick={onRefineSummary}>
            Refine
        </Button>
      </div>
    </div>
  )
}