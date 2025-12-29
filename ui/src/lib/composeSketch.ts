type Paper = {
  title?: string
  authors?: string[]
  year?: number
  venue?: string
  url?: string
}

type ToolOutput = {
  paper?: Paper
  summary_text?: string
  images?: { url: string; kind?: string; label?: string }[]
}

/**
 * Try to load an image in a canvas-safe way.
 * - First: direct <img crossOrigin="anonymous">
 * - Fallback: fetch as blob -> objectURL
 */
async function loadImage(url: string): Promise<HTMLImageElement> {
  // Attempt 1: <img> with crossOrigin
  const img1 = new Image()
  img1.crossOrigin = "anonymous"
  img1.decoding = "async"
  img1.referrerPolicy = "no-referrer"
  img1.src = url
  await img1.decode()
  return img1
}

function wrapText(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, maxWidth: number, lineHeight: number, maxLines: number) {
  const words = text.split(/\s+/)
  let line = ""
  let lines = 0
  for (let i = 0; i < words.length; i++) {
    const test = line ? `${line} ${words[i]}` : words[i]
    const w = ctx.measureText(test).width
    if (w > maxWidth && line) {
      ctx.fillText(line, x, y)
      y += lineHeight
      lines++
      line = words[i]
      if (lines >= maxLines) return { y, truncated: true }
    } else {
      line = test
    }
  }
  if (line && lines < maxLines) {
    ctx.fillText(line, x, y)
    y += lineHeight
    lines++
  }
  return { y, truncated: false }
}

function pickFigures(images: ToolOutput["images"]): string[] {
  const arr = Array.isArray(images) ? images : []
  const figures = arr.filter(i => (i.kind ?? "").toLowerCase() === "figure").map(i => i.url)
  const pages = arr.filter(i => (i.kind ?? "").toLowerCase() === "page").map(i => i.url)
  const any = arr.map(i => i.url)

  // Prefer up to 2 figures; else 1–2 “page” images; else first 2 images.
  return (figures.length ? figures : pages.length ? pages : any).slice(0, 2)
}

