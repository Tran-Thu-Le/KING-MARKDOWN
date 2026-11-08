// graph.js - đồ thị vis-network: vẽ, chế độ, sự kiện, Format, Schema, xuất SVG
const nodesDS = new vis.DataSet(), edgesDS = new vis.DataSet();
const net = new vis.Network($("#g"), {nodes:nodesDS, edges:edgesDS}, {
  physics:{enabled:false, solver:"forceAtlas2Based", stabilization:{iterations:300}},
  edges:{smooth:false}, interaction:{hover:true, multiselect:true},
  manipulation:{enabled:false, addEdge:(d, cb) => { cb(null); onAddEdge(d); }}
});

// ---------- vẽ ----------
function tip(n) {
  const el = document.createElement("div");
  el.style.cssText = "white-space:pre-wrap;max-width:340px;font:12px system-ui";
  el.textContent = [n.id + (n.kind !== "node" ? " (" + n.kind + ")" : ""),
    ...Object.entries(n.meta || {}).map(([k, v]) => k + " = " + v),
    n.content ? "\n" + n.content : "", n.ask ? "\nask: " + n.ask : ""].filter(Boolean).join("\n");
  return el;
}
const LABEL_OUTSIDE = new Set(["dot", "star", "triangle", "diamond", "hexagon", "text"]), LABEL_OUT_COLOR = "#d4d4d4";
// màu nhãn mặc định theo bộ màu chung: section xanh dương, node vàng nhạt (khi xuất SVG nền trắng thì đổi sang chữ tối)
const labelColor = n => n.kind === "section" ? PAL.sec : PAL.node;
const svgText = c => [LABEL_OUT_COLOR, PAL.sec, PAL.node].includes(c) ? "#1f2328" : c;

// ---------- thu gọn / bung: con part-of cha, hoặc cha có meta contain=con ----------
function buildFold(g) {
  S.kids = {}; S.parents = {};
  const add = (p, c) => { if (p === c) return; (S.kids[p] = S.kids[p] || new Set()).add(c); (S.parents[c] = S.parents[c] || new Set()).add(p); };
  for (const l of g.links) {
    if (l.type === "part-of") add(l.target, l.source);
    else if (l.type === "contain") add(l.source, l.target);
  }
  for (const id of [...S.folded]) if (!S.kids[id]) S.folded.delete(id);
  // ẩn mọi con cháu của node đang thu gọn; node thu gọn nằm dưới một node thu gọn khác cũng bị ẩn
  S.hidden = new Set();
  const stack = [...S.folded].flatMap(id => [...S.kids[id]]);
  while (stack.length) {
    const id = stack.pop();
    if (S.hidden.has(id)) continue;
    S.hidden.add(id); if (S.kids[id]) stack.push(...S.kids[id]);
  }
  // schema/style viết ngay trong file dữ liệu: ẩn các node định nghĩa (và section chỉ chứa chúng) khỏi Graph, Book.
  // Tree / Outline vẫn hiện để chọn và sửa. Format › "node schema/style" để hiện lên đồ thị.
  S.defHide = new Set();
  if (g.nodes.some(n => n.kind === "node" && !n.def)) {
    const sub = {};
    g.nodes.forEach(n => { if (n.parent) (sub[n.parent] = sub[n.parent] || []).push(n); });
    g.nodes.forEach(n => {
      if (n.def || (n.kind === "section" && sub[n.id] && sub[n.id].every(c => c.def))) S.defHide.add(n.id);
    });
  }
  if (!S.showDefs) S.defHide.forEach(id => S.hidden.add(id));
}
function countBelow(id) {
  const seen = new Set(), st = [...(S.kids[id] || [])];
  while (st.length) { const x = st.pop(); if (seen.has(x) || x === id) continue; seen.add(x); st.push(...(S.kids[x] || [])); }
  return seen.size;
}
function toggleFold(id) {
  if (!S.kids[id]) return status("Node " + id + " không có node con (part-of / contain).");
  if (S.folded.has(id)) S.folded.delete(id); else S.folded.add(id);
  saveFold(); render(S.graph);
  status((S.folded.has(id) ? "Đã thu gọn " : "Đã bung ") + id);
}
function foldAll(on) {
  if (!S.graph) return;
  S.folded = on ? new Set(Object.keys(S.kids)) : new Set();
  saveFold(); render(S.graph); if (!on) net.fit();
}

