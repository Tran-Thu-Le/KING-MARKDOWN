// module.js - View Module: đồ thị lồng nhau. Node có node con = nhóm (hình chữ nhật bo góc) chứa các node con bên trong;
// node nội dung = hình tròn. Cha–con: con part-of cha, cha contain con, node trong section, + loại link tick thêm.
// Các link khác vẽ giữa các node như Graph. Mỗi nhóm bật / tắt hiện node con (▾ / ▸, hoặc nhấp đúp).
let modClosed = new Set(), modLinks = new Set();      // modLinks: loại link thêm vào quan hệ chứa (nguồn nằm trong đích)
const MV = {k:1, tx:20, ty:20, fit:true};             // pan / zoom
const modKey = () => "kgmod:" + (S.root || "static") + "|" + S.name;
function loadMod() {
  try {
    const v = JSON.parse(localStorage.getItem(modKey()) || "{}");
    modClosed = new Set(Array.isArray(v) ? v : v.closed || []); modLinks = new Set(v.links || []);
  } catch (e) { modClosed = new Set(); modLinks = new Set(); }
  S.modKey = modKey(); MV.fit = true;
}
function saveMod() { try { localStorage.setItem(modKey(), JSON.stringify({closed:[...modClosed], links:[...modLinks]})); } catch (e) {} }

function modChildren() {
  // cha của một node: đích của part-of / của loại link đã chọn, nguồn của contain; không có thì section chứa nó.
  // Node có nhiều cha thì hiện trong nhóm của từng cha.
  const ps = {}, kids = {}, roots = [], seen = new Set();
  const add = (c, p, via) => {
    const k = c + ">" + p;
    if (c === p || !S.byId[p] || !S.byId[c] || seen.has(k)) return;
    seen.add(k); (ps[c] = ps[c] || []).push({p, via});
  };
  for (const l of S.graph.links) {
    if (l.type === "part-of" || modLinks.has(l.type)) add(l.source, l.target, l.type);
    else if (l.type === "contain") add(l.target, l.source, "contain");
  }
  for (const n of S.graph.nodes.slice().sort((a, b) => (a.line || 1e9) - (b.line || 1e9))) {
    const list = ps[n.id];
    if (list) list.forEach(({p, via}) => (kids[p] = kids[p] || []).push({n, via}));
    else if (n.parent && S.byId[n.parent]) (kids[n.parent] = kids[n.parent] || []).push({n, via:null});
    else roots.push({n, via:null});
  }
  return {kids, roots};
}

