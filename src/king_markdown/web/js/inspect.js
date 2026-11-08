// inspect.js - Inspector (thanh bên phải): node / link đang chọn.
// Sửa tiêu đề, meta, nội dung, link → ghi vào .kg.md; sửa format → ghi luật vào style.kg.md. Sau mỗi lần sửa, parse lại.
const SHAPES = [["ellipse", "Elip"], ["box", "Chữ nhật"], ["circle", "Tròn"], ["square", "Vuông"], ["diamond", "Thoi"],
  ["hexagon", "Lục giác"], ["triangle", "Tam giác"], ["star", "Sao"], ["dot", "Chấm"], ["database", "Trụ"], ["text", "Chỉ chữ"]];
const ARROWS = [["to", "→ ở đích"], ["from", "← ở nguồn"], ["both", "↔ hai đầu"], ["none", "không có"]];
const DASH = [["false", "liền"], ["true", "đứt"]];
const FONTS = ["system-ui", "Segoe UI", "Arial", "Times New Roman", "Georgia", "Consolas"].map(f => [f, f]);
let insClosed = new Set();
try { insClosed = new Set(JSON.parse(localStorage.getItem("kgins") || "[]")); } catch (e) {}

function selectLink(l) {
  S.selected = null; S.selLink = {source:l.source, target:l.target, type:l.type};
  markSelected(null); renderInspector(true);
}
function curLink() {
  const k = S.selLink;
  return k && S.graph && S.graph.links.find(l => l.source === k.source && l.target === k.target && l.type === k.type);
}
function insFocused() {
  const a = document.activeElement;
  return $("#inspector").contains(a) && a.matches("input,textarea,select");
}

// ---------- dựng HTML ----------
const hex = (v, d) => /^#[0-9a-f]{6}$/i.test(v || "") ? v : d;
const fmtVal = v => v === undefined || v === null ? "" : String(v);
const sec = (key, title, body) =>
  `<div class="ins-sec${insClosed.has(key) ? " closed" : ""}" data-sec="${key}"><h5>${title}</h5><div class="ins-in">${body}</div></div>`;
const row = (label, ctl) => `<div class="ins-row"><span>${label}</span>${ctl}</div>`;
const sel = (attr, list, cur, blank) => `<select ${attr}>${blank ? `<option value="">${blank}</option>` : ""}` +
  list.map(([v, l]) => `<option value="${esc(v)}"${fmtVal(cur) === v ? " selected" : ""}>${esc(l)}</option>`).join("") + "</select>";
const numIn = (attr, v, min, max, step) =>
  `<input type="number" ${attr} min="${min}" max="${max}" step="${step || 1}" value="${v === undefined ? "" : esc(v)}" placeholder="mặc định">`;
// màu có sẵn (tên màu CSS) ghi thẳng vào style.kg.md: html.color=red
const NAMED = ["red", "orange", "yellow", "green", "teal", "blue", "purple", "pink", "brown", "gray", "black", "white",
  "lightblue", "lightgreen", "lightyellow", "lightpink", "lightgray"];
function colorHex(v) {             // tên màu / #rgb / rgb() → #rrggbb cho ô chọn màu
  const c = document.createElement("canvas").getContext("2d");
  c.fillStyle = "#000000"; c.fillStyle = String(v || "");
  return /^#[0-9a-f]{6}$/i.test(c.fillStyle) ? c.fillStyle : null;
}
const colorIn = (attr, v, d) => {
  const cur = v === undefined || v === null ? "" : String(v);
  return `<div class="cc"><select ${attr} title="Màu có sẵn"><option value="">(mặc định)</option>` +
    NAMED.map(n => `<option value="${n}"${cur === n ? " selected" : ""}>■ ${n}</option>`).join("") +
    (cur && !NAMED.includes(cur) ? `<option value="${esc(cur)}" selected>${esc(cur)}</option>` : "") +
    `</select><input type="color" ${attr} value="${colorHex(cur) || d}" title="Chọn màu bất kỳ"></div>`;
};
const title = id => { const n = S.byId[id]; return n ? (n.title || id) : id; };