// ---------- Graph: hình nhỏ, nhãn luôn nằm DƯỚI hình ----------
// elip / tròn / chữ nhật / vuông: tự vẽ bằng ctxRenderer (vis đặt chữ bên trong các hình này);
// tam giác, sao, thoi, lục giác, chấm: vis vốn đặt nhãn dưới hình.
const CUSTOM_SHAPES = new Set(["ellipse", "circle", "box", "square"]);
function shapeBox(shape, size) {
  if (shape === "ellipse") return {w:size * 2.6, h:size * 1.7};
  if (shape === "circle" || shape === "square") return {w:size * 2, h:size * 2};
  return {w:size * 2.8, h:size * 1.6};                    // box
}
function wrapLabel(ctx, text, max) {
  const lines = []; let cur = "";
  for (const w of String(text).split(/\s+/)) {
    const nx = cur ? cur + " " + w : w;
    if (cur && ctx.measureText(nx).width > max) { lines.push(cur); cur = w; } else cur = nx;
  }
  if (cur) lines.push(cur);
  return lines.slice(0, 3);
}
function shapePath(ctx, m, x, y) {
  ctx.beginPath();
  if (m.shape === "ellipse") ctx.ellipse(x, y, m.w / 2, m.h / 2, 0, 0, 2 * Math.PI);
  else if (m.shape === "circle") ctx.arc(x, y, m.w / 2, 0, 2 * Math.PI);
  else {
    const r = Math.max(0, Math.min(m.radius, m.h / 2)), l = x - m.w / 2, t = y - m.h / 2;
    if (ctx.roundRect) ctx.roundRect(l, t, m.w, m.h, r); else ctx.rect(l, t, m.w, m.h);
  }
}
function renderer(m) {
  return ({ctx, x, y, state}) => ({
    drawNode() {
      const on = state.selected || state.hover;
      ctx.globalAlpha = m.opacity;
      shapePath(ctx, m, x, y);
      ctx.fillStyle = m.bg; ctx.fill();
      ctx.lineWidth = on ? m.bw + 2 : m.bw; ctx.strokeStyle = on ? "#3794ff" : m.bd;
      ctx.setLineDash(m.dash ? [5, 4] : []); ctx.stroke(); ctx.setLineDash([]);
    },
    drawExternalLabel() {
      if (!m.label) return;
      ctx.globalAlpha = m.opacity;
      ctx.font = `${m.fontSize}px ${m.font}`; ctx.textAlign = "center"; ctx.textBaseline = "top";
      ctx.lineWidth = 3; ctx.strokeStyle = "#1e1e1e"; ctx.fillStyle = m.fontColor; ctx.lineJoin = "round";
      wrapLabel(ctx, m.label, 150).forEach((t, i) => {
        const ty = y + m.h / 2 + 4 + i * (m.fontSize + 2);
        ctx.strokeText(t, x, ty); ctx.fillText(t, x, ty);
      });
    },
    nodeDimensions:{width:m.w, height:m.h},
  });
}
function visNode(n) {
  const s = H(n), err = n.kind !== "external" && S.bad.has(n.line), sec = n.kind === "section";
  const bg = s.color || (sec ? "#dbeafe" : "#fff7cc"), bd = err ? "#b00020" : (s["border-color"] || (sec ? "#3b82f6" : "#c9a227"));
  const bw = num(s.border, 1.5), shape = s.shape || (sec ? "box" : "ellipse");
  const fold = !S.kids[n.id] ? "" : S.folded.has(n.id) ? ` ▸ +${countBelow(n.id)}` : " ▾";
  const hide = (S.hideLab || {})[sec ? "section" : "node"];
  const label = hide ? "" : (n.title || n.id) + (n.ask ? " ✎" : "") + fold;
  const font = {face:s.font || "system-ui", size:num(s["font-size"], 13), color:s["font-color"] || labelColor(n)};
  const base = {id:n.id, title:tip(n), hidden:S.hidden.has(n.id), opacity:num(s.opacity, 1)};
  if (CUSTOM_SHAPES.has(shape)) {
    const m = {shape, ...shapeBox(shape, num(s.size, sec ? 13 : 14)), radius:num(s.radius, shape === "box" ? 6 : 0),
               bg, bd, bw:err ? 3 : bw, dash:s.dash === true, opacity:num(s.opacity, 1),
               label, font:font.face, fontSize:font.size, fontColor:font.color};
    return {...base, shape:"custom", ctxRenderer:renderer(m), label, kg:m};
  }
  return {...base, label, shape, size:num(s.size, 14), font,
    color:{background:bg, border:bd, highlight:{background:bg, border:"#3794ff"}, hover:{background:bg, border:"#3794ff"}},
    borderWidth:err ? 3 : bw, borderWidthSelected:bw + 2,
    shapeProperties:{borderDashes:s.dash === true ? [5, 4] : false}};
}
function visEdges() {
  S.edgeMap = {}; const show = $("#showTree").checked, out = [];
  S.graph.links.forEach((l, i) => {
    if (l.tree && !show) return;
    if (S.hidden.has(l.source) || S.hidden.has(l.target)) return;
    S.edgeMap[i] = l; const s = H(l);
    const arrows = s.arrows === "none" ? "" : s.arrows === "both" ? "to, from" : (s.arrows || "to");
    out.push({id:i, from:l.source, to:l.target, arrows,
      label:l.tree || (S.hideLab || {}).link ? "" : l.type, dashes:s.dash === true, width:num(s.width, 1),
      color:{color:s.color || (l.tree ? "#5a5a5a" : linkColor(l.type)), highlight:"#3794ff", hover:"#3794ff", opacity:num(s.opacity, 1)},
      font:{size:10, align:"middle", color:PAL.link, strokeWidth:3, strokeColor:"#1e1e1e"}});
  });
  return out;
}
function render(g) {
  S.graph = g; S.byId = Object.fromEntries(g.nodes.map(n => [n.id, n]));
  S.bad = new Set(g.graph.errors.filter(e => !e.file).map(e => e.line));
  if (S.foldKey !== foldKey()) { S.foldKey = foldKey(); S.folded = loadFold(); }
  const wasHidden = S.hidden; buildFold(g);
  const saved = loadPos(), old = new Set(nodesDS.getIds()), fresh = !old.size;
  const view = net.getViewPosition(); let missing = 0;
  const items = g.nodes.map(n => {
    const v = visNode(n);
    if (old.has(n.id) && wasHidden.has(n.id) && !S.hidden.has(n.id) && !saved[n.id]) {
      const par = [...(S.parents[n.id] || [])].find(p => !S.hidden.has(p));     // vừa bung: đặt cạnh node cha
      const q = par ? net.getPositions([par])[par] : view;
      v.x = q.x + (Math.random() - .5) * 160; v.y = q.y + 70 + Math.random() * 40;
    }
    if (!old.has(n.id)) {
      let p = S.pending[n.id] || saved[n.id];
      if (!p && !fresh) {
        const par = n.parent && old.has(n.parent) ? net.getPositions([n.parent])[n.parent] : view;
        p = {x:par.x + (Math.random() - .5) * 160, y:par.y + 70 + Math.random() * 40};
      }
      if (p) { v.x = p.x; v.y = p.y; } else missing++;
    }
    return v;
  });
  S.pending = {};
  nodesDS.remove([...old].filter(id => !S.byId[id]));
  nodesDS.update(items);
  edgesDS.clear(); edgesDS.add(visEdges());
  if (fresh && missing) {
    net.setOptions({physics:{enabled:true}});
    net.once("stabilizationIterationsDone", () => { net.setOptions({physics:{enabled:false}}); savePos(); net.fit(); });
    net.stabilize(300);
  } else if (fresh) net.fit();
  fillLinkSel(g); showLog(g); updateGutter(); renderViews();
  fillLists(g); renderExplorer(); renderInspector();
  if (S.mode === "link") net.addEdgeMode();
}
function linkTypes(g) {        // loại link chọn được khi nối: schema khai báo, hoặc đã dùng + needs, part-of
  const declared = Object.keys(g.graph.schema.links || {});
  const used = g.links.filter(l => !l.tree && !AUTO_LINKS.includes(l.type)).map(l => l.type);
  return declared.length ? declared : [...new Set([...used, "needs", "part-of"])];
}
function fillLists(g) {        // datalist cho Inspector: node, khóa meta, loại link
  const opt = (v, label) => `<option value="${esc(v)}">${label ? esc(label) : ""}</option>`;
  const names = g.graph.import_names || {};
  const ref = n => {            // tên viết trong link: node import lẻ viết ngắn, node của module viết đủ
    if (n.kind !== "external") return n.id;
    const i = n.id.indexOf("."), mod = n.id.slice(0, i), name = n.id.slice(i + 1);
    return names[name] === mod ? name : n.id;
  };
  $("#dlNodes").innerHTML = g.nodes.filter(n => n.kind !== "section" || !n.auto_id).map(n => opt(ref(n), n.title)).join("");
  const keys = new Set([...Object.keys(g.graph.schema.keys || {}), "type", "contain"]);
  g.nodes.forEach(n => Object.keys(n.meta || {}).forEach(k => keys.add(k)));
  $("#dlKeys").innerHTML = [...keys].map(k => opt(k, (g.graph.schema.keys[k] || {}).title)).join("");
  $("#dlLinks").innerHTML = linkTypes(g).map(t => opt(t)).join("");
}
function fillLinkSel(g) {
  const sel = $("#linkSel"), cur = sel.value;
  const opts = linkTypes(g);
  sel.innerHTML = opts.map(t => `<option>${esc(t)}</option>`).join("");
  if (opts.includes(cur)) sel.value = cur;
}
function showLog(g) {
  const L = [...g.graph.errors.map(e => ({...e, c:"err", t:"Lỗi"})), ...g.graph.warnings.map(e => ({...e, c:"warn", t:"Cảnh báo"}))];
  $("#log").innerHTML = L.length
    ? L.map((e, i) => `<div class="${e.c}" data-i="${i}">${e.t} ${e.file ? esc(e.file) + ":" : "dòng "}${e.line}: ${esc(e.msg)}</div>`).join("")
    : '<span style="color:var(--mute)">Không có lỗi.</span>';
  const ne = g.graph.errors.length, nw = g.graph.warnings.length;
  $("#nprob").textContent = ne + nw;
  $("#sbProb").textContent = `⊗ ${ne}  ⚠ ${nw}`;
  $$("#log [data-i]").forEach(d => d.onclick = () => { const e = L[+d.dataset.i]; if (!e.file) jumpTo(e.line, true); });
}

