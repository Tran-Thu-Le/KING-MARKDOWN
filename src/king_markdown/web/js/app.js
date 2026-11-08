// app.js - menu File / View / Format, 3 view (Graph, Tree, Book), đồng bộ với file trên đĩa, khởi động

// ---------- menu kiểu VS Code ----------
function closeMenus() { $$(".menu.open").forEach(m => m.classList.remove("open")); }
$$(".menu").forEach(m => {
  m.querySelector(".mbtn").onclick = e => {
    e.stopPropagation();
    const was = m.classList.contains("open"); closeMenus(); if (!was) m.classList.add("open");
  };
  m.onmouseenter = () => { if ($(".menu.open") && !m.classList.contains("open")) { closeMenus(); m.classList.add("open"); } };
  m.querySelector(".drop").onclick = e => {
    e.stopPropagation();
    if (e.target.closest(".item")) closeMenus();         // mục bấm một lần thì đóng; ô nhập trong Format thì giữ
  };
});
document.addEventListener("click", closeMenus);
document.addEventListener("keydown", e => { if (e.key === "Escape") closeMenus(); });

// ---------- 3 view ----------
const VIEWS = {graph:"Graph", tree:"Tree", book:"Book", module:"Module"};
function renderViews() {
  if (S.view === "tree") renderTree();
  else if (S.view === "book") renderBook();
  else if (S.view === "module") renderModule();
}
function setView(v) {
  if (!VIEWS[v]) v = "graph";
  S.view = v;
  $$(".view").forEach(el => el.classList.toggle("on", el.id === v + "View"));
  $$("[data-view]").forEach(el => el.classList.toggle("on", el.dataset.view === v));
  $("#sbView").textContent = "View: " + VIEWS[v];
  try { localStorage.setItem("kgview", v); } catch (e) {}
  if (!ST && S.name) history.replaceState(null, "", "?file=" + encodeURIComponent(S.name) + (v !== "graph" ? "&view=" + v : ""));
  if (v === "graph") { net.redraw(); if (!S.graphShown && S.graph) net.fit(); S.graphShown = true; }
  renderViews();
  if (S.selected) markSelected(S.selected, true);
}
$$("[data-view]").forEach(el => el.addEventListener("click", () => setView(el.dataset.view)));
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && ["1", "2", "3", "4"].includes(e.key)) { e.preventDefault(); setView(["graph", "tree", "book", "module"][+e.key - 1]); }
});

// ---------- báo server trang còn mở; đóng trang thì server tự dừng ----------
const CLIENT = Math.random().toString(36).slice(2) + Date.now().toString(36);
function beat(path, keepalive) {
  return fetch(path, {method:"POST", keepalive, headers:{"Content-Type":"application/json"},
                      body:JSON.stringify({id:CLIENT})}).catch(() => {});
}
if (!ST) {
  beat("/api/ping"); setInterval(() => beat("/api/ping"), 10000);
  addEventListener("pagehide", () => {
    if (S.dirty && S.name)      // còn sửa chưa lưu: gửi lưu trước khi đóng
      fetch("/api/save", {method:"POST", keepalive:true, headers:{"Content-Type":"application/json"},
                          body:JSON.stringify({name:S.name, text:S.text})}).catch(() => {});
    beat("/api/bye", true);
  });
  addEventListener("pageshow", e => { if (e.persisted) beat("/api/ping"); });
}

// ---------- đồng bộ với file trên đĩa ----------
setInterval(async () => {
  if (ST || !S.name || document.hidden) return;
  try {
    const m = await api("/api/mtime?name=" + encodeURIComponent(S.name));
    if (m.mtime > S.mtime + 1e-6) {
      if (!S.dirty || confirm(S.name + " vừa được sửa ở nơi khác. Tải lại (bỏ thay đổi ở đây)?")) {
        const f = await api("/api/file?name=" + encodeURIComponent(S.name));
        S.mtime = f.mtime; setText(f.text); S.dirty = false; await reparse(); status("Đã tải lại " + S.name);
      } else S.mtime = m.mtime;
    }
    if (m.side !== S.side) { S.side = m.side; await reparse(); }
  } catch (e) {}
}, 2000);

// ---------- khởi động ----------
// bấm lại "Thu gọn" thì về chế độ Chọn (bản tĩnh không có nút Chọn)
$$("[data-mode]").forEach(b => b.onclick = () => setMode(b.dataset.mode === "fold" && S.mode === "fold" ? "select" : b.dataset.mode));
$("#bSvg").onclick = () => { closeMenus(); if (S.view !== "graph") setView("graph"); exportSVG(); };
$("#bSave").onclick = save; $("#bUndo").onclick = undo;
$("#bFoldAll").onclick = () => foldAll(true); $("#bUnfoldAll").onclick = () => foldAll(false);
$("#showTree").onchange = () => { if (S.graph) { edgesDS.clear(); edgesDS.add(visEdges()); } if (S.mode === "link") net.addEdgeMode(); };
$("#showDefs").onchange = e => { S.showDefs = e.target.checked; if (S.graph) render(S.graph); };
// ẩn / hiện nhãn node, section, link (Format › Nhãn); nhớ trong trình duyệt
try { S.hideLab = JSON.parse(localStorage.getItem("kglabels") || "{}"); } catch (e) { S.hideLab = {}; }
function applyLabels() {
  $$("[data-lab]").forEach(c => { c.checked = !S.hideLab[c.dataset.lab]; });
  try { localStorage.setItem("kglabels", JSON.stringify(S.hideLab)); } catch (e) {}
  if (S.graph) render(S.graph);
}
$$("[data-lab]").forEach(c => c.onchange = () => { S.hideLab[c.dataset.lab] = !c.checked; applyLabels(); });
$("#bLabAll").onclick = () => {
  const hideAll = !["node", "section", "link"].every(k => S.hideLab[k]);
  S.hideLab = {node:hideAll, section:hideAll, link:hideAll}; applyLabels();
};
$$("[data-lab]").forEach(c => { c.checked = !S.hideLab[c.dataset.lab]; });
$("#bFit").onclick = () => net.fit({animation:{duration:300}});

