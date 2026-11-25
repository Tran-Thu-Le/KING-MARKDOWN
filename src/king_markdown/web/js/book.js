// book.js - View Book: dàn trang như sách. Section → tiêu đề, node → thẻ có meta, nội dung, link.
// Node có show=none không hiện (đúng nghĩa "có trong đồ thị, không hiện trong sách").
// @ref: id trong file, module.id, hoặc tên ngắn của node import lẻ (lop11.tiep-tuyen viết @tiep-tuyen)
const findRef = r => S.byId[r] || S.graph.nodes.find(n => n.kind === "external" && n.id.endsWith("." + r));
function mdInline(s) {
  let out = "", last = 0;
  const re = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*\s][^*]*\*)|(\[[^\]]+\]\([^)\s]+\))|(https?:\/\/[^\s)]+)|((?:^|(?<=\s))@[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)?)/g;
  for (const m of s.matchAll(re)) {
    out += esc(s.slice(last, m.index)); last = m.index + m[0].length;
    const t = m[0];
    if (m[1]) out += `<code>${esc(t.slice(1, -1))}</code>`;
    else if (m[2]) out += `<strong>${esc(t.slice(2, -2))}</strong>`;
    else if (m[3]) out += `<em>${esc(t.slice(1, -1))}</em>`;
    else if (m[4]) { const k = t.match(/^\[([^\]]+)\]\(([^)]+)\)$/); out += `<a href="${esc(k[2])}" target="_blank" rel="noopener">${esc(k[1])}</a>`; }
    else if (m[5]) out += `<a href="${esc(t)}" target="_blank" rel="noopener">${esc(t)}</a>`;
    else { const n = findRef(t.slice(1)), id = n ? n.id : t.slice(1); out += `<a data-go="${esc(id)}">${esc(n ? n.title || id : t)}</a>`; }
  }
  return out + esc(s.slice(last));
}
function mdCells(row) {            // "| a | b \| c |" → ["a", "b | c"]
  return row.trim().replace(/^\||\|$/g, "").split(/(?<!\\)\|/).map(c => c.trim().replace(/\\\|/g, "|"));
}
// Token role → CSS class. KING 0.3 (Text view, editor.js) and kir v0.4 fences share this map and the t-* classes
// in app.css (same palette as the VS Code `king` theme), so the two highlighters stay in sync.
const KING_TOK = {kw: "t-kw", link: "t-link", name: "t-id", value: "t-str", com: "t-com", fm: "t-key", variable: "t-type", punct: "t-punct"};
const KING_CMD = /^@(?:add|ask|block|print|world|import|use)\b/;   // kir rule: a line is a command only if it starts with @cmd at column 0
function hlKing(code, st) {         // ```king fence / whole kg: v0.4 file; st carries state across calls (the Text view passes one line at a time)
  const tok = /("(?:[^"\\]|\\.)*")|(\/\/.*)|(@[a-z]+\b)|(\?[A-Za-z_][\w-]*|\b_\b|\bvar\.[\w.-]+)|(-?\b\d+(?:\.\d+)?\b|\b(?:true|false|none)\b)|(=)|([()])|\b(and|or|not)\b|([A-Za-z_][\w.-]*)/g;
  const span = (r, t) => `<span class="${KING_TOK[r]}">${esc(t)}</span>`;
  st = st || {};
  return code.split("\n").map(line => {
    const first = !st.seen; st.seen = true;
    if (st.inner) { if (/^\s*(```|~~~)/.test(line)) st.inner = false; return esc(line); }   // body of @block: left as is
    if (/^\s*---\s*$/.test(line) && (first || st.fm)) { st.fm = !st.fm; return span("fm", line); }
    if (st.fm) { const m = line.match(/^(\s*[\w-]+\s*:)(.*)$/); return m ? span("fm", m[1]) + span("value", m[2]) : esc(line); }
    if (/^(```|~~~)/.test(line)) { st.inner = true; return esc(line); }
    if (!KING_CMD.test(line)) return esc(line);                                            // prose
    const cmd = line.match(KING_CMD)[0], print = cmd === "@print", triple = cmd === "@add" || cmd === "@ask";
    const parts = []; let last = 0, run = [];
    const end = () => { if ((triple && run.length > 1) || (print && run.length === 3)) { const t = parts[run[1]]; if (t.r === "name") t.r = "link"; } run = []; };
    for (const m of line.matchAll(tok)) {
      parts.push({r: null, t: line.slice(last, m.index)}); last = m.index + m[0].length;
      let r;
      if (m[2]) r = "com";                                                 // // only outside strings (strings match first)
      else if (m[3]) r = "kw";
      else if (m[6]) { r = "link"; end(); }                                // "p =": name the statement, restart s r o
      else if (m[7]) { r = "punct"; end(); }
      else if (m[8] && print) { r = "kw"; end(); }                         // and / or / not inside @print
      else r = m[1] || m[5] ? "value" : m[4] ? "variable" : cmd === "@world" ? "value" : "name";
      parts.push({r, t: m[0]});
      if (["value", "variable", "name"].includes(r)) run.push(parts.length - 1);
    }
    end();
    return parts.map(p => p.r ? span(p.r, p.t) : esc(p.t)).join("") + esc(line.slice(last));
  }).join("\n");
}
function mdBlock(text) {
  const out = []; let para = [], list = [], table = [], code = null, lang = "";
  const flush = () => {
    if (para.length) out.push(`<p>${mdInline(para.join(" "))}</p>`);
    if (list.length) out.push(`<ul>${list.map(x => `<li>${mdInline(x)}</li>`).join("")}</ul>`);
    if (table.length) {              // bảng Markdown: dòng đầu là tiêu đề, bỏ dòng |---|
      const rows = table.filter(r => !/^\s*\|?\s*:?-{2,}/.test(r)).map(mdCells);
      out.push(`<table><thead><tr>${rows[0].map(c => `<th>${mdInline(c)}</th>`).join("")}</tr></thead><tbody>` +
        rows.slice(1).map(r => `<tr>${r.map(c => `<td>${mdInline(c)}</td>`).join("")}</tr>`).join("") + "</tbody></table>");
    }
    para = []; list = []; table = [];
  };
  const pre = lines => {             // bỏ phần thụt lề chung của khối code
    const ind = Math.min(...lines.filter(l => l.trim()).map(l => l.match(/^\s*/)[0].length), 99);
    const body = lines.map(l => l.slice(ind)).join("\n");
    return lang === "king" ? `<pre class="hl-king">${hlKing(body)}</pre>` : `<pre>${esc(body)}</pre>`;
  };
  for (const line of String(text || "").split("\n")) {
    if (/^\s*(```|~~~)/.test(line)) {
      if (code) { out.push(pre(code)); code = null; } else { flush(); code = []; lang = line.trim().replace(/^(```|~~~)/, "").trim().split(/\s/)[0].toLowerCase(); }
      continue;
    }
    if (code) { code.push(line); continue; }
    if (/^\s*\|/.test(line)) { if (!table.length) flush(); table.push(line); continue; }
    if (table.length) flush();
    const li = line.match(/^\s*[-*]\s+(.*)$/);
    if (li) { if (para.length) { const l = list; list = []; flush(); list = l; } list.push(li[1]); }
    else if (!line.trim()) flush();
    else { if (list.length) { const p = para; para = []; flush(); para = p; } para.push(line.trim()); }
  }
  if (code) out.push(pre(code));
  flush();
  return out.join("");
}
function bookLinks(n) {
  const outs = S.graph.links.filter(l => l.source === n.id && !l.tree && l.type !== "mention");
  const ins = S.graph.links.filter(l => l.target === n.id && !l.tree && l.type !== "mention");
  const chip = (l, other, arrow) => {
    const o = S.byId[other];
    return `<span class="chip" style="border-color:${esc(linkText(l.type))}"><b style="color:${esc(linkText(l.type))}">${esc(l.type)}</b> ${arrow} ` +
      `<a data-go="${esc(other)}">${esc(o ? o.title || other : other)}</a></span>`;
  };
  return (outs.length || ins.length)
    ? `<div class="chips">${outs.map(l => chip(l, l.target, "→")).join("")}${ins.map(l => chip(l, l.source, "←")).join("")}</div>` : "";
}
function bookItemHtml(n) {          // one node as Book renders it (shared with the Lecture view)
  if (n.kind === "section") {
    const h = Math.min(Math.max(n.level || 1, 1), 6);
    return `<h${h} data-id="${esc(n.id)}" data-line="${n.line}">${mdInline(n.title || n.id)}</h${h}>` +
      (n.content ? `<div data-id="${esc(n.id)}" data-line="${n.line}" class="sec-text">${isKir() ? kirDocHtml(n.content) : mdBlock(n.content)}</div>` : "");   // text dưới heading
  }
  // attribute: small grey text (0.3 palette); node type: purple label; ask sits above the content
  const meta = Object.entries(n.meta || {}).filter(([k]) => !["type", "ask", "show", "hide", "label"].includes(k)).map(([k, v]) =>
    `<span class="chip"><b>${esc(k)}</b>: <span class="mv">${esc(v)}</span></span>`).join("");
  return `<article data-id="${esc(n.id)}" data-line="${n.line}">` +
    `<h4>${mdInline(n.title || n.id)}${n.type ? `<span class="ty">${esc(n.type)}</span>` : ""}<small>@${esc(n.id)}</small></h4>` +
    (meta ? `<div class="chips attrs">${meta}</div>` : "") +
    (n.ask ? `<div class="ask">✎ ${mdInline(n.ask)}</div>` : "") +
    (n.content ? (isKir() ? kirDocHtml(n.content) : mdBlock(n.content)) : (n.ask ? "" : '<p class="empty">(no content yet)</p>')) +
    bookLinks(n) + "</article>";
}
function bookItems(view) {          // nodes in document order, minus definitions and hidden ones → {items, hidden}
  const all = S.graph.nodes.filter(n => n.kind !== "external").sort((a, b) => a.line - b.line), items = [];
  let hidden = 0;
  for (const n of all) {
    if (S.defHide && S.defHide.has(n.id)) continue;          // schema/style trong file: không phải nội dung sách
    if (n.show === "none" || hiddenIn(view).has(n.id)) { hidden++; continue; }
    items.push(n);
  }
  return {items, hidden};
}
function bindBook(el, go) {         // clicks: @ref links → go(id) (or select), blocks → jump to source line
  el.querySelectorAll("[data-go]").forEach(a => a.onclick = e => {
    e.stopPropagation(); const id = a.dataset.go;
    if (go) return go(id);
    if (!el.querySelector(`[data-id="${CSS.escape(id)}"]`)) return status(id + " is not shown in the book (show: none or imported node).");
    focusNode(id, true);
  });
  el.querySelectorAll("[data-line]").forEach(b => b.onclick = e => {
    if (e.target.closest("a")) return;
    jumpTo(+b.dataset.line); focusNode(b.dataset.id, false);
  });
}
function kingBlockHtml(lines) {     // one "KING environment": header (label, line count, ▾/▸ toggle) + highlighted run of commands
  const n = lines.length;
  return `<div class="king-env"><div class="king-head" onclick="kingToggle(event, this)">` +
    `<button class="king-tg" title="Collapse / expand">▾</button><b>KING</b><span class="king-n"> · ${n} line${n === 1 ? "" : "s"}</span></div>` +
    `<pre class="hl-king">${hlKing(lines.join("\n"))}</pre></div>`;
}
function kingToggle(e, h, collapse) {  // header click: fold this block (no jump to source)
  if (e) e.stopPropagation();
  const b = h.closest(".king-env"), c = collapse === undefined ? !b.classList.contains("folded") : collapse;
  b.classList.toggle("folded", c); b.querySelector(".king-tg").textContent = c ? "▸" : "▾";
}
function kingAllBtn(root) {         // one small "fold all KING blocks" button at the top of a view, if it has any
  const bk = root && root.querySelector(".book"); if (!bk || !bk.querySelector(".king-env")) return;
  const b = document.createElement("button"); b.className = "king-all"; b.textContent = "⊟ KING"; b.title = "Collapse / expand all KING blocks";
  b.onclick = e => { e.stopPropagation(); const envs = bk.querySelectorAll(".king-env"), c = ![...envs].every(x => x.classList.contains("folded"));
    envs.forEach(x => kingToggle(null, x, c)); b.textContent = (c ? "⊞" : "⊟") + " KING"; };
  bk.prepend(b);
}
function kirDocHtml(text) {         // kg: v0.4 text: prose as Markdown, runs of @command (and // comment) lines as KING blocks
  const lines = String(text || "").replace(/\r/g, "").split("\n");
  if (lines[0] && lines[0].trim() === "---") { const e = lines.indexOf("---", 1); if (e > 0) lines.splice(0, e + 1); }
  const out = []; let prose = [], cmd = [], fence = false;
  const flush = () => {
    if (prose.length) out.push(mdBlock(prose.join("\n")));
    if (cmd.length) out.push(kingBlockHtml(cmd));
    prose = []; cmd = [];
  };
  for (const l of lines) {
    if (/^\s*(```|~~~)/.test(l)) fence = !fence;               // fenced code in prose stays prose
    if (!fence && (KING_CMD.test(l) || /^\/\//.test(l))) { if (prose.length) flush(); cmd.push(l); }
    else { if (cmd.length) flush(); prose.push(l); }
  }
  flush();
  return out.join("");
}
const isKir = () => /^---\s*\n(?:[^\n]*\n)*?\s*kg\s*:\s*v?0\.[4-9]/.test(String(S.text || "").replace(/\r/g, ""));
function renderBook() {
  const el = $("#bookView");
  if (!S.graph) { el.innerHTML = '<div class="book"><p class="empty">(no data yet)</p></div>'; return; }
  const {items, hidden} = bookItems("book"), out = items.map(bookItemHtml);
  if (!items.length && isKir()) { el.innerHTML = `<div class="book">${kirDocHtml(S.text)}</div>`; kingAllBtn(el); return; }
  if (hidden) out.push(`<p class="note">${hidden} item(s) with <code>show: none</code> or <code>hide</code> are not shown in the book (View › Show hidden nodes).</p>`);
  el.innerHTML = `<div class="book">${out.join("")}</div>`;
  bindBook(el); kingAllBtn(el);
  if (S.selected) markSelected(S.selected, false);
}