// ---------- chế độ, sự kiện đồ thị ----------
const AUTO_LINKS = ["mention", "contain"];   // parser sinh từ @id / meta contain: sửa trong văn bản
const HINT = {
  fold:"Bấm node cha (▾) để thu gọn các node con part-of / contain · bấm lại (▸) để bung",
  select:"Kéo node để sắp xếp · bấm node: nhảy tới dòng · nhấp đúp: đổi tiêu đề · Delete: xóa node/link",
  add:"Bấm nền: thêm node cuối file · bấm một section: thêm node vào section đó",
  link:"Kéo từ node nguồn sang node đích để nối (loại link chọn ở menu)",
  move:"Kéo node thả lên một section để chuyển node sang section đó"};
function setMode(m) {
  S.mode = m;
  $$("[data-mode]").forEach(b => b.classList.toggle("on", b.dataset.mode === m));
  net.disableEditMode(); if (m === "link") net.addEdgeMode();
  $("#hint").textContent = ST && m !== "fold" ? "Bản tĩnh: chỉ xem. Sửa bằng: king serve" : HINT[m];
}
net.on("click", async p => {
  const a = document.activeElement;              // bấm vào đồ thị: rời ô nhập để phím tắt dùng cho node
  if (a && a !== document.body && a.matches("input,textarea,select")) a.blur();
  if (S.mode === "fold") { if (p.nodes[0]) toggleFold(p.nodes[0]); return; }
  if (S.mode === "add" && !ST) {
    const id = p.nodes[0], n = id && S.byId[id];
    if (n && n.kind !== "section") return;
    const t = (prompt(n ? `Node mới trong section "${n.title}" (có thể viết "id: Tiêu đề"):`
                        : 'Node mới ở cuối file (có thể viết "id: Tiêu đề"):') || "").trim();
    if (!t) return;
    const m = t.match(/^([a-z0-9][a-z0-9-]*)\s*:\s*(.+)$/);
    let pt = p.pointer.canvas;
    if (n) { const q = net.getPositions([id])[id]; pt = {x:q.x + (Math.random() - .5) * 120, y:q.y + 80}; }
    await op("add_node", {title:m ? m[2] : t, id:m ? m[1] : null, section:n ? id : null}, r => { S.pending[r.id] = pt; });
    return;
  }
  const id = p.nodes[0];
  if (id && S.byId[id] && S.byId[id].kind !== "external") jumpTo(S.byId[id].line);
  else if (!id && p.edges.length) { const l = S.edgeMap[p.edges[0]]; if (l && l.line) jumpTo(l.line); }
});
net.on("doubleClick", async p => {
  if (ST || S.mode !== "select" || !p.nodes.length) return;
  const n = S.byId[p.nodes[0]]; if (!n || n.kind === "external") return;
  const t = (prompt("Tiêu đề mới cho " + n.id + (n.auto_id ? " (section không có @id: ID sẽ đổi theo)" : "") + ":", n.title) || "").trim();
  if (t && t !== n.title) await op("rename", {id:n.id, title:t});
});
net.on("select", p => {
  fillFormat();
  if (p.nodes.length) focusNode(p.nodes[0], false);
  else if (p.edges.length && S.edgeMap[p.edges[0]]) selectLink(S.edgeMap[p.edges[0]]);
});
const inBox = (b, c) => b && c.x >= b.left && c.x <= b.right && c.y >= b.top && c.y <= b.bottom;
net.on("dragEnd", async p => {
  if (!p.nodes.length) return;
  savePos();
  if (S.mode !== "move" || ST) return;
  const c = p.pointer.canvas;
  const tgt = S.graph.nodes.find(n => n.kind === "section" && !p.nodes.includes(n.id) && inBox(net.getBoundingBox(n.id), c));
  const ids = p.nodes.filter(id => S.byId[id] && S.byId[id].kind === "node" && (!tgt || S.byId[id].parent !== tgt.id));
  if (tgt && ids.length) await op("move_node", {ids, section:tgt.id});
});
async function onAddEdge(d) {
  if (d.from === d.to) { net.addEdgeMode(); return; }
  const type = $("#linkSel").value;
  if (!type) { alert("Chưa có loại link. Thêm bằng Schema → + Link."); return; }
  await op("add_link", {source:d.from, target:d.to, type});
  if (S.mode === "link") net.addEdgeMode();
}
document.addEventListener("keydown", async e => {
  const typing = ["TEXTAREA", "INPUT", "SELECT"].includes(document.activeElement.tagName);
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && k === "s") { e.preventDefault(); await save(); return; }
  if (typing || ST || $("#dlg").open) return;
  if ((e.ctrlKey || e.metaKey) && k === "z") { e.preventDefault(); await undo(); return; }
  if (e.key !== "Delete" && e.key !== "Backspace") return;
  const ns = net.getSelectedNodes().filter(id => S.byId[id] && S.byId[id].kind === "node");
  const es = net.getSelectedEdges().map(i => S.edgeMap[i]).filter(l => l && !l.tree && !AUTO_LINKS.includes(l.type));
  if (ns.length) { if (confirm("Xóa node " + ns.join(", ") + " khỏi " + S.name + "?")) await op("delete_node", {ids:ns}); }
  else if (es.length) await op("delete_link", {links:es.map(l => ({source:l.source, target:l.target, type:l.type}))});
  else if (net.getSelectedEdges().length) status("Cạnh chứa, meta contain và tham chiếu @ sửa trong văn bản.");
});

