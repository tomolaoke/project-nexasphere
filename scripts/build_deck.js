const pptxgen = require("pptxgenjs");

const NAVY = "0B1229";
const NAVY2 = "141B36";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const ACCENT = "4C8DFF";
const ACCENT2 = "35D0A6";
const WARN = "F2A93B";
const MUTED = "8C97B8";
const CARD = "1B2444";

function newDeck() {
  const p = new pptxgen();
  p.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
  p.defineSlideMaster({
    title: "DARK",
    background: { color: NAVY },
  });
  return p;
}

const pres = newDeck();

function darkSlide() {
  const s = pres.addSlide({ masterName: "DARK" });
  return s;
}

function kicker(s, text, opts = {}) {
  s.addText(text.toUpperCase(), {
    x: 0.6, y: opts.y ?? 0.5, w: 8, h: 0.4,
    fontFace: "Calibri", fontSize: 13, bold: true, color: ACCENT2,
    charSpacing: 2, isTextBox: true, margin: 0,
  });
}

function pageNum(s, n) {
  s.addText(String(n).padStart(2, "0"), {
    x: 12.5, y: 6.95, w: 0.6, h: 0.35, fontFace: "Calibri", fontSize: 10,
    color: MUTED, align: "right", isTextBox: true, margin: 0,
  });
}

// ---------------------------------------------------------------------
// Slide 1 — Title
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  s.addShape(pres.ShapeType.ellipse, { x: 9.6, y: -2.2, w: 6, h: 6, fill: { color: NAVY2 }, line: { type: "none" } });
  s.addShape(pres.ShapeType.ellipse, { x: 11.6, y: 4.3, w: 4, h: 4, fill: { color: CARD }, line: { type: "none" } });

  s.addText("AI BUILDFEST 2026  ·  TRACK 1: AI FOR BUSINESS & PRODUCTIVITY  ·  CASE STUDY 4", {
    x: 0.9, y: 1.35, w: 10.5, h: 0.4, fontFace: "Calibri", fontSize: 13, bold: true,
    color: ACCENT2, charSpacing: 1.5, isTextBox: true, margin: 0,
  });
  s.addText("Ordino", {
    x: 0.85, y: 1.9, w: 10.5, h: 1.3, fontFace: "Cambria", fontSize: 60, bold: true,
    color: WHITE, isTextBox: true, margin: 0,
  });
  s.addText("AI Business Intelligence Assistant", {
    x: 0.9, y: 3.05, w: 10.5, h: 0.7, fontFace: "Calibri", fontSize: 26, color: ICE,
    isTextBox: true, margin: 0,
  });
  s.addText("Turning disconnected retail data into decisions worth acting on.", {
    x: 0.9, y: 3.75, w: 9.5, h: 0.6, fontFace: "Calibri", fontSize: 16, italic: true,
    color: MUTED, isTextBox: true, margin: 0,
  });

  s.addShape(pres.ShapeType.rect, { x: 0.9, y: 4.7, w: 0.55, h: 0.55, fill: { color: ACCENT }, line: { type: "none" }, rectRadius: 0.12 });
  s.addText("TO", { x: 0.9, y: 4.7, w: 0.55, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 14, bold: true, color: WHITE, isTextBox: true, margin: 0 });
  s.addText([
    { text: "Built by Tomola Oke", options: { bold: true, color: WHITE, breakLine: true } },
    { text: "Solo builder · AI Systems & Product Engineer", options: { color: MUTED } },
  ], { x: 1.6, y: 4.68, w: 6, h: 0.6, fontFace: "Calibri", fontSize: 13, isTextBox: true, margin: 0 });

  s.addText("$0 BUDGET  ·  100% FREE & OPEN-SOURCE STACK", {
    x: 0.9, y: 6.55, w: 8, h: 0.35, fontFace: "Calibri", fontSize: 11, bold: true,
    color: ACCENT2, charSpacing: 1.5, isTextBox: true, margin: 0,
  });
}

