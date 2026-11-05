/* The Embeddings & Vector Search Handbook — illustration site scripts.
   Vanilla JS, zero dependencies, zero network calls. */

"use strict";

/* ---------- shared helpers ---------- */
function $(id) { return document.getElementById(id); }

function cosineSim(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  if (na === 0 || nb === 0) return 0;
  return dot / Math.sqrt(na * nb);
}

function euclideanDist(a, b) {
  let s = 0;
  for (let i = 0; i < a.length; i++) { const d = a[i] - b[i]; s += d * d; }
  return Math.sqrt(s);
}

function setupCanvas(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  return { ctx, w: rect.width, h: rect.height };
}

/* ============================================================
   1. The meaning map — hand-crafted "fake embeddings" in 2D
   ============================================================ */

const MAP_POINTS = [
  // cooking cluster
  { x: 0.16, y: 0.80, c: "cooking", label: "sourdough starter feeding" },
  { x: 0.24, y: 0.74, c: "cooking", label: "why honey never spoils" },
  { x: 0.10, y: 0.69, c: "cooking", label: "knife skills: julienne" },
  { x: 0.21, y: 0.87, c: "cooking", label: "no-knead bread schedule" },
  // nursing cluster
  { x: 0.78, y: 0.78, c: "nursing", label: "apnea event at 0300" },
  { x: 0.86, y: 0.84, c: "nursing", label: "patient stopped breathing" },
  { x: 0.71, y: 0.69, c: "nursing", label: "med reconciliation handoff" },
  { x: 0.82, y: 0.66, c: "nursing", label: "fall-risk protocol update" },
  // chess cluster
  { x: 0.20, y: 0.26, c: "chess", label: "sicilian defense ideas" },
  { x: 0.28, y: 0.18, c: "chess", label: "punishing a fork blunder" },
  { x: 0.12, y: 0.16, c: "chess", label: "caro-kann pawn structures" },
  // privacy cluster
  { x: 0.76, y: 0.24, c: "privacy", label: "two-factor backup codes" },
  { x: 0.86, y: 0.30, c: "privacy", label: "why password managers pair well" },
  { x: 0.69, y: 0.15, c: "privacy", label: "metadata: what your phone leaks" },
];

const MAP_COLORS = {
  cooking: "#b98a2f",
  nursing: "#2f6f5e",
  chess:   "#6b5aa8",
  privacy: "#b3562d",
};

const embState = { hover: null, query: null };

function drawEmbMap() {
  const canvas = $("embMap");
  if (!canvas) return;
  const { ctx, w, h } = setupCanvas(canvas);

  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#fbfaf7";
  ctx.fillRect(0, 0, w, h);

  ctx.strokeStyle = "#eeeae2";
  ctx.lineWidth = 1;
  for (let i = 1; i < 8; i++) {
    ctx.beginPath(); ctx.moveTo((w / 8) * i, 0); ctx.lineTo((w / 8) * i, h); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, (h / 8) * i); ctx.lineTo(w, (h / 8) * i); ctx.stroke();
  }

  const px = (p) => p.x * w;
  const py = (p) => (1 - p.y) * h;

  for (const name of Object.keys(MAP_COLORS)) {
    const color = MAP_COLORS[name];
    const pts = MAP_POINTS.filter((p) => p.c === name);
    const cx = pts.reduce((s, p) => s + px(p), 0) / pts.length;
    const cy = pts.reduce((s, p) => s + py(p), 0) / pts.length;
    const r = Math.max(...pts.map((p) => Math.hypot(px(p) - cx, py(p) - cy))) + 26;
    ctx.fillStyle = color + "18";
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
  }

  if (embState.query) {
    const qx = embState.query.x * w;
    const qy = (1 - embState.query.y) * h;
    const dists = MAP_POINTS
      .map((p) => ({ p, d: Math.hypot(px(p) - qx, py(p) - qy) }))
      .sort((a, b) => a.d - b.d)
      .slice(0, 3);
    ctx.strokeStyle = "#2f6f5e";
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    for (const { p } of dists) {
      ctx.beginPath(); ctx.moveTo(qx, qy); ctx.lineTo(px(p), py(p)); ctx.stroke();
    }
    ctx.setLineDash([]);
    ctx.fillStyle = "#2f6f5e";
    ctx.beginPath(); ctx.arc(qx, qy, 9, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "bold 10px Georgia";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText("?", qx, qy);
  }

  for (const p of MAP_POINTS) {
    const hovered = embState.hover === p;
    ctx.fillStyle = MAP_COLORS[p.c];
    ctx.beginPath(); ctx.arc(px(p), py(p), hovered ? 10 : 7, 0, Math.PI * 2); ctx.fill();
    if (hovered) {
      ctx.strokeStyle = MAP_COLORS[p.c];
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(px(p), py(p), 15, 0, Math.PI * 2); ctx.stroke();
      ctx.font = "13px Georgia";
      ctx.fillStyle = "#1f2430";
      ctx.textAlign = "center";
      ctx.textBaseline = "alphabetic";
      ctx.fillText(`"${p.label}"`, px(p), py(p) - 24);
    }
  }
}