// ---------- đo và xếp ----------
const _mc = document.createElement("canvas").getContext("2d");
function textW(t, size, bold) { _mc.font = `${bold ? "600 " : ""}${size}px system-ui, sans-serif`; return _mc.measureText(String(t)).width; }
function wrapText(t, max) {
  const lines = []; let cur = "";
  for (const w of String(t).split(/\s+/)) {
    const nx = cur ? cur + " " + w : w;
    if (cur && textW(nx, 13) > max) { lines.push(cur); cur = w; } else cur = nx;
  }
  if (cur) lines.push(cur);
  return lines.slice(0, 4);
}
const PAD = 18, GAP = 48, HEAD = 32;      // GAP rộng để thấy được link giữa các node đứng cạnh nhau
const modVisible = n => (S.showDefs || !(S.defHide && S.defHide.has(n.id))) && !hiddenIn("module").has(n.id);
function flow(items, maxW) {          // xếp thành hàng, mỗi hàng căn giữa; trả kích thước khối
  const rows = []; let row = [], rw = 0;
  for (const it of items) {
    if (row.length && rw + GAP + it.w > maxW) { rows.push(row); row = []; rw = 0; }
    rw += (row.length ? GAP : 0) + it.w; row.push(it);
  }
  if (row.length) rows.push(row);
  const widths = rows.map(r => r.reduce((s, it, i) => s + it.w + (i ? GAP : 0), 0)), inner = Math.max(0, ...widths);
  let y = 0;
  rows.forEach((r, i) => {
    const rh = Math.max(...r.map(it => it.h)); let x = (inner - widths[i]) / 2;
    r.forEach(it => { it.x = x; it.y = y + (rh - it.h) / 2; x += it.w + GAP; });
    y += rh + GAP;
  });
  return {w:inner, h:Math.max(0, y - GAP)};
}
function measure(item, kids, path) {
  const n = item.n, title = n.title || n.id;
  const ch = (kids[n.id] || []).filter(c => modVisible(c.n) && !path.has(c.n.id));
  const box = {n, via:item.via};
  if (!ch.length && n.kind !== "section" && n.id !== "__ext") {        // node nội dung: hình tròn
    const lines = wrapText(title, 112), tw = Math.max(...lines.map(l => textW(l, 13)));
    const r = Math.max(30, Math.hypot(tw / 2 + 6, lines.length * 8 + 4) + 4);
    return Object.assign(box, {leaf:true, lines, r, w:2 * r, h:2 * r, children:[]});
  }
  const tw = textW(title, 13, true) + 64;                                  // nhóm: hình chữ nhật bo góc
  Object.assign(box, {leaf:false, count:ch.length, closed:modClosed.has(n.id) && ch.length > 0});
  if (box.closed || !ch.length) {
    box.children = []; box.hiddenIds = box.closed ? descendants(n.id, kids, path) : [];
    box.w = Math.max(150, tw); box.h = HEAD + (ch.length ? 24 : 12);
    return box;
  }
  const np = new Set([...path, n.id]);
  box.children = ch.map(c => measure(c, kids, np));
  const area = box.children.reduce((s, c) => s + (c.w + GAP) * (c.h + GAP), 0);
  const sz = flow(box.children, Math.max(tw, ...box.children.map(c => c.w), Math.sqrt(area) * 1.5));
  box.w = Math.max(sz.w, tw) + 2 * PAD; box.h = HEAD + sz.h + PAD;
  const off = (box.w - 2 * PAD - sz.w) / 2;
  box.children.forEach(c => { c.x += PAD + off; c.y += HEAD; });
  return box;
}
function descendants(id, kids, path) {
  const out = [], st = [...(kids[id] || [])], seen = new Set(path);
  while (st.length) { const {n} = st.pop(); if (seen.has(n.id)) continue; seen.add(n.id); out.push(n.id); st.push(...(kids[n.id] || [])); }
  return out;
}
function place(box, ox, oy, at, groups, leaves, up) {   // toạ độ tuyệt đối; at: id → hộp đầu tiên hiện node đó
  box.ax = ox + box.x; box.ay = oy + box.y; box.up = up || null;
  if (!(box.n.id in at)) at[box.n.id] = box;
  (box.leaf ? leaves : groups).push(box);
  (box.hiddenIds || []).forEach(id => { if (!(id in at)) at[id] = box; });
  box.children.forEach(c => place(c, box.ax, box.ay, at, groups, leaves, box));
}
const inside = (a, g) => { for (let x = a.up; x; x = x.up) if (x === g) return true; return false; };

