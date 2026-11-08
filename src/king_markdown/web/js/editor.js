// editor.js - trạng thái chung, gọi API, khung văn bản (có tô màu), mở/lưu file
const ST = /*KG_STATIC*/null;   // king html thay bằng dữ liệu → chế độ chỉ xem
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const num = (v, d) => { const x = parseFloat(v); return isNaN(x) ? d : x; };
const H = x => (x.style && x.style.html) || {};
const S = {root:"", name:"", text:"", dirty:false, mtime:0, side:0, graph:null, byId:{}, edgeMap:{},
           mode:"select", view:"graph", pending:{}, hl:0, bad:new Set(), undo:[],
           kids:{}, parents:{}, folded:new Set(), hidden:new Set(), foldKey:null};
const src = $("#src"), gut = $("#gut"), hlEl = $("#hl");

// ---------- tiện ích ----------
function status(msg, kind) {
  const el = $("#status"); el.textContent = msg; el.title = msg; el.className = kind || "";
  $("#fname").classList.toggle("dirty", S.dirty);
}
async function api(path, body) {
  const r = await fetch(path, body === undefined ? {} :
    {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
  const j = await r.json().catch(() => ({error:"HTTP " + r.status}));
  if (!r.ok || j.error) throw new Error(j.error || ("HTTP " + r.status));
  return j;
}
const posKey = () => "kgpos:" + (S.root || "static") + "|" + S.name;
function loadPos() { try { return JSON.parse(localStorage.getItem(posKey()) || "{}"); } catch (e) { return {}; } }
function savePos() {   // chỉ ghi node đang hiện; node đang bị thu gọn giữ vị trí cũ
  try { localStorage.setItem(posKey(), JSON.stringify({...loadPos(), ...net.getPositions(nodesDS.getIds({filter:n => !n.hidden}))})); } catch (e) {}
}
const foldKey = () => "kgfold:" + (S.root || "static") + "|" + S.name;
function loadFold() { try { return new Set(JSON.parse(localStorage.getItem(foldKey()) || "[]")); } catch (e) { return new Set(); } }
function saveFold() { try { localStorage.setItem(foldKey(), JSON.stringify([...S.folded])); } catch (e) {} }

// ---------- màu riêng cho từng khóa meta / loại link ----------
const PALETTE = ["#4fc1ff", "#c586c0", "#dcdcaa", "#4ec9b0", "#ce9178", "#f48771", "#b5cea8", "#d7ba7d", "#c5a5ff", "#9cdcfe"];
function hashColor(s, salt) {
  let h = salt || 7; for (const c of String(s)) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}
// bộ màu chung cho khung văn bản và 4 view (khớp các biến --k-* trong app.css)
const PAL = {sec:"#4fa3ff", node:"#f5e3a1", link:"#f0a04b", meta:"#f48fb8", val:"#c9915e", text:"#ffffff"};
const keyColor = () => PAL.meta;            // khóa meta: hồng ở mọi nơi
const _cx = document.createElement("canvas").getContext("2d");
function readable(c) {         // chữ trên nền tối: màu quá tối (blue, black, navy…) thì pha trắng cho dễ đọc
  _cx.fillStyle = "#000000"; _cx.fillStyle = String(c || "");
  const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(_cx.fillStyle);
  if (!m) return c;
  const [r, g, b] = m.slice(1).map(x => parseInt(x, 16));
  if (0.2126 * r + 0.7152 * g + 0.0722 * b >= 110) return c;
  const mix = x => Math.round(x + (255 - x) * 0.55);
  return `rgb(${mix(r)},${mix(g)},${mix(b)})`;
}
const linkText = () => PAL.link;            // tên loại link dạng chữ (Tree, Book, Inspector): cam; màu đường nối vẫn theo style
function linkColor(t) {        // style.kg.md (select="link=loại", html.color) thắng; không có thì màu theo tên
  const l = S.graph && S.graph.links.find(l => l.type === t && !l.tree && H(l).color);
  return l ? H(l).color : LINK_ORANGE;
}
const LINK_ORANGE = "#f0a04b";      // màu mặc định của link: cam (cùng bộ màu với khung văn bản và style hệ thống)

// ---------- tô màu văn bản .kg.md: chỉ 4 màu ----------
// section: xanh dương · node / module import / ID được tham chiếu: vàng nhạt · loại link: cam · meta và khóa của nó: hồng.
// Phần còn lại giữ màu chữ thường (comment làm mờ).
const FIELDS = ["content", "meta", "link", "show", "ask"];
const span = (cls, s, color) => `<span class="${cls}"${color ? ` style="color:${esc(color)}"` : ""}>${esc(s)}</span>`;
function splitComment(line) {
  const m = line.match(/(^|\s)\/\//);
  return m ? [line.slice(0, m.index + m[1].length), line.slice(m.index + m[1].length)] : [line, ""];
}
function hlInline(s) {
  let out = "", last = 0;
  const re = /(`[^`]*`)|(\*\*[^*]+\*\*)|(%%.*?%%)|((?:^|(?<=\s))@[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)?)/g;
  for (const m of s.matchAll(re)) {
    out += esc(s.slice(last, m.index));
    out += span(m[1] ? "t-code" : m[2] ? "t-bold" : m[3] ? "t-com" : "t-ref", m[0]);
    last = m.index + m[0].length;
  }
  return out + esc(s.slice(last));
}
const hlValue = v => span("t-val", v);          // giá trị sau dấu '=': nâu
function hlMeta(v) {
  const parts = []; let buf = "", q = null;
  for (const c of v) {
    if (q) { buf += c; if (c === q) q = null; }
    else if (c === '"' || c === "'") { buf += c; q = c; }
    else if (c === ",") { parts.push(buf); parts.push(","); buf = ""; }
    else buf += c;
  }
  parts.push(buf);
  return parts.map(p => {
    if (p === ",") return ",";
    const m = p.match(/^(\s*)([^=]*?)(\s*=\s*)([\s\S]*)$/);
    if (!m) { const k = p.trim(); return k ? esc(p.slice(0, p.indexOf(k))) + span("t-meta", k) + esc(p.slice(p.indexOf(k) + k.length)) : esc(p); }
    return esc(m[1]) + span("t-meta", m[2]) + esc(m[3]) + hlValue(m[4]);
  }).join("");
}
function hlLinks(v) {
  let out = "", last = 0;
  for (const m of v.matchAll(/([a-z][a-z0-9-]*)(!?)\(([^)]*)\)/g)) {
    out += esc(v.slice(last, m.index)) + span("t-link", m[1]) +
      (m[2] ? span("t-link", "!") : "") + "(" + span("t-ref", m[3]) + ")";
    last = m.index + m[0].length;
  }
  return out + esc(v.slice(last));
}
// nội dung thường: trắng (riêng @tham chiếu vàng, `code` giữ nguyên)
const hlText = s => `<span class="t-text">${hlInline(s)}</span>`;
function highlight(text) {
  const L = text.split("\n"), out = [];
  let fm = L[0] && L[0].trim() === "---" ? 1 : 0, fence = false, inNode = false, field = null, br = false;
  L.forEach((raw, i) => {
    if (br) {                                   // nội dung [ ... ] nhiều dòng: chữ thường tới dấu ']'
      br = !raw.trim().endsWith("]");
      out.push(hlText(raw)); return;
    }
    if (fm) {
      if (i > 0 && raw.trim() === "---") fm = 0;
      // frontmatter: tên module / node được import tô vàng nhạt như node
      const m = raw.match(/^(\s*)([^:]+)(:)(.*)$/), imp = m && /^(import|from\s)/.test(m[2].trim());
      out.push(raw.trim() === "---" ? span("t-fm", raw) : m ? esc(m[1]) + span("t-fm", m[2]) + m[3] + (imp ? span("t-ref", m[4]) : esc(m[4])) : esc(raw));
      return;
    }
    if (/^\s*(```|~~~)/.test(raw)) { fence = !fence; out.push(span("t-fence", raw)); return; }
    if (fence) { out.push(span("t-code", raw)); return; }
    const [code, com] = splitComment(raw), tail = com ? span("t-com", com) : "";
    let m;
    if ((m = code.match(/^(#{1,6}\s+)(.*?)(\s+@[a-z0-9][a-z0-9-]*)?(\s*)$/))) {
      inNode = false; field = null;
      // tiêu đề section xanh dương; @id của section vàng nhạt như mọi ID
      out.push(span("t-head", m[1] + m[2]) + (m[3] ? span("t-id", m[3]) : "") + esc(m[4]) + tail); return;
    }
    if ((m = code.match(/^(\s*)(@[a-z0-9][a-z0-9-]*)(\s*:\s*)?(.*)$/))) {
      inNode = true; field = null;
      out.push(esc(m[1]) + span("t-id", m[2]) + esc(m[3] || "") + span("t-text", m[4]) + tail); return;
    }
    if (inNode && (m = code.match(/^(\s*[-*]\s+)([a-z][a-z0-9-]*)(\s*:\s*)(.*)$/))) {
      // tên trường (meta, content, link, ask, show) hồng; trường lạ gạch đỏ
      const f = m[2], ok = FIELDS.includes(f); field = ok ? f : null;
      const v = m[4], text = f === "content" || f === "ask";
      if (text && v.trim().startsWith("[") && !v.includes("]")) br = true;   // mở nội dung [ ... ] nhiều dòng
      const val = f === "meta" ? hlMeta(v) : f === "link" ? hlLinks(v) : f === "show" ? hlValue(v) : hlText(v);
      out.push(esc(m[1]) + `<span class="t-meta"${ok ? "" : ' style="color:var(--err);text-decoration:underline wavy"'}>${esc(f)}</span>` +
        esc(m[3]) + val + tail); return;
    }
    if (!code.trim()) { if (["link", "meta", "show"].includes(field)) field = null; out.push(esc(code) + tail); return; }
    out.push((inNode && field === "link" ? hlLinks(code) : hlText(code)) + tail);
  });
  return out.join("\n") + "\n ";
}
let hlPending = false;
function paint() {
  if (hlPending) return; hlPending = true;
  requestAnimationFrame(() => {
    hlPending = false;
    const html = highlight(S.text);
    if (S.wrap) {        // mỗi dòng một khối để đo chiều cao sau khi ngắt, rồi kéo lề số dòng cho khớp
      hlEl.innerHTML = html.replace(/\n $/, "").split("\n").map(l => `<div class="ln">${l || " "}</div>`).join("");
      gut.innerHTML = gutterHTML([...hlEl.children].map(d => d.offsetHeight));
    } else hlEl.innerHTML = html;
    syncScroll();
  });
}
function syncScroll() { hlEl.scrollTop = src.scrollTop; hlEl.scrollLeft = src.scrollLeft; gut.scrollTop = src.scrollTop; }

// ---------- khung trái ----------
function gutterHTML(heights) {     // heights: chiều cao từng dòng khi ngắt dòng (Alt+Z)
  const n = S.text.split("\n").length; let h = "";
  for (let i = 1; i <= n; i++) {
    const c = (S.bad.has(i) ? "e " : "") + (i === S.hl ? "h" : "");
    h += heights ? `<div class="${c}" style="height:${heights[i - 1] || 20}px">${i}</div>`
                 : (c ? `<span class="${c}">${i}</span>` : i) + "\n";
  }
  return h;
}
function updateGutter() {
  if (!S.wrap) gut.innerHTML = gutterHTML();     // khi ngắt dòng, paint() vẽ lề sau khi đo
  gut.scrollTop = src.scrollTop;
  $("#fname").classList.toggle("dirty", S.dirty);
  paint();
}
function setText(t, keepUndo) {
  if (!keepUndo && t !== S.text) { S.undo.push(S.text); if (S.undo.length > 50) S.undo.shift(); }
  const st = src.scrollTop; src.value = t; src.scrollTop = st;
  if (t !== S.text) S.dirty = true;
  S.text = t; updateGutter();
}
function jumpTo(line, focus) {   // focus=true: chuyển con trỏ vào khung văn bản; bấm trên đồ thị thì không (để Ctrl+C/V/ dùng cho node)
  const L = S.text.split("\n"); let off = 0;
  for (let i = 0; i < line - 1 && i < L.length; i++) off += L[i].length + 1;
  if (focus) src.focus({preventScroll:true});
  src.setSelectionRange(off, off + (L[line - 1] || "").length);
  const row = S.wrap && hlEl.children[line - 1];
  src.scrollTop = Math.max(0, row ? row.offsetTop - 60 : (line - 4) * 20); syncScroll();
  S.hl = line; updateGutter();
}
function nodeAtLine(ln) {
  let best = null;
  for (const n of (S.graph ? S.graph.nodes : [])) if (n.kind !== "external" && n.line <= ln && (!best || n.line > best.line)) best = n;
  return best;
}
function caretSync() {
  if (!S.graph) return;
  const ln = src.value.slice(0, src.selectionStart).split("\n").length;
  S.hl = ln; updateGutter();
  const best = nodeAtLine(ln);
  if (best && nodesDS.get(best.id) && !S.hidden.has(best.id)) { net.selectNodes([best.id]); fillFormat(); }
  if (best) focusNode(best.id, false);
}
let tmr;
src.addEventListener("input", () => {
  S.text = src.value; S.dirty = true; status("Đang sửa…"); updateGutter();
  clearTimeout(tmr); tmr = setTimeout(async () => { await reparse(); await save(); }, 600);
});
src.addEventListener("scroll", syncScroll);
src.addEventListener("click", caretSync);
src.addEventListener("keyup", e => { if (/^(Arrow|Page|Home|End)/.test(e.key)) caretSync(); });
// ---------- phím tắt kiểu VS Code trong khung văn bản ----------
const lineBounds = (v, a, b) => { const s = v.lastIndexOf("\n", a - 1) + 1; let e = v.indexOf("\n", b); if (e < 0) e = v.length; return [s, e]; };
function replaceRange(s, e, text, selS, selE) {    // execCommand giữ được Ctrl+Z của trình duyệt
  src.setSelectionRange(s, e); document.execCommand("insertText", false, text);
  if (selS !== undefined) src.setSelectionRange(selS, selE);
}
function toggleComment() {                           // Ctrl+/: thêm / bỏ "// " đầu các dòng đang chọn
  const v = src.value, a = src.selectionStart, b0 = src.selectionEnd;
  const b = b0 > a && v[b0 - 1] === "\n" ? b0 - 1 : b0;
  const [s, e] = lineBounds(v, a, b), lines = v.slice(s, e).split("\n"), body = lines.filter(l => l.trim());
  if (!body.length) return;
  const off = body.every(l => /^\s*\/\/ ?/.test(l)), ind = Math.min(...body.map(l => l.match(/^\s*/)[0].length));
  const t = lines.map(l => !l.trim() ? l : off ? l.replace(/^(\s*)\/\/ ?/, "$1") : l.slice(0, ind) + "// " + l.slice(ind)).join("\n");
  replaceRange(s, e, t, s, s + t.length);
}
src.addEventListener("keydown", e => {
  const mod = e.ctrlKey || e.metaKey, k = e.key.toLowerCase();
  if (e.key === "Tab") { e.preventDefault(); if (!src.readOnly) document.execCommand("insertText", false, "  "); return; }
  if (mod && (k === "/" || e.code === "Slash")) { e.preventDefault(); if (!src.readOnly) toggleComment(); return; }
  if (mod && (k === "c" || k === "x") && src.selectionStart === src.selectionEnd) {
    // không chọn gì: Ctrl+C / Ctrl+X lấy cả dòng (trình duyệt tự sao chép phần đang chọn)
    const v = src.value, p = src.selectionStart, [s, end] = lineBounds(v, p, p);
    S.lineClip = v.slice(s, end) + "\n"; S.lineMode = true;
    src.setSelectionRange(s, Math.min(end + 1, v.length));
    if (k === "c") setTimeout(() => src.setSelectionRange(p, p), 0);
  }
});
["copy", "cut"].forEach(ev => src.addEventListener(ev, () => { if (!S.lineMode) S.lineClip = null; S.lineMode = false; }));
src.addEventListener("paste", e => {                // dán cả dòng vừa sao chép: chèn lên trên dòng hiện tại
  const t = e.clipboardData && e.clipboardData.getData("text/plain");
  if (!S.lineClip || src.readOnly || src.selectionStart !== src.selectionEnd || (t !== S.lineClip && t + "\n" !== S.lineClip)) return;
  e.preventDefault();
  const p = src.selectionStart, [s] = lineBounds(src.value, p, p), n = S.lineClip.length;
  replaceRange(s, s, S.lineClip, p + n, p + n);
});

// ---------- Alt+Z: ngắt dòng ----------
function setWrap(on) {
  S.wrap = on; document.body.classList.toggle("wrap", on); src.wrap = on ? "soft" : "off";
  $$("#bWrap, #bWrap2").forEach(b => b.classList.toggle("on", on));
  try { localStorage.setItem("kgwrap", on ? "1" : ""); } catch (e) {}
  updateGutter();
}
new ResizeObserver(() => { if (S.wrap) paint(); }).observe($("#code"));

// ---------- file ----------
function showFiles(files) { S.files = files; renderExplorer(); }
async function refreshState() {
  const s = await api("/api/state"); S.root = s.root; S.files = s.files;
  showFiles(s.files); $("#sbRoot").textContent = "📁 " + s.root;
  // trang (JS) mới nhưng tiến trình Python cũ: thiếu phép sửa → Inspector không ghi được
  const need = ["set_meta", "set_field", "set_style", "add_link"], miss = need.filter(o => !(s.ops || []).includes(o));
  if (miss.length && !S.warnedOld) {
    S.warnedOld = true;
    const msg = "Server đang chạy là bản cũ (thiếu " + miss.join(", ") + "): sửa trên Inspector sẽ không lưu. Tắt server (Ctrl+C) rồi chạy lại king serve.";
    status(msg, "err"); alert(msg);
  }
  return s;
}
async function openFile(name) {
  if (S.dirty) await save();
  nodesDS.clear(); edgesDS.clear(); S.undo = []; S.graph = null; S.hl = 0; S.selected = null; S.selLink = null;
  S.name = name || ""; showFiles(S.files || []); renderInspector(true);
  if (!name) { src.value = S.text = ""; $("#fname").textContent = "(chưa mở file)"; updateGutter(); $("#log").innerHTML = ""; renderViews(); return; }
  const f = await api("/api/file?name=" + encodeURIComponent(name));
  S.mtime = f.mtime; S.side = f.side; src.value = S.text = f.text; S.dirty = false;
  $("#fname").textContent = name; $("#title").textContent = name + " — " + S.root;
  document.title = name + " · KING Markdown";
  history.replaceState(null, "", "?file=" + encodeURIComponent(name) + (S.view !== "graph" ? "&view=" + S.view : ""));
  await reparse(); status("Đã mở " + name);
}
let seq = 0;
async function reparse() {
  if (ST || !S.name) return;
  const my = ++seq;
  try { const g = await api("/api/parse", {name:S.name, text:S.text}); if (my === seq) render(g); }
  catch (e) { status(e.message, "err"); }
}
async function save() {
  if (ST || !S.name || !S.dirty) return;
  try { const r = await api("/api/save", {name:S.name, text:S.text}); S.mtime = r.mtime; S.dirty = false; status("Đã lưu " + S.name); }
  catch (e) { status("Lưu lỗi: " + e.message, "err"); }
}
async function undo() {
  if (!S.undo.length) return status("Không còn gì để hoàn tác.");
  setText(S.undo.pop(), true); S.dirty = true; await reparse(); await save(); status("Đã hoàn tác.");
}
async function op(name, args, before) {
  if (ST || !S.name) return;
  try {
    const r = await api("/api/op", {name:S.name, text:S.text, op:name, args});
    if (before) before(r);
    if (r.text !== S.text) setText(r.text);
    await reparse(); await save();
    if (r.msg) status(r.msg);
    return r;
  } catch (e) { status(e.message, "err"); alert(e.message); }
}