function initEmbMap() {
  const canvas = $("embMap");
  if (!canvas) return;
  canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    embState.hover = null;
    let best = 14;
    for (const p of MAP_POINTS) {
      const d = Math.hypot(p.x * rect.width - mx, (1 - p.y) * rect.height - my);
      if (d < best) { best = d; embState.hover = p; }
    }
    drawEmbMap();
  });
  canvas.addEventListener("mouseleave", () => { embState.hover = null; drawEmbMap(); });
  canvas.addEventListener("pointerdown", (e) => {
    const rect = canvas.getBoundingClientRect();
    embState.query = { x: (e.clientX - rect.left) / rect.width,
                       y: 1 - (e.clientY - rect.top) / rect.height };
    drawEmbMap();
    let nearest = null, nd = Infinity;
    for (const p of MAP_POINTS) {
      const d = Math.hypot(p.x - embState.query.x, p.y - embState.query.y);
      if (d < nd) { nd = d; nearest = p; }
    }
    if (nearest) {
      $("embExplain").classList.remove("hidden");
      $("embExplain").innerHTML =
        `Your query vector landed at (${embState.query.x.toFixed(2)}, ` +
        `${embState.query.y.toFixed(2)}). Nearest neighbor: ` +
        `<strong>&ldquo;${nearest.label}&rdquo;</strong> in the ` +
        `<strong>${nearest.c}</strong> neighborhood &mdash; so that is the ` +
        `chunk a similarity search would hand back first.`;
    }
  });
  drawEmbMap();
}

/* ============================================================
   2. Cosine similarity playground — drag two unit arrows
   ============================================================ */

const sim = { a: { deg: 30 }, b: { deg: 95 }, drag: null };

function simVec(deg) {
  const r = (deg * Math.PI) / 180;
  return { x: Math.cos(r), y: Math.sin(r) };
}

function drawSim() {
  const canvas = $("simCanvas");
  if (!canvas) return;
  const { ctx, w, h } = setupCanvas(canvas);
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#fbfaf7"; ctx.fillRect(0, 0, w, h);

  const cx = w / 2, cy = h / 2;
  const scale = Math.min(w, h) / 2 - 40;

  ctx.strokeStyle = "#d8d3c9"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(cx - scale - 20, cy); ctx.lineTo(cx + scale + 20, cy); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx, cy - scale - 20); ctx.lineTo(cx, cy + scale + 20); ctx.stroke();
  ctx.strokeStyle = "#eeeae2";
  ctx.beginPath(); ctx.arc(cx, cy, scale, 0, Math.PI * 2); ctx.stroke();

  const a1 = (sim.a.deg * Math.PI) / 180;
  const b1 = (sim.b.deg * Math.PI) / 180;
  ctx.fillStyle = "#2f6f5e22";
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, 46, Math.min(-a1, -b1), Math.max(-a1, -b1));
  ctx.closePath(); ctx.fill();

  const drawArrow = (deg, color, name) => {
    const v = simVec(deg);
    const ex = cx + v.x * scale, ey = cy - v.y * scale;
    ctx.strokeStyle = color; ctx.fillStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke();
    const ang = Math.atan2(ey - cy, ex - cx);
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - 12 * Math.cos(ang - 0.4), ey - 12 * Math.sin(ang - 0.4));
    ctx.lineTo(ex - 12 * Math.cos(ang + 0.4), ey - 12 * Math.sin(ang + 0.4));
    ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.arc(ex, ey, 10, 0, Math.PI * 2);
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.stroke();
    ctx.font = "12px Georgia"; ctx.fillStyle = color; ctx.textAlign = "center";
    ctx.fillText(name, cx + v.x * scale, cy - v.y * scale - 20);
  };

  drawArrow(sim.a.deg, "#2f6f5e", "vector A");
  drawArrow(sim.b.deg, "#b3562d", "vector B");
  updateSimStats();
}