// ---------- vẽ SVG ----------
function clipTo(b, tx, ty) {            // điểm trên mép hình của b, hướng về (tx, ty)
  const cx = b.ax + b.w / 2, cy = b.ay + b.h / 2, dx = tx - cx, dy = ty - cy, L = Math.hypot(dx, dy) || 1;
  if (b.leaf) return [cx + dx / L * b.r, cy + dy / L * b.r];
  const t = Math.min((b.w / 2) / (Math.abs(dx) || 1e-9), (b.h / 2) / (Math.abs(dy) || 1e-9));
  return [cx + dx * t, cy + dy * t];
}
function renderModule() {
  const el = $("#moduleView");
  if (!S.graph) { el.innerHTML = '<p class="ins-empty">(chưa có dữ liệu)</p>'; return; }
  if (S.modKey !== modKey()) loadMod();
  const {kids, roots} = modChildren();
  const main = roots.filter(r => r.n.kind !== "external" && modVisible(r.n)), ext = roots.filter(r => r.n.kind === "external");
  if (ext.length) { kids.__ext = ext; main.push({n:{id:"__ext", title:"Node import", kind:"section"}, via:null}); }
  const top = main.map(r => measure(r, kids, new Set()));
  const area = top.reduce((s, c) => s + (c.w + GAP) * (c.h + GAP), 0);
  flow(top, Math.max(700, Math.sqrt(area) * 1.6, ...top.map(c => c.w)));
  const at = {}, groups = [], leaves = [];
  top.forEach(b => place(b, 0, 0, at, groups, leaves));

  // link: mọi link không dùng cho quan hệ chứa
  const nest = new Set(["part-of", "contain", ...modLinks]), marks = {};
  let defs = "", edges = "";
  for (const l of S.graph.links) {
    if (l.tree || nest.has(l.type) || linkHiddenIn(l, "module")) continue;
    const a = at[l.source], b = at[l.target];
    if (!a || !b || a === b || inside(a, b) || inside(b, a)) continue;   // link tới nhóm đang chứa nó: đã thấy qua việc lồng
    const s = H(l), color = s.color || linkColor(l.type);
    if (!(color in marks)) {
      marks[color] = "mk" + Object.keys(marks).length;
      defs += `<marker id="${marks[color]}" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="${esc(color)}"/></marker>`;
    }
    const [x1, y1] = clipTo(a, b.ax + b.w / 2, b.ay + b.h / 2), [x2, y2] = clipTo(b, a.ax + a.w / 2, a.ay + a.h / 2);
    const arrows = s.arrows || "to", m = `url(#${marks[color]})`;
    edges += `<g class="medge"><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${esc(color)}" stroke-width="${num(s.width, 1.5)}"` +
      (s.dash === true ? ' stroke-dasharray="5,4"' : "") + (s.opacity !== undefined ? ` opacity="${num(s.opacity, 1)}"` : "") +
      (arrows === "to" || arrows === "both" ? ` marker-end="${m}"` : "") + (arrows === "from" || arrows === "both" ? ` marker-start="${m}"` : "") + "/>" +
      ((S.hideLab || {}).link ? "" : `<text x="${(x1 + x2) / 2}" y="${(y1 + y2) / 2}" class="mlabel">${esc(l.type)}</text>`) + "</g>";
  }
  const gsvg = groups.map(b => {
    // hộp nhóm: nền nhạt (16%) nên tên nhóm nằm trên nền trang → dùng màu nhãn; số con dùng chữ phụ
    const s = H(b.n), sec = b.n.kind === "section", look = nodeLook(b.n), stroke = look.border;
    const fill = sec ? "none" : look.fill, has = b.count > 0;
    return `<g class="mod mgroup" data-id="${esc(b.n.id)}">` +
      // section: hình chữ nhật góc vuông; nhóm (node có node con): hình chữ nhật bo góc
      `<rect class="shape" x="${b.ax}" y="${b.ay}" width="${b.w}" height="${b.h}" rx="${num(s.radius, sec ? 0 : 14)}" fill="${esc(fill)}" fill-opacity="${sec ? 0 : 0.16}"` +
      ` stroke="${esc(stroke)}" stroke-width="${num(s.border, 1.5)}"${s.dash === true ? ' stroke-dasharray="6,4"' : ""}/>` +
      (has ? `<text class="mtw" x="${b.ax + 14}" y="${b.ay + 21}">${b.closed ? "▸" : "▾"}</text>` : "") +
      (sec && (S.hideLab || {}).section ? "" : `<text class="mgt${sec ? " sec" : ""}" x="${b.ax + (has ? 30 : 14)}" y="${b.ay + 21}" style="fill:${esc(look.label)}">${esc(b.n.title || b.n.id)}</text>`) +
      (b.closed ? `<text class="mgc" x="${b.ax + 30}" y="${b.ay + 43}" style="fill:${esc(look.sub)}">+${b.count} con · nhấp đúp để mở</text>` : "") + "</g>";
  }).join("");
  const lsvg = leaves.map(b => {
    // lá: chữ nằm trên nền node → dùng màu chữ chính (tự đổi trắng / đen theo nền nếu style không ghi)
    const s = H(b.n), look = nodeLook(b.n), cx = b.ax + b.r, cy = b.ay + b.r, lh = 16, y0 = cy - (b.lines.length - 1) * lh / 2;
    return `<g class="mod mleaf" data-id="${esc(b.n.id)}"><circle class="shape" cx="${cx}" cy="${cy}" r="${b.r}" fill="${esc(look.fill)}"` +
      ` stroke="${esc(look.border)}" stroke-width="${num(s.border, 1.5)}"${s.dash === true ? ' stroke-dasharray="5,4"' : ""}/>` +
      ((S.hideLab || {}).node ? "" : b.lines.map((t, i) => `<text x="${cx}" y="${y0 + i * lh}" fill="${esc(look.text)}">${esc(t)}</text>`).join("")) +
      (b.n.ask ? `<text x="${cx + b.r * 0.72}" y="${cy - b.r * 0.72}" class="mask">✎</text>` : "") + "</g>";
  }).join("");

  const types = [...new Set(S.graph.links.filter(l => !l.tree && !["part-of", "contain", "mention"].includes(l.type)).map(l => l.type))];
  const parents = groups.filter(b => b.count > 0 && b.n.id !== "__ext").map(b => b.n.id);
  el.innerHTML =
    `<div class="mbar"><button class="btn" data-mall="open">Bung hết</button><button class="btn" data-mall="close">Thu hết</button>` +
    `<button class="btn" data-mall="fit" title="Vừa khung">⤢</button>` +
    `<span class="mlinks" title="Mặc định: con part-of cha, cha contain con, node trong section. Tick thêm loại link: nguồn nằm trong đích.">Lồng theo: ` +
    `<b style="color:${esc(linkText("part-of"))}">part-of</b>, <b style="color:${esc(linkText("contain"))}">contain</b>` +
    types.map(t => `<label><input type="checkbox" data-mlink="${esc(t)}"${modLinks.has(t) ? " checked" : ""}> <span style="color:${esc(linkText(t))}">${esc(t)}</span></label>`).join("") +
    `</span></div>` +
    `<svg id="msvg" xmlns="http://www.w3.org/2000/svg"><defs>${defs}</defs><g id="mz">${gsvg}${edges}${lsvg}</g></svg>` +
    `<div class="mhint">▾ / ▸ hoặc nhấp đúp nhóm: hiện / ẩn node con · kéo nền: di chuyển · cuộn: phóng to</div>`;
  const svg = el.querySelector("#msvg"), z = el.querySelector("#mz");
  const apply = () => z.setAttribute("transform", `translate(${MV.tx},${MV.ty}) scale(${MV.k})`);
  const fit = () => {
    const bb = z.getBBox(), W = svg.clientWidth || 600, Hh = svg.clientHeight || 400;
    if (!bb.width) return;
    MV.k = Math.min(1.4, (W - 40) / bb.width, (Hh - 40) / bb.height);
    MV.tx = (W - bb.width * MV.k) / 2 - bb.x * MV.k; MV.ty = Math.max(16, (Hh - bb.height * MV.k) / 2) - bb.y * MV.k; apply();
  };
  if (MV.fit && svg.clientWidth) { MV.fit = false; fit(); } else apply();

  el.querySelectorAll("[data-mlink]").forEach(c => c.onchange = () => {
    if (c.checked) modLinks.add(c.dataset.mlink); else modLinks.delete(c.dataset.mlink);
    saveMod(); MV.fit = true; renderModule();
  });
  el.querySelectorAll("[data-mall]").forEach(b => b.onclick = () => {
    if (b.dataset.mall === "fit") return fit();
    modClosed = b.dataset.mall === "close" ? new Set(parents) : new Set(); saveMod(); MV.fit = true; renderModule();
  });
  const toggle = id => { if (modClosed.has(id)) modClosed.delete(id); else modClosed.add(id); saveMod(); renderModule(); };
  el.querySelectorAll(".mod[data-id]").forEach(g => {
    g.addEventListener("click", e => {
      e.stopPropagation();
      const id = g.dataset.id, n = S.byId[id];
      if (e.target.classList.contains("mtw")) return toggle(id);
      if (!n) return;
      if (n.kind !== "external" && n.line) jumpTo(n.line);
      focusNode(id, false);
    });
    if (g.classList.contains("mgroup")) g.addEventListener("dblclick", e => { e.stopPropagation(); if (g.querySelector(".mtw")) toggle(g.dataset.id); });
  });
  // kéo nền để di chuyển, cuộn để phóng to quanh con trỏ
  svg.onmousedown = e => {
    if (e.target.closest(".mod")) return;
    const x0 = e.clientX - MV.tx, y0 = e.clientY - MV.ty;
    const mv = ev => { MV.tx = ev.clientX - x0; MV.ty = ev.clientY - y0; apply(); };
    const up = () => { removeEventListener("mousemove", mv); removeEventListener("mouseup", up); };
    addEventListener("mousemove", mv); addEventListener("mouseup", up);
  };
  svg.onwheel = e => {
    e.preventDefault();
    const r = svg.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top, f = Math.exp(-e.deltaY * 0.0015);
    const k = Math.min(4, Math.max(0.15, MV.k * f));
    MV.tx = px - (px - MV.tx) * k / MV.k; MV.ty = py - (py - MV.ty) * k / MV.k; MV.k = k; apply();
  };
  if (S.selected) markSelected(S.selected, false);
}