// ---------- Ctrl+C / Ctrl+X / Ctrl+V / Ctrl+/ trên node (đồ thị, Tree, Book) ----------
const onGraph = () => { const a = document.activeElement; return !a || a === document.body || !a.matches("input,textarea,select,[contenteditable]"); };
function pickedNodes() {
  const ids = net.getSelectedNodes().filter(id => S.byId[id] && S.byId[id].kind === "node");
  if (!ids.length && S.selected && S.byId[S.selected] && S.byId[S.selected].kind === "node") ids.push(S.selected);
  return ids;
}
function nodeText(id) {          // khối văn bản của node: từ dòng @id tới trước node / heading kế tiếp
  const L = S.text.split("\n"), i = S.byId[id].line - 1;
  const starts = new Set(S.graph.nodes.filter(n => n.kind !== "external" && n.line).map(n => n.line - 1));
  let j = i + 1;
  while (j < L.length && !starts.has(j)) j++;
  while (j > i + 1 && !L[j - 1].trim()) j--;
  return L.slice(i, j).join("\n");
}
function copyNodes(e, cut) {
  if (!onGraph() || !S.graph || String(getSelection()).trim()) return;   // đang bôi đen chữ: chép chữ như thường
  const ids = pickedNodes().sort((a, b) => S.byId[a].line - S.byId[b].line);
  if (!ids.length) return;
  e.preventDefault();
  e.clipboardData.setData("text/plain", ids.map(nodeText).join("\n\n") + "\n");
  status((cut ? "Đã cắt " : "Đã sao chép ") + ids.join(", ") + " · Ctrl+V để dán thành node mới");
  if (cut && !ST) op("delete_node", {ids});
}
document.addEventListener("copy", e => copyNodes(e, false));
document.addEventListener("cut", e => copyNodes(e, true));
document.addEventListener("paste", async e => {
  if (!onGraph() || ST || !S.name) return;
  const clip = e.clipboardData && e.clipboardData.getData("text/plain");
  if (!clip || !/^\s*@[a-z0-9]/m.test(clip)) return;
  e.preventDefault();
  // dán vào section của node đang chọn (hoặc section đang chọn); không chọn gì thì dán cuối file
  const cur = S.selected && S.byId[S.selected];
  const section = cur ? (cur.kind === "section" ? cur.id : cur.parent) : null;
  const r = await op("paste_nodes", {clip, section: section && S.byId[section] && S.byId[section].kind === "section" ? section : null},
    r => { const c = net.getViewPosition(); r.ids.forEach((id, k) => { S.pending[id] = {x:c.x + 40 + k * 30, y:c.y + 40 + k * 30}; }); });
  if (r && r.ids) { net.selectNodes(r.ids.filter(id => nodesDS.get(id))); focusNode(r.ids[0], false); }
});
document.addEventListener("keydown", e => {
  if (!(e.ctrlKey || e.metaKey) || !(e.key === "/" || e.code === "Slash") || !onGraph() || ST) return;
  const ids = pickedNodes();
  if (!ids.length) return;
  e.preventDefault();
  S.selected = null; op("comment_nodes", {ids});
});