function angleBetweenDegs() {
  let d = Math.abs(sim.a.deg - sim.b.deg) % 360;
  if (d > 180) d = 360 - d;
  return d;
}

function updateSimStats() {
  const vA = simVec(sim.a.deg);
  const vB = simVec(sim.b.deg);
  const a = [vA.x, vA.y];
  const b = [vB.x, vB.y];
  const cos = cosineSim(a, b);
  const dot = a[0] * b[0] + a[1] * b[1];
  const dist = euclideanDist(a, b);
  $("statCos").textContent = cos.toFixed(3);
  $("statDot").textContent = dot.toFixed(3);
  $("statDist").textContent = dist.toFixed(3);

  const rel = angleBetweenDegs();
  let meaning;
  if (rel < 12)      meaning = "Pointing the same way — like two recipes for the same soup.";
  else if (rel < 45) meaning = "Same neighborhood, different house — related topics.";
  else if (rel < 90) meaning = "Loosely related — they share a setting, not a subject. This is the zone where search results feel 'inspired but off'.";
  else if (rel < 150) meaning = "Barely related — a store would rank these last.";
  else               meaning = "Unrelated or roughly opposite — different boroughs of the meaning map.";
  $("statMeaning").textContent = meaning + " Angle between: " + rel.toFixed(0) + "\u00B0.";
  $("statNote").textContent =
    "Note: cos = dot here because both arrows are exactly length 1 (unit vectors), which is how most embedding models ship.";
}

function initSim() {
  const canvas = $("simCanvas");
  if (!canvas) return;

  canvas.addEventListener("pointerdown", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const cx = rect.width / 2, cy = rect.height / 2;
    const scale = Math.min(rect.width, rect.height) / 2 - 40;
    sim.drag = null;
    for (const key of ["a", "b"]) {
      const v = simVec(sim[key].deg);
      const kx = cx + v.x * scale, ky = cy - v.y * scale;
      if (Math.hypot(kx - mx, ky - my) < 18) { sim.drag = key; break; }
    }
    if (sim.drag) canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!sim.drag) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const cx = rect.width / 2, cy = rect.height / 2;
    let deg = (Math.atan2(cy - my, mx - cx) * 180) / Math.PI;
    if (deg < 0) deg += 360;
    sim[sim.drag].deg = deg;
    drawSim();
  });
  canvas.addEventListener("pointerup", () => { sim.drag = null; });

  const preset = (id, aDeg, bDeg) => {
    const b = $(id);
    if (b) b.addEventListener("click", () => { sim.a.deg = aDeg; sim.b.deg = bDeg; drawSim(); });
  };
  preset("btnPresetSame", 40, 52);
  preset("btnPresetUnrelated", 25, 160);
  preset("btnPresetOpposite", 30, 200);

  drawSim();
}

/* ============================================================
   3. Similar texts ↔ close vectors (illustrative scores)
   ============================================================ */

const TEXT_PAIRS = [
  { b: "Apnea event noted at 0300",
    s: 0.86,
    note: "Different words, same meaning — where embeddings shine." },
  { b: "Patient stopped taking insulin overnight",
    s: 0.51,
    note: "Shares words, misses meaning — the trap for keyword search." },
  { b: "Chocolate babka recipe, day 3 rise",
    s: 0.04,
    note: "Nothing in common; the model keeps them far apart." },
];

function renderTextPairs() {
  const host = $("textPairs");
  if (!host) return;
  for (const t of TEXT_PAIRS) {
    const row = document.createElement("tr");
    const other = document.createElement("td");
    other.innerHTML = `<span class="mono">&ldquo;${t.b}&rdquo;</span>`;
    const scoreCell = document.createElement("td");
    scoreCell.innerHTML =
      `<span class="bar" style="width:${Math.round(t.s * 90)}px"></span> ` +
      t.s.toFixed(2);
    const note = document.createElement("td");
    note.textContent = t.note;
    note.className = "muted";
    row.appendChild(other); row.appendChild(scoreCell); row.appendChild(note);
    host.appendChild(row);
  }
}