// ---------- thanh kéo co dãn + bật/tắt panel (nhớ trong trình duyệt) ----------
const LAYOUT_KEY = "kglayout";
function loadLayout() { try { return JSON.parse(localStorage.getItem(LAYOUT_KEY) || "{}"); } catch (e) { return {}; } }
function saveLayout(patch) { try { localStorage.setItem(LAYOUT_KEY, JSON.stringify({...loadLayout(), ...patch})); } catch (e) {} }
const PANEL_SPLIT = {explorer:"#splitE", inspector:"#splitI", left:"#split"};
function setPanel(name, show) {
  const el = $("#" + name), sp = $(PANEL_SPLIT[name]);
  if (show === undefined) show = el.classList.contains("hidden-panel");
  el.classList.toggle("hidden-panel", !show); sp.classList.toggle("hidden-panel", !show);
  $$(`[data-panel="${name}"]`).forEach(b => b.classList.toggle("on", show));
  saveLayout({["show_" + name]: show});
  requestAnimationFrame(() => net.redraw());
}
$$(".split").forEach(sp => sp.onmousedown = e => {
  e.preventDefault();
  const el = $("#" + sp.dataset.target), left = sp.dataset.side === "left";
  const x0 = e.clientX, w0 = el.getBoundingClientRect().width;
  const mv = ev => {
    const w = Math.max(160, Math.min(w0 + (left ? 1 : -1) * (ev.clientX - x0), innerWidth - 420));
    el.style.width = w + "px";
  };
  const up = () => {
    removeEventListener("mousemove", mv); removeEventListener("mouseup", up); sp.classList.remove("drag");
    saveLayout({["w_" + sp.dataset.target]: el.style.width}); net.redraw();
  };
  sp.classList.add("drag"); addEventListener("mousemove", mv); addEventListener("mouseup", up);
});
$$("[data-panel]").forEach(b => b.addEventListener("click", () => setPanel(b.dataset.panel)));
$$("#bWrap, #bWrap2").forEach(b => b.addEventListener("click", () => setWrap(!S.wrap)));
// Alt+Z: ngắt dòng (macOS: Option+Z cho ký tự "Ω"). Mở trang trong VS Code thì VS Code giữ Alt+Z: dùng nút ↵ Wrap.
document.addEventListener("keydown", e => {
  if (e.altKey && !e.ctrlKey && !e.metaKey && (e.code === "KeyZ" || /^[zΩ]$/i.test(e.key))) {
    e.preventDefault(); setWrap(!S.wrap); status(S.wrap ? "Ngắt dòng: bật (Alt+Z để tắt)" : "Ngắt dòng: tắt");
  }
}, true);
{ let w = ""; try { w = localStorage.getItem("kgwrap"); } catch (e) {} if (w) setWrap(true); }
document.addEventListener("keydown", e => {
  if (!(e.ctrlKey || e.metaKey)) return;
  const k = e.key.toLowerCase();
  if (k === "b" && e.altKey) { e.preventDefault(); setPanel("inspector"); }
  else if (k === "b") { e.preventDefault(); setPanel("explorer"); }
  else if (k === "e") { e.preventDefault(); setPanel("left"); }
});
{
  const L = loadLayout();
  for (const name of ["explorer", "inspector", "left"]) {
    if (L["w_" + name]) $("#" + name).style.width = L["w_" + name];
    setPanel(name, L["show_" + name] !== false);
  }
}
const BOOT_URL = new URLSearchParams(location.search);   // đọc trước khi openFile() viết lại URL
function pickFromUrl() {           // ?node=id mở sẵn node đó (link chia sẻ tới một node)
  const id = BOOT_URL.get("node");
  if (id && S.byId[id]) { focusNode(id, true); if (S.byId[id].line) jumpTo(S.byId[id].line); }
}
(async () => {
  setMode("select");
  let v = new URLSearchParams(location.search).get("view");
  if (!v) { try { v = localStorage.getItem("kgview"); } catch (e) {} }
  setView(v || "graph");
  if (ST) {
    document.body.classList.add("static"); src.readOnly = true;
    S.name = ST.name; src.value = S.text = ST.text; $("#fname").textContent = ST.name;
    $("#title").textContent = ST.name + " — bản tĩnh, chỉ xem"; $("#sbRoot").textContent = "Bản tĩnh";
    $("#editLink").href = "http://127.0.0.1:8765/?file=" + encodeURIComponent(ST.name);
    document.title = ST.name; render(ST.graph); renderExplorer(); pickFromUrl(); return;
  }
  try {
    const s = await refreshState(), want = new URLSearchParams(location.search).get("file");
    await openFile(s.files.includes(want) ? want : (s.files.find(f => !/^(schema|style)\./.test(f)) || s.files[0] || ""));
    pickFromUrl();
  } catch (e) { status("Không kết nối được server (king serve): " + e.message, "err"); }
})();
