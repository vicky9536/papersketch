export {}

declare global {
  interface Window {
    openai?: {
      toolOutput?: unknown
      setWidgetState?: (state: unknown) => void
      sendFollowUpMessage?: (args: { prompt: string }) => Promise<void>
      callTool?: (name: string, args: unknown) => Promise<unknown>
    }
  }
}