export async function composeSketchPng(data: ToolOutput): Promise<Blob> {
  const W = 1400
  const P = 64
  const cardRadius = 32

  const title = data.paper?.title ?? "PaperSketch"
  const authors = (data.paper?.authors ?? []).slice(0, 3).join(", ")
  const meta = [authors, data.paper?.venue, data.paper?.year].filter(Boolean).join(" · ")
  const url = data.paper?.url ?? ""

  const summary = (data.summary_text ?? "").trim()
  const figureUrls = pickFigures(data.images)

  // Load images (best effort). If CORS blocks it, we’ll skip images and still export text.
  const loadedImages: HTMLImageElement[] = []
  for (const u of figureUrls) {
    try {
      loadedImages.push(await loadImage(u))
    } catch {
      // Ignore: canvas export still works with text-only
    }
  }

  // Compute height: header + summary + images + footer
  const headerH = 220
  const summaryH = 360
  const imageH = loadedImages.length ? 520 : 0
  const footerH = 120
  const H = P + headerH + summaryH + imageH + footerH + P

  const canvas = document.createElement("canvas")
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext("2d")
  if (!ctx) throw new Error("No canvas context")

  // Background
  ctx.fillStyle = "#ffffff"
  ctx.fillRect(0, 0, W, H)

  // Card container
  const x0 = P
  const y0 = P
  const cardW = W - P * 2
  const cardH = H - P * 2

  // Rounded rect
  ctx.fillStyle = "#ffffff"
  ctx.strokeStyle = "rgba(0,0,0,0.10)"
  ctx.lineWidth = 2

  ctx.beginPath()
  const r = cardRadius
  ctx.moveTo(x0 + r, y0)
  ctx.arcTo(x0 + cardW, y0, x0 + cardW, y0 + cardH, r)
  ctx.arcTo(x0 + cardW, y0 + cardH, x0, y0 + cardH, r)
  ctx.arcTo(x0, y0 + cardH, x0, y0, r)
  ctx.arcTo(x0, y0, x0 + cardW, y0, r)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()

  // Header text
  let cx = x0 + 48
  let cy = y0 + 64

  ctx.fillStyle = "rgba(0,0,0,0.65)"
  ctx.font = "28px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  ctx.fillText("PaperSketch", cx, cy)

  cy += 64
  ctx.fillStyle = "rgba(0,0,0,0.92)"
  ctx.font = "64px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  // Title wrap (2 lines)
  wrapText(ctx, title, cx, cy, cardW - 96, 74, 2)
  cy += 96

  ctx.fillStyle = "rgba(0,0,0,0.55)"
  ctx.font = "30px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  if (meta) ctx.fillText(meta, cx, cy)

  // TL;DR block
  const sTop = y0 + headerH
  const boxX = x0 + 48
  const boxY = sTop + 24
  const boxW = cardW - 96
  const boxH = 300

  ctx.fillStyle = "rgba(0,0,0,0.035)"
  ctx.strokeStyle = "rgba(0,0,0,0.06)"
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.moveTo(boxX + 24, boxY)
  ctx.arcTo(boxX + boxW, boxY, boxX + boxW, boxY + boxH, 24)
  ctx.arcTo(boxX + boxW, boxY + boxH, boxX, boxY + boxH, 24)
  ctx.arcTo(boxX, boxY + boxH, boxX, boxY, 24)
  ctx.arcTo(boxX, boxY, boxX + boxW, boxY, 24)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()

  ctx.fillStyle = "rgba(0,0,0,0.60)"
  ctx.font = "26px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  ctx.fillText("TL;DR", boxX + 24, boxY + 48)

  ctx.fillStyle = "rgba(0,0,0,0.88)"
  ctx.font = "30px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  const t = summary || "No summary text returned."
  wrapText(ctx, t, boxX + 24, boxY + 100, boxW - 48, 44, 5)

  // Images row
  let imgTop = y0 + headerH + summaryH
  if (loadedImages.length) {
    const gap = 24
    const imgBoxX = x0 + 48
    const imgBoxW = cardW - 96
    const eachW = loadedImages.length === 1 ? imgBoxW : (imgBoxW - gap) / 2
    const eachH = 440

    for (let i = 0; i < loadedImages.length; i++) {
      const img = loadedImages[i]
      const ix = imgBoxX + i * (eachW + gap)
      const iy = imgTop + 24

      // frame
      ctx.fillStyle = "rgba(0,0,0,0.02)"
      ctx.strokeStyle = "rgba(0,0,0,0.08)"
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.moveTo(ix + 24, iy)
      ctx.arcTo(ix + eachW, iy, ix + eachW, iy + eachH, 24)
      ctx.arcTo(ix + eachW, iy + eachH, ix, iy + eachH, 24)
      ctx.arcTo(ix, iy + eachH, ix, iy, 24)
      ctx.arcTo(ix, iy, ix + eachW, iy, 24)
      ctx.closePath()
      ctx.fill()
      ctx.stroke()

      // draw image “contain”
      const pad = 16
      const dx = ix + pad
      const dy = iy + pad
      const dw = eachW - pad * 2
      const dh = eachH - pad * 2

      const scale = Math.min(dw / img.naturalWidth, dh / img.naturalHeight)
      const sw = img.naturalWidth * scale
      const sh = img.naturalHeight * scale
      const ox = dx + (dw - sw) / 2
      const oy = dy + (dh - sh) / 2
      ctx.drawImage(img, ox, oy, sw, sh)
    }
  }

  // Footer
  const fY = y0 + cardH - 64
  ctx.fillStyle = "rgba(0,0,0,0.45)"
  ctx.font = "24px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  const footerLeft = url ? `Source: ${url}` : "Source: (URL not provided)"
  ctx.fillText(footerLeft, x0 + 48, fY)
  ctx.textAlign = "right"
  ctx.fillText("Generated by PaperSketch", x0 + cardW - 48, fY)
  ctx.textAlign = "left"

  // Export
  const blob: Blob = await new Promise((resolve, reject) => {
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("toBlob failed"))), "image/png", 0.95)
  })
  return blob
}