/* ============================================================
   4. Chunking visualizer — a real seam-aware chunker, in-browser
   ============================================================ */

const SAMPLE_DOC =
`## Refunds

We accept returns within 30 days of delivery. Items must be unused and in
original packaging. Gift cards and digital downloads are final sale and
cannot be refunded once the code has been redeemed.

## Shipping

Orders ship within 2 business days. Some remote addresses may take an extra
week. If your package is marked delivered but never arrived, wait 3 days,
then contact us with your order number.

## Loyalty program

Every dollar spent earns one point. Every one hundred points converts to a
five-dollar credit at checkout. Points expire after 24 months of no orders.`;

function splitParagraphs(text) {
  return text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
}

function chunkBySeams(text, maxChars, overlapChars) {
  const paras = splitParagraphs(text);
  const chunks = [];
  let cur = "";
  const flush = () => { if (cur.trim()) { chunks.push(cur.trim()); cur = ""; } };

  for (const para of paras) {
    if (para.length > maxChars) {
      flush();
      const sentences = para.match(/[^.!?]+[.!?]+(\s|$)|[^.!?]+$/g) || [para];
      let s = "";
      for (const sent of sentences) {
        if ((s + sent).length > maxChars && s.length > 0) {
          chunks.push(s.trim());
          s = s.slice(Math.max(0, s.length - overlapChars));
        }
        s += sent;
      }
      if (s.trim()) chunks.push(s.trim());
      continue;
    }
    if ((cur + "\n\n" + para).length > maxChars && cur.length > 0) flush();
    cur = cur ? (cur + "\n\n" + para) : para;
  }
  if (cur.trim()) chunks.push(cur.trim());

  // append a short overlap tail from the previous chunk, as real chunkers do
  const withOverlap = [];
  for (let i = 0; i < chunks.length; i++) {
    const tail = i > 0 ? chunks[i - 1].slice(Math.max(0, chunks[i - 1].length - overlapChars)).trim() : "";
    withOverlap.push(tail ? (tail + " \u2026 " + chunks[i]) : chunks[i]);
  }
  return withOverlap;
}

function wordCount(s) { return s.replace(/\s+/g, " ").trim().split(" ").length; }
function isOrphan(chunk) { return wordCount(chunk) < 25; }

function renderChunks() {
  const out = $("chunkOutput");
  if (!out) return;
  const maxChars = parseInt($("chunkSize").value, 10);
  const overlap = Math.round(maxChars * 0.15);
  $("chunkSizeVal").textContent = maxChars + " chars max, " + overlap + " overlap";
  const chunks = chunkBySeams(SAMPLE_DOC, maxChars, overlap);

  out.innerHTML = "";
  let orphans = 0;
  chunks.forEach((c, i) => {
    const orphan = isOrphan(c);
    if (orphan) orphans++;
    const box = document.createElement("div");
    box.className = "chunk-box" + (orphan ? " orphan" : "");
    const head = document.createElement("div");
    head.className = "muted";
    head.textContent =
      `chunk ${i + 1} \u00B7 ${c.length} chars` +
      (orphan ? " \u00B7 orphan (short, thin meaning on its own)" : "");
    const body = document.createElement("div");
    body.textContent = c;
    box.appendChild(head); box.appendChild(body);
    out.appendChild(box);
  });

  $("chunkStats").textContent =
    `${chunks.length} chunks, ${orphans} orphaned, from ${SAMPLE_DOC.length} ` +
    `chars of source. Every chunk becomes exactly one vector. Watch what ` +
    `happens to the section boundaries as you slide: too small and the ` +
    `chunks lose their topic; just right and each chunk is one whole subject.`;
}

function initChunks() {
  const slider = $("chunkSize");
  if (!slider) return;
  slider.addEventListener("input", renderChunks);
  renderChunks();
}

/* ============================================================
   5. "Is RAG overkill?" decision flow
   ============================================================ */

