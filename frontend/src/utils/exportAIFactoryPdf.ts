/**
 * AI Factory — Export PDF groupé (charte EDUAI Learning).
 *
 * Un seul PDF pour TOUTES les leçons générées du batch courant :
 * couverture navy/orange, sommaire cliquable + bookmarks PDF,
 * une leçon par page (Lesson Content mis en forme + encadrés Media Content),
 * pied de page paginé sur chaque page.
 *
 * Polices : Cormorant Garamond / DM Sans sont chargées via Google Fonts CDN
 * (src/index.css:1, src/index.css:27,35) et ne peuvent pas être embarquées
 * telles quelles dans jsPDF ; on utilise les équivalents standards Times
 * (serif display) et Helvetica (texte courant) avec les couleurs EXACTES de
 * tailwind.config.js:7-29.
 */
import { jsPDF } from "jspdf";

const NAVY = "#0D1B2A";
const NAVY_M = "#1A2E4A";
const ORANGE = "#FF6B2B";
const ORANGE_L = "#FFB347";
const CREAM_M = "#F5EDE4";
const GRAY = "#8A7A6E";
const BLUE_BG = "#EFF6FF";
const BLUE_BORDER = "#BFDBFE";
const BLUE_LABEL = "#2563EB";
const PINK_BG = "#FDF2F8";
const PINK_BORDER = "#FBCFE8";
const PINK_LABEL = "#DB2777";

const PAGE_W = 595.28;
const PAGE_H = 841.89;
const MARGIN = 56;
const CONTENT_W = PAGE_W - MARGIN * 2;

export interface AIFactoryPdfBundle {
  plan?: {
    title?: string;
    level?: string;
    category?: string;
    modules?: { title: string; lessons?: { title: string }[] }[];
  } | null;
  lessons?: Record<string, string> | null;
  media_prompts?: Record<
    string,
    { image_prompt?: string | null; video_prompt?: string | null }
  > | null;
}

interface LessonEntry {
  key: string;
  moduleTitle: string;
  lessonTitle: string;
  content: string;
  imagePrompt: string;
  videoPrompt: string;
}

/** Format exigé: EDUAI_AIFactory_Export_YYYY-MM-DD_HHhMM.pdf */
export function aiFactoryExportFileName(d: Date = new Date()): string {
  const p = (n: number) => String(n).padStart(2, "0");
  const date = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  const time = `${p(d.getHours())}h${p(d.getMinutes())}`;
  return `EDUAI_AIFactory_Export_${date}_${time}.pdf`;
}

/** Leçons dans l'ordre du plan == ordre de génération (useContentCreator.ts:140-150). */
function orderedLessons(bundle: AIFactoryPdfBundle): LessonEntry[] {
  const lessons = bundle.lessons || {};
  const media = bundle.media_prompts || {};
  const entries: LessonEntry[] = [];
  const push = (key: string, moduleTitle: string, lessonTitle: string) => {
    if (!(key in lessons)) return;
    const m = media[key] || {};
    entries.push({
      key,
      moduleTitle,
      lessonTitle,
      content: lessons[key] || "",
      imagePrompt: (m.image_prompt || "").trim(),
      videoPrompt: (m.video_prompt || "").trim(),
    });
  };
  for (const mod of bundle.plan?.modules || []) {
    for (const les of mod.lessons || []) {
      push(`${mod.title}::${les.title}`, mod.title || "", les.title || "");
    }
  }
  for (const key of Object.keys(lessons)) {
    if (!entries.some((e) => e.key === key)) {
      const sep = key.indexOf("::");
      push(key, key.slice(0, sep), key.slice(sep + 2) || key);
    }
  }
  return entries;
}

type Block =
  | { t: "h1"; text: string }
  | { t: "h2"; text: string }
  | { t: "h3"; text: string }
  | { t: "ul"; items: string[] }
  | { t: "ol"; items: string[] }
  | { t: "quote"; text: string }
  | { t: "p"; text: string };