// ---------------------------------------------------------------------
// Slide 2 — The Problem
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  kicker(s, "The Problem");
  s.addText("Revenue can grow while profit\nquietly doesn't.", {
    x: 0.6, y: 0.95, w: 7.3, h: 1.7, fontFace: "Cambria", fontSize: 34, bold: true,
    color: WHITE, isTextBox: true, margin: 0,
  });

  const items = [
    ["Data is scattered", "Sales, returns, delivery, inventory and marketing data live in separate systems management has to manually connect."],
    ["Every question starts from zero", "Answering 'why did this number move?' takes 30-60+ minutes of manual cross-referencing - every single time."],
    ["Dashboards show numbers, not reasons", "Traditional BI tells a manager what happened. It doesn't explain why, or what to do next."],
  ];
  let y = 2.85;
  items.forEach(([h, body], i) => {
    s.addShape(pres.ShapeType.roundRect, { x: 0.6, y, w: 12.1, h: 1.25, fill: { color: CARD }, line: { type: "none" }, rectRadius: 0.08 });
    s.addShape(pres.ShapeType.ellipse, { x: 0.9, y: y + 0.32, w: 0.6, h: 0.6, fill: { color: ACCENT }, line: { type: "none" } });
    s.addText(String(i + 1), { x: 0.9, y: y + 0.32, w: 0.6, h: 0.6, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 20, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText(h, { x: 1.75, y: y + 0.14, w: 10.6, h: 0.4, fontFace: "Calibri", fontSize: 17, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText(body, { x: 1.75, y: y + 0.55, w: 10.6, h: 0.6, fontFace: "Calibri", fontSize: 13, color: ICE, isTextBox: true, margin: 0 });
    y += 1.4;
  });
  pageNum(s, 2);
}

// ---------------------------------------------------------------------
// Slide 3 — Cost of the Problem
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  kicker(s, "The Cost of the Problem");
  s.addText("These signals already exist in the data.\nNobody is looking at all of them at once.", {
    x: 0.6, y: 0.95, w: 12, h: 1.2, fontFace: "Cambria", fontSize: 24, bold: true,
    color: WHITE, isTextBox: true, margin: 0,
  });

  const stats = [
    { big: "+63.2%", small: "revenue, last 30 days", sub: "but gross profit grew only +53.8% - margin fell -1.45pp", color: WARN },
    { big: "12.77%", small: "Audio return rate", sub: "891 units returned - ₦294,656.64 refunded", color: ACCENT },
    { big: "34.0%", small: "UrbanMove delayed rate", sub: "vs. ~7.8% average across the other delivery partners", color: "E8595B" },
  ];
  let x = 0.6;
  stats.forEach((st) => {
    s.addShape(pres.ShapeType.roundRect, { x, y: 2.55, w: 3.95, h: 3.5, fill: { color: CARD }, line: { type: "none" }, rectRadius: 0.1 });
    s.addText(st.big, { x: x + 0.25, y: 2.85, w: 3.45, h: 1.0, fontFace: "Cambria", fontSize: 44, bold: true, color: st.color, isTextBox: true, margin: 0 });
    s.addText(st.small, { x: x + 0.25, y: 3.85, w: 3.45, h: 0.5, fontFace: "Calibri", fontSize: 15, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText(st.sub, { x: x + 0.25, y: 4.35, w: 3.5, h: 1.5, fontFace: "Calibri", fontSize: 12, color: MUTED, isTextBox: true, margin: 0 });
    x += 4.2;
  });
  pageNum(s, 3);
}

// ---------------------------------------------------------------------
// Slide 4 — Our Insight
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  kicker(s, "Our Insight");
  s.addText("The gap isn't data. It's interpretation speed.", {
    x: 0.6, y: 0.95, w: 12, h: 0.9, fontFace: "Cambria", fontSize: 30, bold: true,
    color: WHITE, isTextBox: true, margin: 0,
  });

  function flow(y, label, steps, stepColor) {
    s.addText(label, { x: 0.6, y, w: 3, h: 0.4, fontFace: "Calibri", fontSize: 13, bold: true, color: MUTED, charSpacing: 1, isTextBox: true, margin: 0 });
    let x = 0.6;
    const w = 2.15;
    steps.forEach((txt, i) => {
      s.addShape(pres.ShapeType.roundRect, { x, y: y + 0.5, w, h: 0.95, fill: { color: CARD }, line: { color: stepColor, width: 1 }, rectRadius: 0.08 });
      s.addText(txt, { x: x + 0.08, y: y + 0.5, w: w - 0.16, h: 0.95, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 11, color: WHITE, isTextBox: true, margin: 0 });
      if (i < steps.length - 1) {
        s.addText("→", { x: x + w, y: y + 0.72, w: 0.35, h: 0.5, align: "center", fontFace: "Calibri", fontSize: 18, bold: true, color: stepColor, isTextBox: true, margin: 0 });
      }
      x += w + 0.35;
    });
  }

  flow(2.15, "TRADITIONAL BI  (SLOW)", ["Database", "Dashboard", "Human\ninterprets", "Human\ndecides"], MUTED);
  flow(4.15, "ORDINO  (FAST + SAFE)", ["Business\ndata", "Analytics\nengine", "Verified\nmetrics", "AI\nexplains", "Human\ndecides"], ACCENT2);

  s.addText("Same destination - a human decision - reached through verified evidence instead of manual detective work.", {
    x: 0.6, y: 6.3, w: 11.8, h: 0.6, fontFace: "Calibri", fontSize: 14, italic: true, color: ICE, isTextBox: true, margin: 0,
  });
  pageNum(s, 4);
}

// ---------------------------------------------------------------------
// Slide 5 — Our Solution
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  kicker(s, "Our Solution");
  s.addText("Ordino AI Business Intelligence Assistant", {
    x: 0.6, y: 0.95, w: 12, h: 0.7, fontFace: "Cambria", fontSize: 28, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });
  s.addText("Every number on screen is traceable to a deterministic calculation.", {
    x: 0.6, y: 1.6, w: 12, h: 0.5, fontFace: "Calibri", fontSize: 15, italic: true, color: MUTED, isTextBox: true, margin: 0,
  });

  const cols = [
    { title: "Discover", tag: "AUTOMATIC", color: ACCENT2, body: "Six ranked findings generated fresh from live data every time the app opens - profitability, returns, delivery, inventory, marketing, targets - each with its evidence attached." },
    { title: "Ask", tag: "ON DEMAND", color: ACCENT, body: "Type a business question in plain English. The system matches it to a verified analysis, computes the answer live, and explains it - or says honestly it can't." },
  ];
  let x = 0.6;
  cols.forEach((c) => {
    s.addShape(pres.ShapeType.roundRect, { x, y: 2.4, w: 5.9, h: 4.1, fill: { color: CARD }, line: { type: "none" }, rectRadius: 0.1 });
    s.addText(c.tag, { x: x + 0.35, y: 2.65, w: 4, h: 0.35, fontFace: "Calibri", fontSize: 11, bold: true, color: c.color, charSpacing: 1.5, isTextBox: true, margin: 0 });
    s.addText(c.title, { x: x + 0.35, y: 2.98, w: 5, h: 0.6, fontFace: "Cambria", fontSize: 26, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText(c.body, { x: x + 0.35, y: 3.7, w: 5.2, h: 2.5, fontFace: "Calibri", fontSize: 14, color: ICE, isTextBox: true, margin: 0, lineSpacingMultiple: 1.15 });
    x += 6.2;
  });
  pageNum(s, 5);
}

// ---------------------------------------------------------------------
// Slide 6 — How It Works
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  kicker(s, "How It Works");
  s.addText("The AI never calculates. It only explains numbers a\ncalculator already verified.", {
    x: 0.6, y: 0.95, w: 12, h: 1.1, fontFace: "Cambria", fontSize: 24, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });

  const steps = [
    { t: "Business Data", d: "sales, returns,\ndelivery, inventory,\nmarketing (CSV)", c: MUTED },
    { t: "Analytics Engine", d: "pandas - \ndeterministic,\nunit-tested", c: ACCENT },
    { t: "Insight Engine", d: "ranks findings,\ncites evidence", c: ACCENT },
    { t: "AI Narration", d: "local open-source\nLLM (Ollama) or\nsafe template", c: ACCENT2 },
    { t: "Dashboard", d: "Streamlit UI - \nFindings + Ask +\nCharts", c: ACCENT2 },
  ];
  const w = 2.15, gap = 0.28;
  let x = 0.6;
  const y = 2.5;
  steps.forEach((st, i) => {
    s.addShape(pres.ShapeType.roundRect, { x, y, w, h: 2.0, fill: { color: CARD }, line: { color: st.c, width: 1.25 }, rectRadius: 0.09 });
    s.addText(st.t, { x: x + 0.12, y: y + 0.18, w: w - 0.24, h: 0.6, fontFace: "Calibri", fontSize: 14, bold: true, color: WHITE, align: "center", isTextBox: true, margin: 0 });
    s.addText(st.d, { x: x + 0.12, y: y + 0.85, w: w - 0.24, h: 1.05, fontFace: "Calibri", fontSize: 11, color: MUTED, align: "center", isTextBox: true, margin: 0 });
    if (i < steps.length - 1) {
      s.addText("→", { x: x + w, y: y + 0.75, w: gap, h: 0.5, align: "center", fontFace: "Calibri", fontSize: 20, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
    }
    x += w + gap;
  });

  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 5.05, w: 12.1, h: 1.15, fill: { color: NAVY2 }, line: { color: ACCENT2, width: 1 }, rectRadius: 0.08 });
  s.addText("Analytics never imports the AI layer, and the AI layer never sees raw data - only already-verified evidence. This is enforced in code and covered by automated tests, not just described in a prompt.", {
    x: 0.95, y: 5.2, w: 11.4, h: 0.85, fontFace: "Calibri", fontSize: 13, italic: true, color: ICE, valign: "middle", isTextBox: true, margin: 0,
  });
  pageNum(s, 6);
}

// ---------------------------------------------------------------------
// Slide 7 — Why AI, Why Different
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  kicker(s, "Why This Is Different");
  s.addText("Not another 'chat with your CSV.'", {
    x: 0.6, y: 0.95, w: 12, h: 0.8, fontFace: "Cambria", fontSize: 30, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });

  const rows = [
    ["Numeric-grounding guardrail", "Every AI-generated sentence is checked against the verified evidence. Any sentence with an unsupported number is discarded and replaced automatically - no exceptions."],
    ["$0 cost, no vendor lock-in", "Runs on Python, pandas, Streamlit and a local open-source LLM (Ollama). No API keys, no usage caps, no paid tier to outgrow."],
    ["Works with zero setup", "If a local LLM isn't installed, the system falls back to a deterministic, evidence-only template - nothing breaks, nothing degrades to guessing."],
  ];
  let y = 2.15;
  rows.forEach(([h, b]) => {
    s.addShape(pres.ShapeType.roundRect, { x: 0.6, y, w: 0.14, h: 1.25, fill: { color: ACCENT2 }, line: { type: "none" } });
    s.addText(h, { x: 1.05, y: y - 0.05, w: 11, h: 0.45, fontFace: "Calibri", fontSize: 18, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText(b, { x: 1.05, y: y + 0.42, w: 11.2, h: 0.75, fontFace: "Calibri", fontSize: 14, color: ICE, isTextBox: true, margin: 0 });
    y += 1.45;
  });
  pageNum(s, 7);
}

// ---------------------------------------------------------------------
// Slide 8 — Responsible AI
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  kicker(s, "Responsible AI");
  s.addText("Trustworthy by construction, not by promise.", {
    x: 0.6, y: 0.95, w: 12, h: 0.8, fontFace: "Cambria", fontSize: 28, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });

  const cards = [
    ["No hallucinated numbers", "Enforced in code via a numeric-grounding check - not just a prompt instruction."],
    ["Every claim cites evidence", "Findings and answers show the exact computed values they're based on."],
    ["Recommends, never executes", "The system flags what to investigate. A human decides and acts - always."],
    ["Fully transparent sourcing", "Every sentence is labeled: produced by the AI, or by the safe template."],
  ];
  let x = 0.6, y = 2.25;
  cards.forEach((c, i) => {
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 5.9, h: 1.95, fill: { color: CARD }, line: { type: "none" }, rectRadius: 0.09 });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.3, y: y + 0.3, w: 0.5, h: 0.5, fill: { color: ACCENT2 }, line: { type: "none" } });
    s.addText("✓", { x: x + 0.3, y: y + 0.3, w: 0.5, h: 0.5, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    s.addText(c[0], { x: x + 0.95, y: y + 0.24, w: 4.7, h: 0.5, fontFace: "Calibri", fontSize: 16, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText(c[1], { x: x + 0.3, y: y + 0.95, w: 5.35, h: 0.9, fontFace: "Calibri", fontSize: 12.5, color: ICE, isTextBox: true, margin: 0 });
    x += 6.2;
    if (i === 1) { x = 0.6; y += 2.15; }
  });
  pageNum(s, 8);
}

// ---------------------------------------------------------------------
// Slide 9 — Business Impact
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  kicker(s, "Demonstrated Impact");
  s.addText("Minutes, not hours - and every number checked.", {
    x: 0.6, y: 0.95, w: 12, h: 0.8, fontFace: "Cambria", fontSize: 28, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });

  s.addChart(pres.ChartType.bar, [
    {
      name: "Minutes per business question",
      labels: ["Manual spreadsheet\ncross-referencing", "Ordino\n(Discover / Ask)"],
      values: [45, 0.5],
    },
  ], {
    x: 0.6, y: 2.1, w: 5.7, h: 3.4,
    barDir: "bar",
    showTitle: true, title: "Time per business question (minutes)", titleColor: WHITE, titleFontSize: 13,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: WHITE, dataLabelFontSize: 12,
    chartColors: [ACCENT2],
    catAxisLabelColor: ICE, catAxisLabelFontSize: 11,
    valAxisLabelColor: MUTED, valAxisHidden: false,
    valGridLine: { color: "2A3358", size: 0.75 },
    catGridLine: { style: "none" },
    showLegend: false,
    plotArea: { fill: { color: NAVY } },
    chartArea: { fill: { color: NAVY } },
  });

  const bullets = [
    "22 automated tests validate every KPI against an independently pre-computed ground truth - not eyeballed",
    "All nine required business questions from the case study answerable end-to-end",
    "Applicable far beyond retail: e-commerce, logistics, manufacturing, financial services - anywhere structured operational data outpaces analyst time",
  ];
  s.addText(bullets.map((b, i) => ({ text: b, options: { bullet: { code: "25AA" }, breakLine: i < bullets.length - 1, paraSpaceAfter: 14 } })), {
    x: 6.7, y: 2.25, w: 6.0, h: 3.4, fontFace: "Calibri", fontSize: 14, color: ICE, isTextBox: true, margin: 0, valign: "top",
  });
  pageNum(s, 9);
}

// ---------------------------------------------------------------------
// Slide 10 — Closing
// ---------------------------------------------------------------------
{
  const s = darkSlide();
  s.addShape(pres.ShapeType.ellipse, { x: -2, y: -2.5, w: 6, h: 6, fill: { color: NAVY2 }, line: { type: "none" } });

  s.addText("Ordino", {
    x: 0.9, y: 2.0, w: 11.5, h: 1.0, fontFace: "Cambria", fontSize: 42, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });
  s.addText("Turning scattered business data into decisions worth acting on.", {
    x: 0.9, y: 2.95, w: 11, h: 0.7, fontFace: "Calibri", fontSize: 20, color: ICE, isTextBox: true, margin: 0,
  });

  s.addShape(pres.ShapeType.roundRect, { x: 0.9, y: 4.0, w: 11.4, h: 1.0, fill: { color: CARD }, line: { type: "none" }, rectRadius: 0.09 });
  s.addText("Built solo for AI BuildFest 2026  ·  100% free & open-source stack  ·  $0 total cost", {
    x: 0.9, y: 4.0, w: 11.4, h: 1.0, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 15, bold: true, color: ACCENT2, isTextBox: true, margin: 0,
  });

  s.addText("Thank you - questions welcome.", {
    x: 0.9, y: 5.5, w: 10, h: 0.6, fontFace: "Calibri", fontSize: 18, italic: true, color: MUTED, isTextBox: true, margin: 0,
  });
  s.addText("Tomola Oke", {
    x: 0.9, y: 6.6, w: 6, h: 0.4, fontFace: "Calibri", fontSize: 13, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });
}

pres.writeFile({ fileName: "docs/pitch-deck/Ordino-Pitch-Deck.pptx" }).then(() => {
  console.log("Deck written.");
});