// ---------- format → style.kg.md ----------
function fillFormat() {
  const ns = net.getSelectedNodes(), n = ns.length === 1 && S.byId[ns[0]], s = n ? H(n) : {};
  $$("#fmt [data-p]").forEach(el => {
    const v = s[el.dataset.p];
    if (el.type === "color") { if (/^#[0-9a-f]{6}$/i.test(v || "")) el.value = v; }
    else el.value = v === undefined ? "" : String(v);
  });
}
const LINKMAP = {color:"color", "border-color":"color", border:"width", dash:"dash"};
function targets() {
  const ns = net.getSelectedNodes();
  if (ns.length) return {sel:ns.map(id => "#" + id)};
  const ls = net.getSelectedEdges().map(i => S.edgeMap[i]).filter(Boolean);
  if (ls.length) return {sel:[...new Set(ls.map(l => "link=" + l.type))], link:true};
  return null;
}
async function applyFmt(p, v) {
  const t = targets();
  if (!t) return status("Chọn node hoặc link trước khi format.", "err");
  let k = p;
  if (t.link) { k = LINKMAP[p]; if (!k) return status("Thuộc tính này không áp cho link.", "err"); }
  await op("set_style", {selectors:t.sel, props:{[k]:v}});
}
$$("#fmt [data-p]").forEach(el => el.addEventListener("change", () => {
  let v = el.value; if (v === "") return;
  if (el.type === "number") v = +v;
  if (el.dataset.p === "dash") v = v === "true";
  applyFmt(el.dataset.p, v);
}));
$("#bClear").onclick = async () => { const t = targets(); if (t) await op("set_style", {selectors:t.sel, props:null}); else status("Chọn node hoặc link trước.", "err"); };

// ---------- schema ----------
$$("[data-schema]").forEach(b => b.onclick = async () => {
  const kind = b.dataset.schema, L = {type:"kiểu node", key:"khóa meta", link:"loại link"}[kind];
  const id = (prompt(`ID ${L} mới (a-z, 0-9, -):`) || "").trim(); if (!id) return;
  const title = (prompt("Tên hiển thị (có thể bỏ trống):") || "").trim(), extra = {};
  if (kind === "type") {
    const a = (prompt("Các khóa meta kiểu này được dùng, ngăn bằng dấu phẩy (bỏ trống = mọi khóa):") || "").trim();
    if (a) extra.allow = a;
  } else if (kind === "key") {
    const v = (prompt('Giá trị cho phép ngăn bằng | (ví dụ "Nạp | Xuất"), hoặc bool / int / number / text (bỏ trống = tự do):') || "").trim();
    if (/^(bool|int|number|text)$/.test(v)) extra.value = v; else if (v) extra.values = v;
    if (confirm("Bắt buộc với các kiểu node có khóa này trong allow?")) extra.required = true;
  } else {
    if (confirm("Cấm vòng lặp (dag)?")) extra.dag = true;
    const to = (prompt("Đích phải có type nào? (bỏ trống = bất kỳ)") || "").trim(); if (to) extra.to = to;
  }
  await op("schema_add", {kind, id, title, extra});
});

// ---------- SVG ----------
function poly(s, x, y, r) {
  let p = [];
  if (s === "diamond") p = [[x, y - r], [x + r, y], [x, y + r], [x - r, y]];
  else if (s === "triangle") p = [[x, y - r], [x + r * .866, y + r * .5], [x - r * .866, y + r * .5]];
  else if (s === "hexagon") for (let i = 0; i < 6; i++) { const a = Math.PI / 3 * i; p.push([x + r * Math.cos(a), y + r * Math.sin(a)]); }
  else for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + Math.PI / 5 * i, q = i % 2 ? r * .45 : r; p.push([x + q * Math.cos(a), y + q * Math.sin(a)]); }
  return p.map(q => q.map(v => v.toFixed(1)).join(",")).join(" ");
}
function exportSVG() {
  const ids = nodesDS.getIds({filter:n => !n.hidden}); if (!ids.length) return status("Đồ thị trống.", "err");
  const pos = net.getPositions(), G = {}, OUT = new Set(["dot", "star", "triangle", "diamond", "square", "hexagon"]);
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const id of ids) {
    const n = nodesDS.get(id), b = net.getBoundingBox(id), out = OUT.has(n.shape) || !!n.kg;
    let g;
    if (n.kg) {                       // hình tự vẽ (elip, tròn, chữ nhật, vuông): nhãn dưới hình
      g = {n, out, kg:n.kg, cx:pos[id].x, cy:pos[id].y, rx:n.kg.w / 2, ry:n.kg.h / 2};
      if (n.kg.shape === "circle") g.r = n.kg.w / 2;
      b.left = g.cx - Math.max(g.rx, 75); b.right = g.cx + Math.max(g.rx, 75); b.top = g.cy - g.ry; b.bottom = g.cy + g.ry + 40;
    } else g = out ? {n, out, cx:pos[id].x, cy:pos[id].y, r:n.size}
                   : {n, out, cx:(b.left + b.right) / 2, cy:(b.top + b.bottom) / 2, rx:(b.right - b.left) / 2, ry:(b.bottom - b.top) / 2};
    G[id] = g; x0 = Math.min(x0, b.left); y0 = Math.min(y0, b.top); x1 = Math.max(x1, b.right); y1 = Math.max(y1, b.bottom);
  }
  const pad = 24, W = x1 - x0 + 2 * pad, Hh = y1 - y0 + 2 * pad, X = v => (v - x0 + pad).toFixed(1), Y = v => (v - y0 + pad).toFixed(1);
  const clip = (g, dx, dy) => {
    const L = Math.hypot(dx, dy) || 1; let t;
    if (g.r !== undefined) t = g.r / L;
    else if ((g.kg ? g.kg.shape : g.n.shape) === "ellipse") t = 1 / Math.sqrt((dx / g.rx) ** 2 + (dy / g.ry) ** 2);
    else t = Math.min(g.rx / (Math.abs(dx) || 1e-9), g.ry / (Math.abs(dy) || 1e-9));
    return [g.cx + dx * t, g.cy + dy * t];
  };
  const marks = {}; let defs = "", body = "";
  const mk = c => { if (!(c in marks)) { const k = "m" + Object.keys(marks).length; marks[c] = k;
    defs += `<marker id="${k}" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="${c}"/></marker>`; } return marks[c]; };
  for (const e of edgesDS.get()) {
    const a = G[e.from], b = G[e.to]; if (!a || !b || a === b) continue;
    const dx = b.cx - a.cx, dy = b.cy - a.cy, [sx, sy] = clip(a, dx, dy), [ex, ey] = clip(b, -dx, -dy), c = e.color.color, m = mk(c);
    body += `<line x1="${X(sx)}" y1="${Y(sy)}" x2="${X(ex)}" y2="${Y(ey)}" stroke="${c}" stroke-width="${e.width}"` +
      (e.dashes ? ' stroke-dasharray="5,4"' : "") + (e.color.opacity < 1 ? ` opacity="${e.color.opacity}"` : "") +
      (e.arrows.includes("to") ? ` marker-end="url(#${m})"` : "") + (e.arrows.includes("from") ? ` marker-start="url(#${m})"` : "") + "/>";
    if (e.label) body += `<text x="${X((sx + ex) / 2)}" y="${Y((sy + ey) / 2)}" font-family="system-ui,sans-serif" font-size="10" fill="#555" text-anchor="middle" dominant-baseline="central" stroke="#fff" stroke-width="3" paint-order="stroke">${esc(e.label)}</text>`;
  }
  for (const id of ids) {
    const g = G[id], n = g.n, cx = +X(g.cx), cy = +Y(g.cy), r = g.r;
    if (g.kg) {
      const m = g.kg, st = `fill="${esc(m.bg)}" stroke="${esc(m.bd)}" stroke-width="${m.bw}"` +
        (m.dash ? ' stroke-dasharray="5,4"' : "") + (m.opacity < 1 ? ` opacity="${m.opacity}"` : "");
      body += m.shape === "ellipse" ? `<ellipse cx="${cx}" cy="${cy}" rx="${g.rx.toFixed(1)}" ry="${g.ry.toFixed(1)}" ${st}/>`
        : m.shape === "circle" ? `<circle cx="${cx}" cy="${cy}" r="${g.r.toFixed(1)}" ${st}/>`
        : `<rect x="${(cx - g.rx).toFixed(1)}" y="${(cy - g.ry).toFixed(1)}" width="${(2 * g.rx).toFixed(1)}" height="${(2 * g.ry).toFixed(1)}" rx="${Math.min(m.radius, g.ry)}" ${st}/>`;
      if (m.label) {
        const fill = svgText(m.fontColor);
        _cx.font = `${m.fontSize}px ${m.font}`;
        wrapLabel(_cx, m.label, 150).forEach((t, i) => {
          body += `<text x="${cx}" y="${(cy + g.ry + 4 + i * (m.fontSize + 2)).toFixed(1)}" font-family="${esc(m.font)}" font-size="${m.fontSize}" fill="${esc(fill)}" text-anchor="middle" dominant-baseline="hanging">${esc(t)}</text>`;
        });
      }
      continue;
    }
    const st = `fill="${n.color.background}" stroke="${n.color.border}" stroke-width="${n.borderWidth}"` +
      (n.shapeProperties.borderDashes ? ' stroke-dasharray="5,4"' : "") + (n.opacity < 1 ? ` opacity="${n.opacity}"` : "");
    let shp = "";
    if (n.shape === "ellipse") shp = `<ellipse cx="${cx}" cy="${cy}" rx="${g.rx.toFixed(1)}" ry="${g.ry.toFixed(1)}" ${st}/>`;
    else if (n.shape === "circle" || n.shape === "dot") shp = `<circle cx="${cx}" cy="${cy}" r="${r.toFixed(1)}" ${st}/>`;
    else if (n.shape === "square") shp = `<rect x="${(cx - r).toFixed(1)}" y="${(cy - r).toFixed(1)}" width="${2 * r}" height="${2 * r}" ${st}/>`;
    else if (g.out) shp = `<polygon points="${poly(n.shape, cx, cy, r)}" ${st}/>`;
    else if (n.shape !== "text") shp = `<rect x="${(cx - g.rx).toFixed(1)}" y="${(cy - g.ry).toFixed(1)}" width="${(2 * g.rx).toFixed(1)}" height="${(2 * g.ry).toFixed(1)}" rx="5" ${st}/>`;
    const f = n.font, ty = g.out ? cy + r + f.size * .9 : cy;
    const fill = svgText(f.color);     // SVG nền trắng: chữ sáng mặc định đổi lại tối
    body += shp + `<text x="${cx}" y="${ty.toFixed(1)}" font-family="${esc(f.face)}" font-size="${f.size}" fill="${fill}" text-anchor="middle" dominant-baseline="central"${n.opacity < 1 ? ` opacity="${n.opacity}"` : ""}>${esc(n.label)}</text>`;
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W.toFixed(0)}" height="${Hh.toFixed(0)}" viewBox="0 0 ${W.toFixed(1)} ${Hh.toFixed(1)}"><defs>${defs}</defs><rect width="100%" height="100%" fill="#fff"/>${body}</svg>`;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([svg], {type:"image/svg+xml"}));
  a.download = (S.name || "graph").replace(/\.kg\.md$/, "") + ".svg"; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000); status("Đã xuất " + a.download);
}
