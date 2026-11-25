// lecture.js - Lecture view: one unit (section) at a time, TOC sidebar, Prev / Next.
// A unit shows its own prose + nodes (rendered like Book) and links to its child sections.
// Sections deeper than the chosen depth are folded into their ancestor unit.
const LEC = {depth: 3, cur: null, fold: new Set(), side: true, file: null};
const lecKey = () => "kglecture:" + (S.name || "");
function lecLoad() {
  if (LEC.file === S.name) return;
  LEC.file = S.name; LEC.cur = null; LEC.depth = 3; LEC.fold = new Set();
  try { const v = JSON.parse(localStorage.getItem(lecKey()) || "null"); if (v) { LEC.cur = v.id; LEC.depth = v.depth || 3; } } catch (e) {}
}
function lecSave() { try { localStorage.setItem(lecKey(), JSON.stringify({id: LEC.cur, depth: LEC.depth})); } catch (e) {} }
function lecModel() {
  const {items} = bookItems("book"), byId = {}, rank = {};
  for (const n of items) byId[n.id] = n;
  const secRank = n => {                    // 1 + number of section ancestors (robust to skipped heading levels)
    if (rank[n.id]) return rank[n.id];
    let r = 1, p = n.parent && byId[n.parent];
    while (p) { if (p.kind === "section") r++; p = p.parent && byId[p.parent]; }
    return rank[n.id] = r;
  };
  const units = items.filter(n => n.kind === "section" && secRank(n) <= LEC.depth);
  const isUnit = new Set(units.map(n => n.id));
  const unitOf = n => {                     // nearest ancestor-or-self unit; "" = before the first section
    for (let p = n; p; p = p.parent && byId[p.parent]) if (isUnit.has(p.id)) return p.id;
    return "";
  };
  const body = {}; for (const n of items) (body[unitOf(n)] ||= []).push(n);
  const list = (body[""] || []).length ? [{id: "", title: S.name || "Start", rank: 1, parent: null}] : [];
  for (const n of units) {
    let p = n.parent && byId[n.parent]; while (p && !isUnit.has(p.id)) p = p.parent && byId[p.parent];
    list.push({id: n.id, title: n.title || n.id, rank: secRank(n), parent: p ? p.id : null});
  }
  return {list, body, unitOf};
}
function renderLecture() {
  const el = $("#lectureView");
  if (!S.graph) { el.innerHTML = '<div class="book"><p class="empty">(no data yet)</p></div>'; return; }
  lecLoad();
  const M = lecModel(), L = M.list;
  if (!L.length) {
    el.innerHTML = isKir() ? `<div class="book">${kirDocHtml(S.text)}</div>` : '<div class="book"><p class="empty">(no sections)</p></div>';
    kingAllBtn(el); return;
  }
  let i = L.findIndex(u => u.id === LEC.cur); if (i < 0) i = 0;
  const u = L[i]; LEC.cur = u.id;
  const kids = id => L.filter(x => x.parent === id);
  // TOC: hide items under a folded ancestor
  const folded = x => { for (let p = x.parent; p !== null; p = (L.find(y => y.id === p) || {}).parent ?? null) if (LEC.fold.has(p)) return true; return false; };
  const toc = L.filter(x => !folded(x)).map(x => {
    const has = kids(x.id).length;
    return `<div class="tr lec-it${x.id === u.id ? " on" : ""}" data-u="${esc(x.id)}" style="padding-left:${(x.rank - 1) * 14 + 4}px">` +
      `<span class="tw">${has ? (LEC.fold.has(x.id) ? "▸" : "▾") : ""}</span><span class="nm">${mdInline(x.title)}</span></div>`;
  }).join("");
  const depthOpts = [1, 2, 3, 4, 5, 6].map(d => `<option${d === LEC.depth ? " selected" : ""}>${d}</option>`).join("");
  const sub = kids(u.id);
  const main = (M.body[u.id] || []).map(bookItemHtml).join("") +
    (sub.length ? `<div class="lec-sub"><b>In this section</b><ul>${sub.map(x => `<li><a data-u="${esc(x.id)}">${mdInline(x.title)}</a></li>`).join("")}</ul></div>` : "");
  el.innerHTML = `<div class="lecture${LEC.side ? "" : " noside"}">` +
    `<aside class="lec-side"><div class="lec-tools">` +
    `<label title="Number of heading levels in the contents">Depth <select id="lecDepth">${depthOpts}</select></label>` +
    `<button id="lecCollapse" title="Collapse all">⊟</button><button id="lecExpand" title="Expand all">⊞</button></div>` +
    `<div class="lec-toc">${toc}</div></aside>` +
    `<section class="lec-main"><div class="lec-bar"><button id="lecSide" title="Show / hide contents">☰</button>` +
    `<button id="lecPrev" ${i ? "" : "disabled"} title="Previous (←)">← Prev</button><span class="lec-pos">${i + 1} / ${L.length}</span>` +
    `<button id="lecNext" ${i < L.length - 1 ? "" : "disabled"} title="Next (→)">Next →</button></div>` +
    `<div class="book">${main || '<p class="empty">(empty)</p>'}</div></section></div>`;
  const open = id => { LEC.cur = id; lecSave(); renderLecture(); el.querySelector(".lec-main").scrollTop = 0; };
  el.querySelectorAll(".lec-it").forEach(t => t.onclick = e => {
    const id = t.dataset.u;
    if (e.target.closest(".tw") && kids(id).length) { LEC.fold.has(id) ? LEC.fold.delete(id) : LEC.fold.add(id); return renderLecture(); }
    open(id);
  });
  el.querySelectorAll(".lec-sub a[data-u]").forEach(a => a.onclick = () => open(a.dataset.u));
  $("#lecDepth").onchange = e => { LEC.depth = +e.target.value; lecSave(); renderLecture(); };
  $("#lecCollapse").onclick = () => { LEC.fold = new Set(L.filter(x => kids(x.id).length).map(x => x.id)); renderLecture(); };
  $("#lecExpand").onclick = () => { LEC.fold.clear(); renderLecture(); };
  $("#lecSide").onclick = () => { LEC.side = !LEC.side; renderLecture(); };
  $("#lecPrev").onclick = () => lecStep(-1); $("#lecNext").onclick = () => lecStep(1);
  bindBook(el.querySelector(".lec-main .book"), id => {       // @ref: open the unit that holds the node
    const n = S.byId[id];
    if (!n || n.kind === "external") return status(id + " is not in this document.");
    const v = M.unitOf(n); if (v !== LEC.cur && L.some(x => x.id === v)) open(v);
    focusNode(id, true);
  });
  kingAllBtn(el.querySelector(".lec-main"));
  const on = el.querySelector(".lec-it.on"); if (on) on.scrollIntoView({block: "nearest"});
  lecSave();
}
function lecStep(d) {
  const L = lecModel().list, i = Math.max(0, L.findIndex(u => u.id === LEC.cur)), j = i + d;
  if (j < 0 || j >= L.length) return;
  LEC.cur = L[j].id; lecSave(); renderLecture();
  const m = $("#lectureView .lec-main"); if (m) m.scrollTop = 0;
}
document.addEventListener("keydown", e => {
  if (e.ctrlKey || e.metaKey || e.altKey || !["ArrowLeft", "ArrowRight"].includes(e.key) || !shown("lecture")) return;
  const t = e.target; if (t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable)) return;
  e.preventDefault(); lecStep(e.key === "ArrowLeft" ? -1 : 1);
});