const FLOW = {
  start: {
    q: "How big is your document collection, roughly?",
    opts: [
      { label: "One document (up to a few dozen pages)", go: "one" },
      { label: "A folder of files (a handful to a few dozen)", go: "folder" },
      { label: "Hundreds of docs, or it keeps growing", go: "big" },
    ],
  },
  one: {
    q: "Do you need to find facts, or answer open questions?",
    opts: [
      { label: "Find facts (I know roughly what I'm looking for)", go: "verdictControlF" },
      { label: "Free-form natural questions about it", go: "verdictPaste" },
    ],
  },
  folder: {
    q: "Do your queries tend to use the same words the documents use?",
    opts: [
      { label: "Usually yes (names, product codes, my own phrasing)", go: "verdictFTS" },
      { label: "Not reliably (other people's wording, flaky OCR)", go: "verdictRAG" },
    ],
  },
  big: {
    q: "Does one answer usually need just one document, or several mixed?",
    opts: [
      { label: "One document, and filenames are honest", go: "verdictTitles" },
      { label: "Several, in predictable ways", go: "verdictRAG" },
      { label: "Several, unpredictably, and it keeps growing", go: "verdictRAGdef" },
    ],
  },
  verdictPaste: {
    verdict: ["Paste it into the context window.",
      "When the whole corpus fits, retrieval is pure overhead: the model sees everything, and no chunk boundary can ever be wrong. The simplest correct system wins.", "green"],
  },
  verdictControlF: {
    verdict: ["Ctrl+F — you already have the database.",
      "Keyword search is exact, honest, and free. If you can phrase your query in the document's own words, you don't need embeddings for this job.", "green"],
  },
  verdictFTS: {
    verdict: ["SQLite full-text search (FTS5).",
      "Same storage layer as the vector chapters, zero models. If wording drift later becomes real, this is the natural place to add a small vector layer.", "green"],
  },
  verdictTitles: {
    verdict: ["Honest filenames plus a titles table.",
      "For a bounded set of docs, curation beats infrastructure: read what you have, keep a title+summary index, and skip the pipeline entirely.", "green"],
  },
  verdictRAG: {
    verdict: ["Real RAG case — start small and boring.",
      "Seam-aware chunking, one model, one collection, cosine search. Add the fancy machinery (rerankers, hybrid retrieval) only after the boring version is boringly correct.", "amber"],
  },
  verdictRAGdef: {
    verdict: ["Textbook RAG territory.",
      "An unbounded, unpredictable corpus is exactly what similarity search is for. Keep chunk quality your north star (Chapter 4), and always show retrieved sources.", "amber"],
  },
};

let currentKey = "start";
let backStack = [];

function showNode(host, key) {
  currentKey = key;
  const node = FLOW[key];
  let html = "";
  if (node.verdict) {
    const [fat, why] = node.verdict;
    html += `<div class="verdict"><span class="fat">${fat}</span>${why}</div>`;
    html += `<button class="option" data-go="start">Start over</button>`;
  } else {
    html += `<div class="question"><strong>${node.q}</strong></div>`;
    html += `<div class="options">`;
    for (const o of node.opts) {
      html += `<button class="option" data-go="${o.go}">${o.label}</button>`;
    }
    html += `</div>`;
  }
  host.innerHTML = html;

  host.querySelectorAll("button[data-go]").forEach((b) => {
    b.addEventListener("click", () => {
      if (currentKey !== "start" && FLOW[currentKey] && !FLOW[currentKey].verdict) {
        backStack.push(currentKey);
      }
      if (b.dataset.go === "start") backStack = [];
      showNode(host, b.dataset.go);
      syncBack(host);
    });
  });
}

function syncBack(host) {
  let back = $("btnBack");
  if (!back) {
    back = document.createElement("button");
    back.id = "btnBack";
    back.className = "secondary";
    back.textContent = "\u2190 one question back";
    back.addEventListener("click", () => {
      if (backStack.length) {
        showNode(host, backStack.pop());
        syncBack(host);
      }
    });
    host.appendChild(back);
  }
  back.classList.toggle("hidden", backStack.length === 0);
}

function initFlow() {
  const host = $("decision");
  if (!host) return;
  backStack = [];
  showNode(host, "start");
  syncBack(host);
}

/* ============================================================
   boot
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  initEmbMap();
  initSim();
  renderTextPairs();
  initChunks();
  initFlow();
  window.addEventListener("resize", () => {
    drawEmbMap();
    drawSim();
  });
});
