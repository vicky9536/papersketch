import { useMemo } from "react"
import { PaperSketchInlineCard } from "./components/PaperSketchInlineCard"

function getToolOutput(): any {
  const raw = window.openai?.toolOutput
  if (!raw || typeof raw !== "object") return null
  return raw
}

export default function App() {
  const data = useMemo(() => getToolOutput(), [])

  // Local dev demo data if not running inside ChatGPT
  const demo = {
    paper: {
      title: "Attention Is All You Need",
      authors: ["Vaswani", "Shazeer", "Parmar", "Uszkoreit"],
      year: 2017,
      venue: "NeurIPS",
      url: "https://arxiv.org/abs/1706.03762",
    },
    tldr: "Introduces the Transformer, replacing recurrence with self-attention for sequence modeling.",
    key_takeaways: [
      "Self-attention enables parallel training and long-range dependencies.",
      "Multi-head attention improves representation capacity.",
      "Strong results with efficient parallel training.",
    ],
    generated_image_url: "",
  }

  return (
    <div className="p-3">
      <PaperSketchInlineCard data={data ?? demo} />
    </div>
  )
}