function valueList(n, k) {       // gợi ý giá trị cho một khóa meta
  const sc = S.graph.graph.schema, spec = sc.keys[k];
  let vals = [];
  if (k === "type") vals = Object.keys(sc.types || {});
  else if (k === "contain") vals = S.graph.nodes.filter(x => x.kind === "node" && x.id !== n.id).map(x => x.id);
  else if (spec && spec.values) vals = spec.values;
  else if (spec && spec.value === "bool") vals = ["true", "false"];
  return vals.length ? `<datalist id="dlv-${esc(k)}">${vals.map(v => `<option value="${esc(v)}">`).join("")}</datalist>` : "";
}
function linkRows(n) {
  const L = S.graph.links.filter(l => !l.tree && (l.source === n.id || l.target === n.id));
  if (!L.length) return '<div class="ins-note">Chưa có link.</div>';
  return '<div class="ins-links">' + L.map(l => {
    const out = l.source === n.id, other = out ? l.target : l.source, auto = AUTO_LINKS.includes(l.type);
    const spec = esc(JSON.stringify({source:l.source, target:l.target, type:l.type}));
    return `<div class="lk"><span class="t" style="color:${esc(linkText(l.type))};cursor:pointer" data-sellink="${spec}" title="Chọn link này">${esc(l.type)}</span>` +
      `${out ? "→" : "←"} <a data-sel="${esc(other)}" title="${esc(other)}">${esc(title(other))}</a>` +
      (auto ? `<span class="auto" title="Parser tự sinh: sửa trong văn bản (${l.type === "contain" ? "meta contain" : "@tham chiếu"})">tự sinh</span>`
            : (ST ? "" : `<button class="x" data-dellink="${spec}" title="Xóa link">×</button>`)) + "</div>";
  }).join("") + "</div>";
}
function nodeFormat(n) {
  const s = H(n);
  return row("Hình", sel('data-fmt="shape"', SHAPES, s.shape, "(mặc định)")) +
    row("Màu nền", colorIn('data-fmt="color"', s.color, "#ffffff")) +
    row("Màu viền", colorIn('data-fmt="border-color"', s["border-color"], "#607d8b")) +
    row("Màu chữ", colorIn('data-fmt="font-color"', s["font-color"], "#1f2328")) +
    row("Viền dày", numIn('data-fmt="border"', s.border, 0, 10)) +
    row("Nét viền", sel('data-fmt="dash"', DASH, s.dash, "(mặc định)")) +
    row("Bo góc", numIn('data-fmt="radius"', s.radius, 0, 40)) +
    row("Font", sel('data-fmt="font"', FONTS, s.font, "(mặc định)")) +
    row("Cỡ chữ", numIn('data-fmt="font-size"', s["font-size"], 8, 48)) +
    row("Kích thước", numIn('data-fmt="size"', s.size, 5, 300)) +
    row("Độ đậm", numIn('data-fmt="opacity"', s.opacity, 0, 1, 0.1)) +
    `<div class="ins-acts"><button class="btn" data-act="clearfmt">Xóa format riêng</button></div>` +
    `<div class="ins-note">Ghi vào style.kg.md, luật <code>select="#${esc(n.id)}"</code>. Kích thước dùng cho vuông, chấm, sao…</div>`;
}
function nodePanel(n) {
  const ext = n.kind === "external", node = n.kind === "node";
  let h = `<div class="ins-in" style="padding-top:10px"><span class="ins-kind">${esc(n.kind)}</span><span class="ins-id">${node ? "@" : ""}${esc(n.id)}</span>` +
    row("Tiêu đề", `<input type="text" data-act="title" value="${esc(n.title || "")}"${ext ? " disabled" : ""}>`) +
    `<div class="ins-acts">${!ext && n.line ? `<button class="btn" data-act="goto">Tới dòng ${n.line}</button>` : ""}` +
    (node && !ST ? '<button class="btn danger" data-act="delnode">Xóa node</button>' : "") + "</div>" +
    (n.auto_id ? '<div class="ins-note">Section chưa có @id: ID sinh từ tiêu đề nên đổi theo tiêu đề.</div>' : "") +
    (ext ? `<div class="ins-note">Node import từ module <b>${esc(n.module)}</b>: chỉ xem.</div>` : "") + "</div>";
  if (node) {
    const meta = Object.entries(n.meta || {});
    h += sec("meta", "META",
      '<div class="ins-meta">' + meta.map(([k, v]) =>
        `<span class="k" style="color:${esc(keyColor(k))}" title="${esc(k)}">${esc(k)}</span>` +
        `<input type="text" data-meta="${esc(k)}" value="${esc(fmtVal(v))}" list="dlv-${esc(k)}"><button class="x" data-delmeta="${esc(k)}" title="Xóa khóa">×</button>`
      ).join("") +
      '<input type="text" id="insNewKey" placeholder="khóa mới" list="dlKeys"><input type="text" id="insNewVal" placeholder="giá trị">' +
      '<button class="btn" data-act="addmeta" title="Thêm khóa">+</button></div>' +
      meta.map(([k]) => valueList(n, k)).join("") +
      '<div class="ins-note">Giá trị viết như trong file: true/false, số, chữ; <code>contain</code> là danh sách ID node con.</div>');
    h += sec("text", "NỘI DUNG",
      row("content", "") + `<textarea data-field="content" rows="4">${esc(n.content || "")}</textarea>` +
      row("ask", "") + `<textarea data-field="ask" rows="2" placeholder="lời dặn cho AI">${esc(n.ask || "")}</textarea>` +
      `<label style="display:flex;gap:6px;align-items:center;margin-top:6px;color:var(--mute)"><input type="checkbox" data-act="show"${n.show === "none" ? " checked" : ""}> Ẩn khỏi sách (show: none)</label>`);
  }
  h += sec("links", "LINK", linkRows(n) + (ST || ext ? "" :
    `<div class="ins-add"><input type="text" id="insLinkType" list="dlLinks" value="${esc(S.lastLinkType || $("#linkSel").value || "")}" placeholder="loại">` +
    `<input type="text" id="insLinkTarget" list="dlNodes" placeholder="node đích"><button class="btn pri" data-act="addlink">Nối</button></div>` +
    '<div class="ins-note">Hoặc dùng chế độ ⤳ Nối trên đồ thị: kéo từ node này sang node khác.</div>'));
  h += sec("format", "FORMAT", nodeFormat(n));
  return h;
}
function linkPanel(l) {
  const s = H(l), auto = AUTO_LINKS.includes(l.type) || l.tree;
  const spec = esc(JSON.stringify({source:l.source, target:l.target, type:l.type}));
  let h = `<div class="ins-in" style="padding-top:10px"><span class="ins-kind">link</span>` +
    `<span class="t" style="font:600 13px var(--mono);color:${esc(l.tree ? "#888" : linkText(l.type))}">${esc(l.type)}</span>` +
    `<div class="ins-links" style="margin-top:6px"><div class="lk">từ <a data-sel="${esc(l.source)}">${esc(title(l.source))}</a></div>` +
    `<div class="lk">tới <a data-sel="${esc(l.target)}">${esc(title(l.target))}</a></div></div>` +
    `<div class="ins-acts">${l.line ? `<button class="btn" data-act="goto" data-line="${l.line}">Tới dòng ${l.line}</button>` : ""}` +
    (!auto && !ST ? `<button class="btn danger" data-dellink="${spec}">Xóa link</button>` : "") + "</div>" +
    (auto ? `<div class="ins-note">${l.tree ? "Cạnh chứa section → node: đổi bằng cách chuyển node sang section khác." :
      l.type === "contain" ? "Sinh từ meta contain của node nguồn." : "Sinh từ @tham chiếu trong nội dung."}</div>` : "") + "</div>";
  if (!auto && !ST)
    h += sec("retype", "ĐỔI LOẠI LINK", `<div class="ins-add" style="grid-template-columns:1fr auto"><input type="text" id="insRetype" list="dlLinks" value="${esc(l.type)}">` +
      '<button class="btn" data-act="retype">Đổi</button></div>');
  h += sec("lformat", "FORMAT",
    `<div class="ins-note" style="margin-top:0">Áp cho <b>mọi link loại ${esc(l.type)}</b>: luật <code>select="link=${esc(l.type)}"</code> trong style.kg.md.</div>` +
    row("Màu", colorIn('data-lfmt="color"', s.color, colorHex(l.tree ? "#5a5a5a" : linkColor(l.type)) || "#9e9e9e")) +
    row("Độ dày", numIn('data-lfmt="width"', s.width, 1, 12)) +
    row("Nét", sel('data-lfmt="dash"', DASH, s.dash, "(mặc định)")) +
    row("Mũi tên", sel('data-lfmt="arrows"', ARROWS, s.arrows, "(mặc định: ở đích)")) +
    row("Độ đậm", numIn('data-lfmt="opacity"', s.opacity, 0, 1, 0.1)) +
    '<div class="ins-acts"><button class="btn" data-act="clearlfmt">Xóa format loại này</button></div>');
  return h;
}

