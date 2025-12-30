import { useSyncExternalStore } from "react"
import { PaperSketchInlineCard } from "./components/PaperSketchInlineCard"

type ToolOutput = {
  summary?: string
  version?: string
  modelInfo?: string
}

// Demo data for LOCAL browser dev only
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

// --- Host globals store ---
type OpenAiGlobals = { toolOutput?: unknown }
type SetGlobalsEvent = CustomEvent<{ globals?: OpenAiGlobals }>
const SET_GLOBALS_EVENT_TYPE = "openai:set_globals"

// Keep last seen globals from host events
let lastGlobals: OpenAiGlobals | null = null

function useHostToolOutput<T = unknown>(): T | undefined {
  return useSyncExternalStore(
    (onStoreChange) => {
      const handler = (evt: Event) => {
        const e = evt as SetGlobalsEvent
        // Host should send { detail: { globals: {...} } }
        if (e.detail?.globals) {
          lastGlobals = e.detail.globals
          onStoreChange()
        }
      }

      window.addEventListener(SET_GLOBALS_EVENT_TYPE, handler as EventListener, {
        passive: true,
      })

      return () => {
        window.removeEventListener(SET_GLOBALS_EVENT_TYPE, handler as EventListener)
      }
    },
    () => {
      // Prefer event-fed globals; if host also injects window.openai, use it as a fallback.
      const fromEvents = lastGlobals?.toolOutput as T | undefined
      const fromWindow = (globalThis as any)?.openai?.toolOutput as T | undefined
      return fromEvents ?? fromWindow
    }
  )
}

export default function App() {
  const toolOutput = useHostToolOutput<ToolOutput>()

  const isLocal =
    location.hostname === "localhost" || location.hostname === "127.0.0.1"

  const data: ToolOutput | undefined = toolOutput ?? (isLocal ? demo : undefined)

  console.log("toolOutput(from host):", toolOutput)
  console.log("window.openai exists?:", (globalThis as any)?.openai !== undefined)

  if (!data) {
    return (
      <div className="p-3 text-sm text-secondary">
        Waiting for tool output…
      </div>
    )
  }

  return (
    <div className="p-3">
      <div className="text-xs opacity-60">
        BUILD MARKER: 2025-12-30-A
      </div>
      <PaperSketchInlineCard data={data} />
    </div>
  )
}
