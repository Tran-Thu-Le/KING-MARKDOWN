// editor.js - trạng thái chung, gọi API, khung văn bản (có tô màu), mở/lưu file
const ST = /*KG_STATIC*/null;   // king html thay bằng dữ liệu → chế độ chỉ xem
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const num = (v, d) => { const x = parseFloat(v); return isNaN(x) ? d : x; };
const H = x => (x.style && x.style.html) || {};
const S = {root:"", name:"", text:"", dirty:false, mtime:0, side:0, graph:null, byId:{}, edgeMap:{},
           mode:"select", view:"graph", pending:{}, hl:0, bad:new Set(), undo:[],
           kids:{}, parents:{}, folded:new Set(), hidden:new Set(), foldKey:null};
const src = $("#src"), gut = $("#gut"), hlEl = $("#hlIn");   // #hlIn: khối chữ tô màu bên trong <pre id="hl">

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
const PAL = {sec:"#FFFFFF", node:"#E8D48A", link:"#A5ABB6", meta:"#9CDCFE", key:"#9CDCFE", kw:"#C586C0", type:"#4EC9B0",
             val:"#D4D4D4", str:"#CE9178", text:"#D4D4D4"};
const keyColor = () => PAL.key;            // khóa meta: hồng ở mọi nơi

// ---------- hình thức chuẩn của một node (dùng chung cho Graph, Module, xuất SVG) ----------
// Mỗi node luôn có đủ 5 màu; style (html.*) ghi đè, thiếu thì lấy mặc định:
//   fill   html.color         nền
//   border html.border-color  viền
//   text   html.font-color    chữ chính nằm TRÊN nền node (Module); mặc định: trắng trên nền tối, đen trên nền sáng
//   label  html.label-color   nhãn nằm NGOÀI hình, trên nền trang (Graph)
//   sub    html.sub-color     chữ phụ: kiểu node, "+n con"
const _lc = document.createElement("canvas").getContext("2d");
function isLight(c) {                      // màu sáng? (nhận cả tên màu CSS: lightblue, white…)
  _lc.fillStyle = "#000"; _lc.fillStyle = String(c);
  const v = _lc.fillStyle, m = v.match(/^#(..)(..)(..)$/) || v.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/);
  if (!m) return false;
  if (m[4] !== undefined && +m[4] < 0.3) return false;      // gần trong suốt: chữ nằm trên nền trang tối
  const [r, g, b] = (v[0] === "#" ? m.slice(1, 4).map(h => parseInt(h, 16)) : m.slice(1, 4).map(Number));
  return 0.299 * r + 0.587 * g + 0.114 * b > 150;
}
// ---------- - hide: all | graph, module … ----------
// Node / section có hide cho view v thì bị ẩn khỏi v cùng mọi con cháu (node trong section, con part-of / contain).
// @link có hide: ẩn mọi link loại đó. S.showHidden (menu View) tạm hiện lại tất cả.
const hides = (x, v) => !!(x && x.hide && (x.hide.includes("all") || x.hide.includes(v)));
let _hideCache = {g:null, sets:{}};
function hiddenIn(v) {                     // Set id node bị ẩn ở view v
  const g = S.graph;
  if (!g || S.showHidden) return new Set();
  if (_hideCache.g !== g) _hideCache = {g, sets:{}};
  if (_hideCache.sets[v]) return _hideCache.sets[v];
  const kids = {}, add = (p, c) => { if (p && c && p !== c) (kids[p] = kids[p] || []).push(c); };
  for (const n of g.nodes) add(n.parent, n.id);
  for (const l of g.links) {
    if (l.type === "part-of") add(l.target, l.source);
    else if (l.type === "contain") add(l.source, l.target);
  }
  const out = new Set(), st = g.nodes.filter(n => hides(n, v)).map(n => n.id);
  while (st.length) { const id = st.pop(); if (out.has(id)) continue; out.add(id); st.push(...(kids[id] || [])); }
  return (_hideCache.sets[v] = out);
}
const linkHiddenIn = (l, v) => !S.showHidden && (hides(l, v) || hiddenIn(v).has(l.source) || hiddenIn(v).has(l.target));
function nodeLook(n) {
  const s = H(n), sec = n.kind === "section";
  const fill = s.color || (sec ? "#3A3D41" : "#E8D48A");
  return {
    fill,
    border: s["border-color"] || (sec ? "#A5ABB6" : "#C9B66E"),
    text: s["font-color"] || (isLight(fill) ? "#1E1E1E" : "#FFFFFF"),
    label: s["label-color"] || (sec ? PAL.sec : PAL.node),
    sub: s["sub-color"] || PAL.kw,
  };
}
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
const LINK_ORANGE = "#A5ABB6";      // màu mặc định của link: cam (cùng bộ màu với khung văn bản và style hệ thống)

// ---------- tô màu văn bản .kg.md 0.3 (bảng màu plan-v2c) ----------
// vàng: tên node · tím: keyword (@node, @link, link, from, to) · xanh nhạt: attribute key · xanh ngọc: type
// xám: tên link · Str cam nhạt · giá trị khác #D4D4D4 · comment xanh lá nghiêng · dấu - : , xám.
const span = (cls, s, color) => `<span class="${cls}"${color ? ` style="color:${esc(color)}"` : ""}>${esc(s)}</span>`;
const bad = s => `<span style="color:var(--err);text-decoration:underline wavy">${esc(s)}</span>`;
const DTYPES = ["Num", "Str", "Bool", "None", "List", "Dict", "Content"];
function splitComment(line) {             // // là comment khi ở đầu dòng hoặc sau khoảng trắng, ngoài "..." và `...`
  let q = null;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (q) { if (c === q) q = null; }
    else if (c === '"' || c === "`") q = c;
    else if (c === "/" && line[i + 1] === "/" && (i === 0 || /\s/.test(line[i - 1]))) return [line.slice(0, i), line.slice(i)];
  }
  return [line, ""];
}
function hlInline(s) {
  let out = "", last = 0;
  const re = /(`[^`]*`)|(\*\*[^*]+\*\*)|((?:^|(?<=\s))@[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)?)/g;
  for (const m of s.matchAll(re)) {
    out += esc(s.slice(last, m.index));
    out += span(m[1] ? "t-code" : m[2] ? "t-bold" : "t-ref", m[0]);
    last = m.index + m[0].length;
  }
  return out + esc(s.slice(last));
}
const hlText = s => `<span class="t-text">${hlInline(s)}</span>`;
// giá trị: mode "ref" (tên node), "link" (tên link), "type" (tên kiểu), "str" (chuỗi), "" (chung)
function hlVal(v, mode) {
  let out = "";
  const tok = /("[^"]*"?)|(`[^`]*`?)|(\[[\s\S]*)|([(),\]])|([A-Za-z_][\w-]*\s*=(?!=))|(-?\d+(?:\.\d+)?(?![\w-]))|([^\s(),"`=\[\]]+(?:\s+[^\s(),"`=\[\]]+)*)|(\s+)|(.)/g;
  for (const m of v.matchAll(tok)) {
    const t = m[0];
    if (m[1]) out += span("t-str", t);
    else if (m[2]) out += span("t-code", t);
    else if (m[3]) out += span("t-text", t);
    else if (m[4]) out += span("t-val", t);
    else if (m[5]) { const k = t.replace(/\s*=$/, ""); out += span("t-key", k) + esc(t.slice(k.length)); }
    else if (m[6]) out += span("t-val", t);
    else if (m[7]) {
      if (mode === "ref") out += span("t-id", t);
      else if (mode === "link") out += span("t-link", t);
      else if (mode === "type" || DTYPES.includes(t)) out += span("t-type", t);
      else if (/^(true|false|none)$/.test(t)) out += span("t-val", t);
      else out += span("t-str", t);
    } else out += esc(t);
  }
  return out;
}
function depth(v) {                       // số ngoặc ( [ còn mở
  let d = 0, q = null;
  for (const c of v) {
    if (q) { if (c === q) q = null; }
    else if (c === '"' || c === "`") q = c;
    else if (c === "[" || c === "(") d++;
    else if (c === "]" || c === ")") d--;
  }
  return d;
}
function highlight(text) {
  const L = text.split("\n"), out = [];
  let fm = L[0] && L[0].trim() === "---" ? 1 : 0, fence = false, block = null, phase = "body", open = 0;
  L.forEach((raw, i) => {
    if (open > 0) {                                   // giá trị [ … ] / ( … ) nhiều dòng
      open += depth(raw);
      out.push(span("t-text", raw)); return;
    }
    if (fm) {
      if (raw.trim() === "---") { if (i > 0) fm = 0; out.push(span("t-punct", raw)); return; }
      const [code, com] = splitComment(raw), tail = com ? span("t-com", com) : "";
      let m;
      if ((m = code.match(/^(\s*-\s+)([^:]+?)(?:(:)(.*))?$/))) {   // - king/schema.node: Concept, Group
        const sel = /\.node\s*$/.test(m[2]) ? "type" : /\.link\s*$/.test(m[2]) ? "link" : "str";
        out.push(span("t-punct", m[1]) + span("t-val", m[2]) + (m[3] ? span("t-punct", ":") + hlVal(m[4], sel) : "") + tail); return;
      }
      if ((m = code.match(/^(\s*)([A-Za-z][\w-]*)(\s*:)(.*)$/))) {
        out.push(esc(m[1]) + span("t-key", m[2]) + span("t-punct", m[3]) + hlVal(m[4], m[2] === "import" ? "ref" : "") + tail); return;
      }
      out.push(esc(code) + tail); return;
    }
    if (/^\s*(```|~~~)/.test(raw)) { fence = !fence; phase = "body"; out.push(span("t-fence", raw)); return; }
    if (fence) { out.push(span("t-code", raw)); return; }
    const [code, com] = splitComment(raw), tail = com ? span("t-com", com) : "";
    let m;
    if ((m = code.match(/^(#{1,6}\s+)(.*?)(\s+@[a-z0-9][a-z0-9-]*)?(\s*)$/))) {
      block = "section"; phase = "attrs";
      out.push(span("t-head", m[1] + m[2]) + (m[3] ? span("t-id", m[3]) : "") + esc(m[4]) + tail); return;
    }
    if ((m = code.match(/^(@(?:node|link))(\s+)(\S+)(.*)$/))) {
      block = m[1].slice(1); phase = "attrs";
      const nm = m[3], cls = block === "link" ? "t-link" : /^[A-Z]/.test(nm) ? "t-type" : "t-id";
      out.push(span("t-kw", m[1]) + esc(m[2]) + span(cls, nm) + (m[4].trim() ? bad(m[4]) : esc(m[4])) + tail); return;
    }
    if (/^@[a-z0-9][a-z0-9-]*\s*:/.test(code)) { out.push(bad(code) + tail); return; }   // cú pháp v0.2
    if (phase === "attrs" && block) {
      if (!raw.trim()) { phase = "body"; out.push(""); return; }
      if (!code.trim()) { out.push(tail); return; }
      if (raw.startsWith("- ")) {
        let v = null;
        if (block === "link" && (m = code.match(/^(-\s+)(from)(\s+)(.+?)(\s+)(to)(\s+)(.+)$/))) {
          out.push(span("t-punct", m[1]) + span("t-kw", m[2]) + esc(m[3]) + hlVal(m[4], "ref") + esc(m[5]) +
            span("t-kw", m[6]) + esc(m[7]) + hlVal(m[8], "ref") + tail); return;
        }
        if ((m = code.match(/^(-\s+)(link)(\s+)(\S+?)(\s*:)(.*)$/))) {
          v = m[6];
          out.push(span("t-punct", m[1]) + span("t-kw", m[2]) + esc(m[3]) + span("t-link", m[4]) + span("t-punct", m[5]) + hlVal(v, "ref") + tail);
        } else if ((m = code.match(/^(-\s+)([A-Za-z_][\w-]*)(\s*:)(.*)$/))) {
          const k = m[2], mode = k === "type" ? "type" : k === "inverse" ? "link" : k === "label" ? "str" : "";
          v = m[4];
          out.push(span("t-punct", m[1]) + span("t-key", k) + span("t-punct", m[3]) +
            (k === "label" && !/^\s*"/.test(v) ? span("t-str", v) : hlVal(v, mode)) + tail);
        } else if (block !== "section") { out.push(bad(code) + tail); return; }
        if (v !== null) { open = Math.max(0, depth(v)); return; }
      }
      phase = "body";
    }
    out.push(hlText(code) + tail);
  });
  return out.join("\n") + "\n ";
}
let hlPending = false;
function paint() {
  if (hlPending) return; hlPending = true;
  requestAnimationFrame(() => {
    hlPending = false;
    const html = highlight(S.text);
    // khi ngắt dòng: khối tô màu rộng đúng bằng vùng chữ của textarea (trừ thanh cuộn) để ngắt dòng giống hệt
    hlEl.style.width = S.wrap ? src.clientWidth + "px" : "";
    const pre = hlEl.parentElement;                  // không cho chữ tô màu lộ ra dưới thanh cuộn của textarea
    pre.style.right = (src.offsetWidth - src.clientWidth) + "px"; pre.style.bottom = (src.offsetHeight - src.clientHeight) + "px";
    if (S.wrap) {        // mỗi dòng một khối để đo chiều cao sau khi ngắt, rồi kéo lề số dòng cho khớp
      hlEl.innerHTML = html.replace(/\n $/, "").split("\n").map(l => `<div class="ln">${l || " "}</div>`).join("");
      gut.innerHTML = gutterHTML([...hlEl.children].map(d => d.offsetHeight));
    } else hlEl.innerHTML = html;
    syncScroll();
    if (S.wrap) requestAnimationFrame(() => {        // thanh cuộn dọc vừa hiện / ẩn → bề rộng ngắt dòng đổi: vẽ lại
      if (hlEl.style.width !== src.clientWidth + "px") paint();
    });
  });
}
function syncScroll() {     // dịch khối tô màu thay vì cuộn: không bị giới hạn cuộn khác textarea nên chữ luôn trùng con trỏ
  hlEl.style.transform = `translate(${-src.scrollLeft}px, ${-src.scrollTop}px)`; gut.scrollTop = src.scrollTop;
}

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
  const st = src.scrollTop, sl = src.scrollLeft, a = src.selectionStart, b = src.selectionEnd;
  src.value = t; src.setSelectionRange(Math.min(a, t.length), Math.min(b, t.length));   // giữ chỗ con trỏ (không nhảy về cuối)
  src.scrollTop = st; src.scrollLeft = sl;
  if (t !== S.text) S.dirty = true;
  S.text = t; updateGutter();
}
function jumpTo(line, focus) {   // focus=true: chuyển con trỏ vào khung văn bản; bấm trên đồ thị thì không (để Ctrl+C/V/ dùng cho node)
  const L = S.text.split("\n"); let off = 0;
  for (let i = 0; i < line - 1 && i < L.length; i++) off += L[i].length + 1;
  if (focus) src.focus({preventScroll:true});
  src.setSelectionRange(off, off + (L[line - 1] || "").length);
  const row = S.wrap && hlEl.children[line - 1];
  src.scrollTop = Math.max(0, row ? row.getBoundingClientRect().top - hlEl.getBoundingClientRect().top - 60 : (line - 4) * 20); syncScroll();
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
  if (mod && !e.altKey && (k === "s" || e.code === "KeyS")) { e.preventDefault(); e.stopPropagation(); saveNow(); return; }
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
async function save(force) {
  if (ST || !S.name || (!S.dirty && !force)) return;
  const text = S.text;
  try {
    const r = await api("/api/save", {name:S.name, text});
    S.mtime = r.mtime;
    if (S.text === text) S.dirty = false;            // gõ thêm trong lúc đang lưu: vẫn còn là "chưa lưu"
    $("#fname").classList.toggle("dirty", S.dirty);
    status("Đã lưu " + S.name);
  }
  catch (e) { status("Lưu lỗi: " + e.message, "err"); }
}
async function saveNow() {                           // Ctrl+S: lưu ngay, không chờ hẹn giờ tự lưu
  if (ST) { status("Trang tĩnh (chỉ xem): không lưu được. Mở bằng king serve để sửa."); return; }
  if (!S.name) { status("Chưa mở file."); return; }
  clearTimeout(tmr);
  await save(true); await reparse();
}
async function undo() {
  if (!S.undo.length) return status("Không còn gì để hoàn tác.");
  setText(S.undo.pop(), true); S.dirty = true; await reparse(); await save(); status("Đã hoàn tác.");
}
// KING 0.3: Inspector và các thao tác sửa trên view tạm khóa (dev/plan-working/README.md mục 2).
// Mọi chỉnh sửa đi qua khung văn bản; op() không gửi gì.
const FROZEN = true;
async function op(name, args, before) {
  if (ST || !S.name) return;
  if (FROZEN) { status("KING 0.3: sửa trên view / Inspector đang tạm khóa — hãy sửa trong khung văn bản.", "warn"); return; }
  try {
    const r = await api("/api/op", {name:S.name, text:S.text, op:name, args});
    if (before) before(r);
    if (r.text !== S.text) setText(r.text);
    await reparse(); await save();
    if (r.msg) status(r.msg);
    return r;
  } catch (e) { status(e.message, "err"); alert(e.message); }
}
