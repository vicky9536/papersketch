import { parsePaperSketchMarkdown } from "./parsePaperSketch"

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
  maxLines: number
) {
  const words = text.split(/\s+/)
  let line = ""
  let lines = 0

  for (const w of words) {
    const test = line ? `${line} ${w}` : w
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, y)
      y += lineHeight
      lines++
      line = w
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

async function loadImage(url: string): Promise<HTMLImageElement> {
  const img = new Image()
  img.crossOrigin = "anonymous"
  img.referrerPolicy = "no-referrer"
  img.decoding = "async"
  img.src = url
  await img.decode()
  return img
}

export async function composeSketchFromToolOutput(toolOutput: { summary: string }): Promise<Blob> {
  const parsed = parsePaperSketchMarkdown(toolOutput.summary || "")
  const title = parsed.title ?? "PaperSketch"
  const authors = parsed.authors?.slice(0, 3)?.join(", ") ?? ""

  // Pick bullets for infographic (6 bullets max)
  const bullets: string[] = []
  const preferredOrder = [
    "Main Contributions",
    "Research Background",
    "Research Methodology",
    "Experimental Results",
    "Limitations",
    "Future Work",
  ]
  for (const name of preferredOrder) {
    const sec = parsed.sections.find(s => s.heading.toLowerCase() === name.toLowerCase())
    if (!sec) continue
    for (const b of sec.bullets) {
      bullets.push(b)
      if (bullets.length >= 6) break
    }
    if (bullets.length >= 6) break
  }
  if (!bullets.length) {
    // fallback: first bullets anywhere
    for (const sec of parsed.sections) {
      for (const b of sec.bullets) {
        bullets.push(b)
        if (bullets.length >= 6) break
      }
      if (bullets.length >= 6) break
    }
  }

  // Load up to 2 images (figures/tables)
  const imgUrls = parsed.images.map(i => i.url).slice(0, 2)
  const imgs: HTMLImageElement[] = []
  for (const u of imgUrls) {
    try {
      imgs.push(await loadImage(u))
    } catch {
      // CORS might block. Still export a text-only infographic.
    }
  }

  // Canvas size
  const W = 1400
  const P = 64
  const headerH = 220
  const bulletsH = 520
  const imageH = imgs.length ? 520 : 0
  const footerH = 110
  const H = P + headerH + bulletsH + imageH + footerH + P

  const canvas = document.createElement("canvas")
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext("2d")
  if (!ctx) throw new Error("no canvas context")

  // background
  ctx.fillStyle = "#ffffff"
  ctx.fillRect(0, 0, W, H)

  // card border
  const x0 = P, y0 = P, cardW = W - 2 * P, cardH = H - 2 * P, r = 32
  ctx.strokeStyle = "rgba(0,0,0,0.10)"
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(x0 + r, y0)
  ctx.arcTo(x0 + cardW, y0, x0 + cardW, y0 + cardH, r)
  ctx.arcTo(x0 + cardW, y0 + cardH, x0, y0 + cardH, r)
  ctx.arcTo(x0, y0 + cardH, x0, y0, r)
  ctx.arcTo(x0, y0, x0 + cardW, y0, r)
  ctx.closePath()
  ctx.stroke()

  const cx = x0 + 56
  let cy = y0 + 70

  // header
  ctx.fillStyle = "rgba(0,0,0,0.60)"
  ctx.font = "28px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  ctx.fillText("PaperSketch", cx, cy)

  cy += 66
  ctx.fillStyle = "rgba(0,0,0,0.92)"
  ctx.font = "64px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  wrapText(ctx, title, cx, cy, cardW - 112, 74, 2)

  cy += 108
  ctx.fillStyle = "rgba(0,0,0,0.55)"
  ctx.font = "30px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  if (authors) ctx.fillText(authors + (parsed.authors && parsed.authors.length > 3 ? " et al." : ""), cx, cy)

  // bullets block
  const bTop = y0 + headerH
  const boxX = x0 + 56
  const boxY = bTop + 24
  const boxW = cardW - 112
  const boxH = 460

  ctx.fillStyle = "rgba(0,0,0,0.035)"
  ctx.strokeStyle = "rgba(0,0,0,0.06)"
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.roundRect(boxX, boxY, boxW, boxH, 24)
  ctx.fill()
  ctx.stroke()

  ctx.fillStyle = "rgba(0,0,0,0.60)"
  ctx.font = "26px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  ctx.fillText("Key points", boxX + 24, boxY + 48)

  ctx.fillStyle = "rgba(0,0,0,0.88)"
  ctx.font = "30px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"

  let ty = boxY + 100
  for (let i = 0; i < Math.min(6, bullets.length); i++) {
    ctx.fillText("•", boxX + 24, ty)
    const res = wrapText(ctx, bullets[i], boxX + 52, ty, boxW - 76, 44, 2)
    ty = res.y + 10
    if (ty > boxY + boxH - 40) break
  }

  // images
  if (imgs.length) {
    const imgTop = y0 + headerH + bulletsH
    const gap = 24
    const frameX = x0 + 56
    const frameW = cardW - 112
    const eachW = imgs.length === 1 ? frameW : (frameW - gap) / 2
    const eachH = 440
    const iy = imgTop + 24

    for (let i = 0; i < imgs.length; i++) {
      const ix = frameX + i * (eachW + gap)

      ctx.fillStyle = "rgba(0,0,0,0.02)"
      ctx.strokeStyle = "rgba(0,0,0,0.08)"
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.roundRect(ix, iy, eachW, eachH, 24)
      ctx.fill()
      ctx.stroke()

      const img = imgs[i]
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

  // footer
  ctx.fillStyle = "rgba(0,0,0,0.45)"
  ctx.font = "24px system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  ctx.fillText("Generated by PaperSketch (client-side)", x0 + 56, y0 + cardH - 56)

  const blob: Blob = await new Promise((resolve, reject) => {
    canvas.toBlob(b => (b ? resolve(b) : reject(new Error("toBlob failed"))), "image/png", 0.95)
  })
  return blob
}
