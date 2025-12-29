export type ParsedPaperSketch = {
  title?: string
  authors?: string[]
  sections: { heading: string; bullets: string[] }[]
  images: { url: string; label?: string }[]
  plainPreview: string
}

const IMG_RE = /!\[(?<label>[^\]]*)\]\((?<url>https?:\/\/[^)]+)\)/g

export function parsePaperSketchMarkdown(md: string): ParsedPaperSketch {
  const images: { url: string; label?: string }[] = []
  for (const m of md.matchAll(IMG_RE)) {
    const url = m.groups?.url?.trim()
    if (url) images.push({ url, label: m.groups?.label?.trim() })
  }

  // Extract title + authors from the top bullet area
  // Format:
  // * Paper Title: ...
  // * Author Information:
  //   - Name (Org)
  const lines = md.split(/\r?\n/)
  let title: string | undefined
  const authors: string[] = []
  let inAuthors = false

  for (const raw of lines) {
    const line = raw.trim()

    const mTitle = line.match(/^\*\s*Paper Title:\s*(.+)\s*$/i)
    if (mTitle) title = mTitle[1].trim()

    if (/^\*\s*Author Information:/i.test(line)) {
      inAuthors = true
      continue
    }
    if (inAuthors) {
      if (line.startsWith("## ")) inAuthors = false
      const mAuthor = line.match(/^-+\s*(.+)$/)
      if (mAuthor) authors.push(mAuthor[1].trim())
    }
  }

  // Split into sections by "## Heading"
  const sections: { heading: string; bullets: string[] }[] = []
  const parts = md.split(/\n##\s+/) // first chunk is preface
  for (let i = 1; i < parts.length; i++) {
    const chunk = parts[i]
    const [headingLine, ...rest] = chunk.split("\n")
    const heading = (headingLine ?? "").trim()

    const bullets: string[] = []
    for (const r of rest) {
      const t = r.trim()
      if (!t) continue
      if (t.startsWith("![")) continue // ignore images
      // numbered bullet lines like "1. ...", "2. ..."
      const mNum = t.match(/^\d+\.\s+(.*)$/)
      if (mNum) bullets.push(mNum[1].trim())
    }

    if (heading) sections.push({ heading, bullets })
  }

  // Make a small preview paragraph (first 2–3 bullets across first sections)
  const previewBits: string[] = []
  for (const sec of sections) {
    for (const b of sec.bullets) {
      previewBits.push(b)
      if (previewBits.length >= 3) break
    }
    if (previewBits.length >= 3) break
  }

  return {
    title,
    authors: authors.length ? authors : undefined,
    sections,
    images,
    plainPreview: previewBits.join(" "),
  }
}