/** Markdown léger: titres #/##/###, listes -,*,1., citations >, paragraphes. */
function parseBlocks(content: string): Block[] {
  const blocks: Block[] = [];
  const nl = String.fromCharCode(10);
  const lines = content.replace(new RegExp("\\r", "g"), "").split(nl);
  let para: string[] = [];
  const flushPara = () => {
    if (para.length) {
      blocks.push({ t: "p", text: para.join(" ").trim() });
      para = [];
    }
  };
  for (const raw of lines) {
    const line = raw.trim();
    const isBullet = /^[-*•]\s+/.test(line);
    const isNumbered = /^\d+[.)]\s+/.test(line);
    if (!line) { flushPara(); continue; }
    if (/^###\s+/.test(line)) { flushPara(); blocks.push({ t: "h3", text: line.replace(/^###\s+/, "") }); }
    else if (/^##\s+/.test(line)) { flushPara(); blocks.push({ t: "h2", text: line.replace(/^##\s+/, "") }); }
    else if (/^#\s+/.test(line)) { flushPara(); blocks.push({ t: "h1", text: line.replace(/^#\s+/, "") }); }
    else if (/^>\s?/.test(line)) { flushPara(); blocks.push({ t: "quote", text: line.replace(/^>\s?/, "") }); }
    else if (isBullet) {
      flushPara();
      const last = blocks[blocks.length - 1];
      const item = line.replace(/^[-*•]\s+/, "");
      if (last && last.t === "ul") last.items.push(item);
      else blocks.push({ t: "ul", items: [item] });
    } else if (isNumbered) {
      flushPara();
      const last = blocks[blocks.length - 1];
      const item = line.replace(/^\d+[.)]\s+/, "");
      if (last && last.t === "ol") last.items.push(item);
      else blocks.push({ t: "ol", items: [item] });
    } else para.push(line);
  }
  flushPara();
  return blocks;
}

// ── Rendu texte riche (gras **...**) avec wrap manuel ───────────────────────
type Token = { text: string; bold: boolean };

function tokenizeInline(text: string): Token[] {
  const tokens: Token[] = [];
  const parts = text.split("**");
  parts.forEach((part, i) => {
    if (part) tokens.push({ text: part, bold: i % 2 === 1 });
  });
  return tokens;
}

interface DrawOpts {
  size: number;
  color: string;
  lineHeightFactor?: number;
  font?: "helvetica" | "times";
}

function drawStyledText(
  doc: jsPDF,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  opts: DrawOpts
): number {
  const { size, color, font = "helvetica" } = opts;
  const lh = (opts.lineHeightFactor ?? 1.45) * size;
  doc.setFont(font, "normal");
  doc.setFontSize(size);
  doc.setTextColor(color);
  const spaceW = doc.getTextWidth(" ");
  type Word = { text: string; w: number; bold: boolean };
  const words: Word[] = [];
  for (const tok of tokenizeInline(text)) {
    doc.setFont(font, tok.bold ? "bold" : "normal");
    for (const w of tok.text.split(/\s+/).filter(Boolean)) {
      words.push({ text: w, w: doc.getTextWidth(w), bold: tok.bold });
    }
  }
  let lineX = x;
  let cursor = y;
  for (const word of words) {
    if (lineX > x && lineX + word.w > x + maxWidth) {
      lineX = x;
      cursor += lh;
    }
    doc.setFont(font, word.bold ? "bold" : "normal");
    doc.text(word.text, lineX, cursor);
    lineX += word.w + spaceW;
  }
  return cursor + lh;
}

function measureStyledLines(doc: jsPDF, text: string, maxWidth: number, size: number): number {
  const plain = text.replace(/\*\*/g, "");
  doc.setFont("helvetica", "normal");
  doc.setFontSize(size);
  return doc.splitTextToSize(plain, maxWidth).length;
}

// ── Construction du document ────────────────────────────────────────────────

export function buildAIFactoryPdf(bundle: AIFactoryPdfBundle): jsPDF {
  const lessons = orderedLessons(bundle);
  const doc = new jsPDF({ unit: "pt", format: "a4", compress: true });
  let y = MARGIN;

  const ensureSpace = (h: number) => {
    if (y + h > PAGE_H - MARGIN - 26) {
      doc.addPage();
      y = MARGIN;
    }
  };

  // ── Page 1 : couverture EDUAI Learning ──
  doc.setFillColor(NAVY);
  doc.rect(0, 0, PAGE_W, PAGE_H, "F");
  try {
    doc.setGState(doc.GState({ opacity: 0.08 }));
    doc.setFillColor(ORANGE);
    doc.circle(PAGE_W - 60, 110, 190, "F");
    doc.circle(40, PAGE_H - 90, 150, "F");
    doc.setGState(doc.GState({ opacity: 1 }));
  } catch { /* GState indisponible: fond uni */ }
  doc.setFillColor(ORANGE);
  doc.rect(MARGIN, MARGIN + 6, 46, 4, "F");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.setTextColor(ORANGE_L);
  doc.text("EDUAI LEARNING".split("").join(" "), MARGIN, MARGIN + 42);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor("#9AABB3");
  doc.text("A I   F A C T O R Y   —   E X P O R T", MARGIN, MARGIN + 62);

  const courseTitle = bundle.plan?.title?.trim() || "Cours généré par IA";
  doc.setFont("times", "bold");
  doc.setFontSize(31);
  doc.setTextColor("#FFFFFF");
  const titleLines = doc.splitTextToSize(courseTitle, CONTENT_W);
  doc.text(titleLines, MARGIN, PAGE_H / 2 - 60);

  doc.setFillColor(ORANGE);
  doc.rect(MARGIN, PAGE_H / 2 - 34, 64, 3.5, "F");

  const meta = [
    new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }),
    `${lessons.length} leçon${lessons.length > 1 ? "s" : ""} · ${bundle.plan?.modules?.length || 0} module${(bundle.plan?.modules?.length || 0) > 1 ? "s" : ""}`,
    [bundle.plan?.level, bundle.plan?.category].filter(Boolean).join(" · "),
  ].filter(Boolean);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.setTextColor("#C5CDD9");
  meta.forEach((line, i) => doc.text(line, MARGIN, PAGE_H / 2 + 4 + i * 20));

  doc.setFontSize(8.5);
  doc.setTextColor("#6E898D");
  doc.text(
    "Document généré automatiquement par la plateforme EDUAI Learning — usage pédagogique interne.",
    MARGIN,
    PAGE_H - MARGIN
  );

  // ── Sommaire : pages réservées d'avance ──
  const tocRowH = 21;
  const perPage = Math.floor((PAGE_H - 2 * MARGIN - 70) / tocRowH);
  const tocPages = Math.max(1, Math.ceil(lessons.length / perPage));
  const tocRows: { page: number; yPos: number; label: string; target: number }[] = [];
  for (let p = 0; p < tocPages; p++) {
    doc.addPage();
    if (p === 0) {
      doc.setFont("times", "bold");
      doc.setFontSize(20);
      doc.setTextColor(NAVY);
      doc.text("Sommaire", MARGIN, MARGIN + 14);
      doc.setFillColor(ORANGE);
      doc.rect(MARGIN, MARGIN + 24, 44, 3, "F");
    } else {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10);
      doc.setTextColor(GRAY);
      doc.text(`Sommaire (suite ${p + 1}/${tocPages})`, MARGIN, MARGIN);
    }
    for (let i = p * perPage; i < Math.min((p + 1) * perPage, lessons.length); i++) {
      tocRows.push({
        page: doc.getNumberOfPages(),
        yPos: MARGIN + (p === 0 ? 58 : 30) + (i - p * perPage) * tocRowH,
        label: `${i + 1}.  ${lessons[i].moduleTitle} › ${lessons[i].lessonTitle}`.slice(0, 92),
        target: 0,
      });
    }
  }

  // ── Corps : une leçon = une nouvelle page ──
  const startPages: number[] = [];
  const sectionHeading = (num: string, title: string) => {
    ensureSpace(34);
    doc.setFillColor(ORANGE);
    doc.rect(MARGIN, y - 9, 16, 16, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor("#FFFFFF");
    doc.text(num, MARGIN + 8, y + 2.5, { align: "center" });
    doc.setFont("times", "bold");
    doc.setFontSize(13);
    doc.setTextColor(NAVY);
    doc.text(title, MARGIN + 24, y + 3);
    y += 12;
    doc.setDrawColor(CREAM_M);
    doc.setLineWidth(1);
    doc.line(MARGIN, y, PAGE_W - MARGIN, y);
    y += 14;
  };

  const renderMediaBox = (
    label: string,
    value: string,
    bg: string,
    border: string,
    labelColor: string,
    inkColor: string
  ) => {
    const padX = 12, padTop = 22, padBottom = 12;
    const innerW = CONTENT_W - padX * 2;
    const missing = !value;
    const shown = value || "Non généré pour cette leçon";
    doc.setFont("courier", "normal");
    doc.setFontSize(9);
    const lines = doc.splitTextToSize(shown, innerW);
    const boxH = missing ? padTop + padBottom + 6 : padTop + lines.length * 12 + padBottom;
    ensureSpace(boxH + 10);
    const top = y;
    doc.setFillColor(bg);
    doc.setDrawColor(border);
    doc.setLineWidth(1);
    doc.roundedRect(MARGIN, top, CONTENT_W, boxH, 6, 6, "FD");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.setTextColor(labelColor);
    doc.text(label.toUpperCase(), MARGIN + padX, top + 14);
    if (missing) {
      doc.setFont("helvetica", "italic");
      doc.setFontSize(9.5);
      doc.setTextColor(GRAY);
      doc.text(shown, MARGIN + padX, top + padTop + 2);
    } else {
      doc.setFont("courier", "normal");
      doc.setFontSize(9);
      doc.setTextColor(inkColor);
      lines.forEach((ln: string, i: number) =>
        doc.text(ln, MARGIN + padX, top + padTop + i * 12)
      );
    }
    y = top + boxH + 14;
  };

  lessons.forEach((lesson, li) => {
    doc.addPage();
    startPages.push(doc.getNumberOfPages());
    y = MARGIN;

    // En-tête de leçon
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(ORANGE);
    doc.text(`MODULE — ${lesson.moduleTitle}`.toUpperCase(), MARGIN, y);
    y += 18;
    doc.setFont("times", "bold");
    doc.setFontSize(19);
    doc.setTextColor(NAVY);
    const headLines = doc.splitTextToSize(lesson.lessonTitle, CONTENT_W);
    doc.text(headLines, MARGIN, y + 8);
    y += 8 + headLines.length * 22;
    doc.setFillColor(ORANGE);
    doc.rect(MARGIN, y, 40, 3, "F");
    y += 24;

    // 1. Lesson Content
    sectionHeading("1", "Lesson Content");
    const blocks = parseBlocks(lesson.content || "");
    if (!blocks.length) {
      doc.setFont("helvetica", "italic");
      doc.setFontSize(9.5);
      doc.setTextColor(GRAY);
      doc.text("Contenu non généré pour cette leçon.", MARGIN, y + 4);
      y += 20;
    }
    for (const b of blocks) {
      if (b.t === "h1" || b.t === "h2" || b.t === "h3") {
        const size = b.t === "h3" ? 11.5 : b.t === "h2" ? 12.5 : 14;
        const plain = b.text.replace(/\*\*/g, "");
        const nLines = measureStyledLines(doc, plain, CONTENT_W, size);
        ensureSpace(nLines * size * 1.35 + 16);
        doc.setFont("times", "bold");
        doc.setFontSize(size);
        doc.setTextColor(b.t === "h3" ? NAVY_M : NAVY);
        const out = doc.splitTextToSize(plain, CONTENT_W);
        doc.text(out, MARGIN, y + size);
        y += size * 1.35 * nLines + 8;
      } else if (b.t === "ul" || b.t === "ol") {
        b.items.forEach((item, idx) => {
          const nLines = measureStyledLines(doc, item, CONTENT_W - 18, 10.5);
          ensureSpace(nLines * 15.2 + 2);
          const bullet = b.t === "ul" ? "•" : `${idx + 1}.`;
          doc.setFont("helvetica", "bold");
          doc.setFontSize(10.5);
          doc.setTextColor(ORANGE);
          doc.text(bullet, MARGIN + 2, y + 10.5);
          y = drawStyledText(doc, item, MARGIN + 18, y + 10.5, CONTENT_W - 18, { size: 10.5, color: "#33415C" }) + 2;
        });
        y += 4;
      } else if (b.t === "quote") {
        const nLines = measureStyledLines(doc, b.text, CONTENT_W - 26, 10.5);
        ensureSpace(nLines * 15.2 + 10);
        doc.setFillColor(CREAM_M);
        doc.rect(MARGIN + 4, y + 2, 3, nLines * 15.2 - 4, "F");
        y = drawStyledText(doc, b.text, MARGIN + 18, y + 10.5, CONTENT_W - 26, { size: 10.5, color: GRAY, font: "times" }) + 6;
      } else {
        const nLines = measureStyledLines(doc, b.text, CONTENT_W, 10.5);
        ensureSpace(nLines * 15.2 + 6);
        y = drawStyledText(doc, b.text, MARGIN, y + 10.5, CONTENT_W, { size: 10.5, color: "#33415C" }) + 8;
      }
    }

    // 2. Media Content
    sectionHeading("2", "Media Content");
    ensureSpace(60);
    doc.setFont("helvetica", "italic");
    doc.setFontSize(9.5);
    doc.setTextColor(GRAY);
    doc.text("a. DALL-E Prompt", MARGIN, y + 4);
    y += 12;
    renderMediaBox("DALL-E Prompt", lesson.imagePrompt, BLUE_BG, BLUE_BORDER, BLUE_LABEL, "#1E3A5F");
    ensureSpace(30);
    doc.setFont("helvetica", "italic");
    doc.setFontSize(9.5);
    doc.setTextColor(GRAY);
    doc.text("b. Video Prompt", MARGIN, y + 4);
    y += 12;
    renderMediaBox("Video Prompt", lesson.videoPrompt, PINK_BG, PINK_BORDER, PINK_LABEL, "#5B2344");
  });

  // ── Sommaire : numéros de page réels + liens cliquables + bookmarks ──
  tocRows.forEach((row, i) => {
    row.target = startPages[i] || 1;
    doc.setPage(row.page);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10.5);
    doc.setTextColor(NAVY);
    try {
      doc.textWithLink(row.label, MARGIN, row.yPos + 10, { pageNumber: row.target });
      doc.setTextColor(GRAY);
      const pw = doc.getTextWidth(String(row.target));
      doc.textWithLink(String(row.target), PAGE_W - MARGIN - pw, row.yPos + 10, { pageNumber: row.target });
      doc.setDrawColor(CREAM_M);
      doc.setLineWidth(0.6);
      doc.line(MARGIN, row.yPos + 16, PAGE_W - MARGIN, row.yPos + 16);
    } catch { /* liens non supportés: sommaire lisible quand même */ }
    if (startPages[i]) {
      try { doc.outline.add(null, `${lessons[i].moduleTitle} › ${lessons[i].lessonTitle}`, startPages[i]); } catch {}
    }
  });

  // ── Pieds de page (hors couverture) ──
  const total = doc.getNumberOfPages();
  for (let p = 2; p <= total; p++) {
    doc.setPage(p);
    doc.setDrawColor(CREAM_M);
    doc.setLineWidth(0.8);
    doc.line(MARGIN, PAGE_H - 34, PAGE_W - MARGIN, PAGE_H - 34);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(GRAY);
    doc.text("EDUAI Learning · AI Factory", MARGIN, PAGE_H - 22);
    doc.text(`Page ${p} / ${total}`, PAGE_W - MARGIN, PAGE_H - 22, { align: "right" });
  }
  doc.setPage(total);
  return doc;
}

/** Génère et déclenche le téléchargement du PDF du batch courant. */
export function exportAIFactoryPdf(bundle: AIFactoryPdfBundle): void {
  buildAIFactoryPdf(bundle).save(aiFactoryExportFileName());
}
