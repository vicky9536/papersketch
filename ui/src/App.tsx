import { useMemo } from "react"
import { PaperSketchInlineCard } from "./components/PaperSketchInlineCard"

type ToolOutput = {
  summary?: string
  version?: string
  modelInfo?: string
}

// Read toolOutput injected by ChatGPT Apps runtime.
// In local dev (browser), this will be undefined; we show demo data.
function getToolOutput(): ToolOutput | null {
  const raw = window.openai?.toolOutput
  if (!raw || typeof raw !== "object") return null
  return raw as ToolOutput
}

const demo: ToolOutput = {
  summary: `* Paper Title: Attention Is All You Need
* Author Information:
  - Ashish Vaswani (Google Brain)
  - Noam Shazeer (Google Brain)

## Research Background
1. Traditional sequence transduction models rely on recurrent or convolutional neural networks with encoder-decoder architectures.
2. Recurrent models suffer from sequential computation constraints, limiting parallelization and efficiency.

![page=3](https://example.com/figure_1.png)

## Main Contributions
1. Proposes the Transformer, eliminating recurrence and convolutions.
2. Demonstrates superior parallelizability and training efficiency.`,
  version: "demo",
  modelInfo: "demo",
}

export default function App() {
  const data = useMemo(() => getToolOutput() ?? demo, [])
  return (
    <div className="p-3">
      <PaperSketchInlineCard data={data} />
    </div>
  )
}