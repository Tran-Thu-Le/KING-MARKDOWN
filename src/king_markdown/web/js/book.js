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
function mdBlock(text) {
  const out = []; let para = [], list = [], table = [], code = null;
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
    return `<pre>${esc(lines.map(l => l.slice(ind)).join("\n"))}</pre>`;
  };
  for (const line of String(text || "").split("\n")) {
    if (/^\s*(```|~~~)/.test(line)) {
      if (code) { out.push(pre(code)); code = null; } else { flush(); code = []; }
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
function renderBook() {
  const el = $("#bookView");
  if (!S.graph) { el.innerHTML = '<div class="book"><p class="empty">(chưa có dữ liệu)</p></div>'; return; }
  const items = S.graph.nodes.filter(n => n.kind !== "external").sort((a, b) => a.line - b.line), out = [];
  let hidden = 0;
  for (const n of items) {
    if (S.defHide && S.defHide.has(n.id)) continue;          // schema/style trong file: không phải nội dung sách
    if (n.show === "none" || hiddenIn("book").has(n.id)) { hidden++; continue; }
    if (n.kind === "section") {
      const h = Math.min(Math.max(n.level || 1, 1), 6);
      out.push(`<h${h} data-id="${esc(n.id)}" data-line="${n.line}">${mdInline(n.title || n.id)}</h${h}>`);
      if (n.content) out.push(`<div data-id="${esc(n.id)}" data-line="${n.line}" class="sec-text">${mdBlock(n.content)}</div>`);   // văn bản dưới heading
      continue;
    }
    // attribute: chữ xám nhỏ (bảng màu 0.3); kiểu node: nhãn tím; ask nằm trên nội dung
    const meta = Object.entries(n.meta || {}).filter(([k]) => !["type", "ask", "show", "hide", "label"].includes(k)).map(([k, v]) =>
      `<span class="chip"><b>${esc(k)}</b>: <span class="mv">${esc(v)}</span></span>`).join("");
    out.push(`<article data-id="${esc(n.id)}" data-line="${n.line}">` +
      `<h4>${mdInline(n.title || n.id)}${n.type ? `<span class="ty">${esc(n.type)}</span>` : ""}<small>@${esc(n.id)}</small></h4>` +
      (meta ? `<div class="chips attrs">${meta}</div>` : "") +
      (n.ask ? `<div class="ask">✎ ${mdInline(n.ask)}</div>` : "") +
      (n.content ? mdBlock(n.content) : (n.ask ? "" : '<p class="empty">(chưa có nội dung)</p>')) +
      bookLinks(n) + "</article>");
  }
  if (hidden) out.push(`<p class="note">${hidden} mục có <code>show: none</code> hoặc <code>hide</code> không hiện trong sách (View › Hiện cả node đã ẩn).</p>`);
  el.innerHTML = `<div class="book">${out.join("")}</div>`;
  el.querySelectorAll("[data-go]").forEach(a => a.onclick = e => {
    e.stopPropagation(); const id = a.dataset.go;
    if (!el.querySelector(`[data-id="${CSS.escape(id)}"]`)) return status(id + " không hiện trong sách (show: none hoặc node import).");
    focusNode(id, true);
  });
  el.querySelectorAll("[data-line]").forEach(b => b.onclick = e => {
    if (e.target.closest("a")) return;
    jumpTo(+b.dataset.line); focusNode(b.dataset.id, false);
  });
  if (S.selected) markSelected(S.selected, false);
}