function renderInspector(force) {
  const el = $("#insBody");
  if (!force && insFocused()) return;          // đang gõ trong Inspector: không vẽ đè
  const n = S.selected && S.byId[S.selected], l = !n && curLink();
  if (!S.graph || (!n && !l)) {
    el.innerHTML = `<div class="ins-empty">Chọn một node hoặc link (trên đồ thị, Tree, Book, Outline, hoặc đặt con trỏ trong văn bản) để xem và sửa.<br><br>` +
      (ST ? "" : "Tạo node: chế độ <b>＋ Node</b> trên đồ thị.<br>Nối node: chế độ <b>⤳ Nối</b>.") + "</div>";
    return;
  }
  el.innerHTML = (ST ? '<div class="ins-note" style="margin:8px 12px;color:#e2c08d">Bản tĩnh (file .html): chỉ xem, sửa ở đây không được lưu. Muốn sửa: chạy <code>king serve</code>.</div>' : "") +
    (n ? nodePanel(n) : linkPanel(l));
  wireInspector(el, n, l);
}

// ---------- sự kiện → phép sửa ----------
async function insOp(name, args) { const r = await op(name, args); renderInspector(true); return r; }
function resolveRef(v) {            // id đầy đủ, tên ngắn của node import, hoặc giữ nguyên
  v = v.trim();
  if (S.byId[v]) return v;
  const ext = S.graph.nodes.find(x => x.kind === "external" && x.id.endsWith("." + v));
  return ext ? ext.id : v;
}
function fmtValue(el) {
  let v = el.value;
  if (v === "") return null;                                      // bỏ thuộc tính
  if (el.type === "number") v = +v;
  if (el.dataset.fmt === "dash" || el.dataset.lfmt === "dash") v = v === "true";
  return v;
}
function wireInspector(el, n, l) {
  el.querySelectorAll("[data-sec]>h5").forEach(h => h.onclick = () => {
    const s = h.parentElement, k = s.dataset.sec;
    s.classList.toggle("closed");
    if (s.classList.contains("closed")) insClosed.add(k); else insClosed.delete(k);
    try { localStorage.setItem("kgins", JSON.stringify([...insClosed])); } catch (e) {}
  });
  el.querySelectorAll("[data-sel]").forEach(a => a.onclick = () => focusNode(a.dataset.sel, true));
  el.querySelectorAll("[data-sellink]").forEach(a => a.onclick = () => selectLink(JSON.parse(a.dataset.sellink)));
  el.querySelectorAll("[data-dellink]").forEach(b => b.onclick = async () => {
    const spec = JSON.parse(b.dataset.dellink);
    if (l) S.selLink = null;
    await insOp("delete_link", {links:[spec]});
  });
  const on = (q, ev, fn) => { const x = el.querySelector(q); if (x) x.addEventListener(ev, fn); };
  on('[data-act="goto"]', "click", e => jumpTo(+(e.target.dataset.line || (n && n.line)), true));

  if (n) {
    on('[data-act="title"]', "change", e => { const t = e.target.value.trim(); if (t && t !== n.title) insOp("rename", {id:n.id, title:t}); });
    on('[data-act="delnode"]', "click", async () => {
      if (!confirm(`Xóa node ${n.id} khỏi ${S.name}?`)) return;
      S.selected = null; await insOp("delete_node", {ids:[n.id]});
    });
    const setMeta = meta => insOp("set_meta", {id:n.id, meta});
    el.querySelectorAll("[data-meta]").forEach(i => i.addEventListener("change", () => {
      const meta = {...n.meta}, k = i.dataset.meta, v = i.value.trim();
      if (v === "") delete meta[k]; else meta[k] = v;
      setMeta(meta);
    }));
    el.querySelectorAll("[data-delmeta]").forEach(b => b.onclick = () => {
      const meta = {...n.meta}; delete meta[b.dataset.delmeta]; setMeta(meta);
    });
    const addMeta = () => {
      const k = $("#insNewKey").value.trim(), v = $("#insNewVal").value.trim();
      if (!k) return status("Nhập tên khóa meta.", "err");
      setMeta({...n.meta, [k]:v || "true"});
    };
    on('[data-act="addmeta"]', "click", addMeta);
    on("#insNewVal", "keydown", e => { if (e.key === "Enter") addMeta(); });
    on("#insNewKey", "input", e => {           // gợi ý giá trị theo khóa vừa gõ
      const k = e.target.value.trim(), old = el.querySelector("#dlvNew");
      if (old) old.remove();
      const html = valueList(n, k);
      if (html) { el.insertAdjacentHTML("beforeend", html.replace(`id="dlv-${esc(k)}"`, 'id="dlvNew"')); $("#insNewVal").setAttribute("list", "dlvNew"); }
    });
    el.querySelectorAll("[data-field]").forEach(t => t.addEventListener("change", () =>
      insOp("set_field", {id:n.id, key:t.dataset.field, value:t.value})));
    on('[data-act="show"]', "change", e => insOp("set_field", {id:n.id, key:"show", value:e.target.checked ? "none" : ""}));
    const addLink = async () => {
      const type = $("#insLinkType").value.trim(), target = resolveRef($("#insLinkTarget").value);
      if (!type || !target) return status("Nhập loại link và node đích.", "err");
      S.lastLinkType = type;
      await insOp("add_link", {source:n.id, target, type});
    };
    on('[data-act="addlink"]', "click", addLink);
    on("#insLinkTarget", "keydown", e => { if (e.key === "Enter") addLink(); });
    el.querySelectorAll("[data-fmt]").forEach(i => i.addEventListener("change", () =>
      insOp("set_style", {selectors:["#" + n.id], props:{[i.dataset.fmt]:fmtValue(i)}})));
    on('[data-act="clearfmt"]', "click", () => insOp("set_style", {selectors:["#" + n.id], props:null}));
  }
  if (l) {
    const selector = "link=" + l.type;
    el.querySelectorAll("[data-lfmt]").forEach(i => i.addEventListener("change", () =>
      insOp("set_style", {selectors:[selector], props:{[i.dataset.lfmt]:fmtValue(i)}})));
    on('[data-act="clearlfmt"]', "click", () => insOp("set_style", {selectors:[selector], props:null}));
    on('[data-act="retype"]', "click", async () => {
      const t = $("#insRetype").value.trim();
      if (!t || t === l.type) return;
      const spec = {source:l.source, target:l.target, type:l.type};
      if (!(await op("delete_link", {links:[spec]}))) return;
      S.selLink = {source:l.source, target:l.target, type:t};
      await insOp("add_link", {source:l.source, target:l.target, type:t});
    });
  }
}
