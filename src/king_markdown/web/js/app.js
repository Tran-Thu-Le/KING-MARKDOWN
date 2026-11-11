// app.js - menu File / View / Format, hai khung nhiều tab (Văn bản, Graph, Tree, Book, Module), đồng bộ với file trên đĩa, khởi động

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

// ---------- hai khung, mỗi khung nhiều tab ----------
// Panel: text (khung văn bản) và 4 view. Mỗi panel chỉ có một bản, nằm ở một khung (left / right) hoặc đang đóng.
// Mỗi khung có một tab đang mở; hai khung có thể mở hai view khác nhau cùng lúc (vd. Tree bên trái, Graph bên phải).
const VIEWS = {graph:"Graph", tree:"Tree", book:"Book", module:"Module"};
const PANELS = {text:"Văn bản (.kg.md)", ...VIEWS};
const PANES = ["left", "right"];
const PANE_KEY = "kgpanes";
const tabOf = p => $(`.tab[data-panel="${p}"]`), bodyOf = p => $("#" + p + "View");
const closedBox = document.createElement("div");                   // panel đang đóng: vẫn ở trong trang (code khác còn tìm #log, #fname…) nhưng ẩn
closedBox.hidden = true; closedBox.id = "closedPanels"; document.body.appendChild(closedBox);
const paneOf = p => { const t = tabOf(p).closest(".pane"); return t ? t.id : null; };
const paneTabs = id => [...$("#" + id).querySelectorAll(".tab-list .tab")].map(t => t.dataset.panel);
const activeOf = id => { const t = $("#" + id).querySelector(".tab-list .tab.on"); return t ? t.dataset.panel : null; };
const shown = p => PANES.some(id => activeOf(id) === p);          // panel đang hiện ở một khung nào đó
function savePanes() {
  const L = {}; for (const id of PANES) L[id] = {tabs: paneTabs(id), on: activeOf(id)};
  try { localStorage.setItem(PANE_KEY, JSON.stringify(L)); } catch (e) {}
}
function refreshPane(id) {
  const pane = $("#" + id), on = activeOf(id);
  pane.classList.toggle("empty", !on);
  pane.classList.toggle("text-on", on === "text");
  for (const t of pane.querySelectorAll(".tab-list .tab")) bodyOf(t.dataset.panel).classList.toggle("on", t.dataset.panel === on);
}
function renderViews() {
  if (shown("tree")) renderTree();
  if (shown("book")) renderBook();
  if (shown("module")) renderModule();
}
function afterShow(p) {
  if (p === "graph") requestAnimationFrame(() => { net.redraw(); if (!S.graphShown && S.graph) net.fit(); S.graphShown = true; });
  if (p === "text") updateGutter();
  if (VIEWS[p]) {
    S.view = p; $("#sbView").textContent = "View: " + VIEWS[p];
    $$(".item[data-view]").forEach(el => el.classList.toggle("on", shown(el.dataset.view)));
    try { localStorage.setItem("kgview", p); } catch (e) {}
    if (!ST && S.name) history.replaceState(null, "", "?file=" + encodeURIComponent(S.name) + (p !== "graph" ? "&view=" + p : ""));
  }
}
function showTab(id, p) {
  $("#" + id).querySelectorAll(".tab-list .tab").forEach(t => t.classList.toggle("on", t.dataset.panel === p));
  refreshPane(id);
}
function activate(p) {                    // mở tab p trong khung đang chứa nó
  const id = paneOf(p); if (!id) return;
  showTab(id, p); savePanes();
  afterShow(p); renderViews();
  if (S.selected) markSelected(S.selected, true);
}
function detach(p) {                      // gỡ panel p khỏi khung đang chứa; khung đó mở tab bên cạnh
  const id = paneOf(p); if (!id) return;
  const wasOn = activeOf(id) === p, rest = paneTabs(id).filter(x => x !== p);
  const t = tabOf(p), b = bodyOf(p);
  t.classList.remove("on"); b.classList.remove("on");
  closedBox.append(t, b);
  if (wasOn && rest.length) showTab(id, rest[rest.length - 1]); else refreshPane(id);
  const o = activeOf(id); if (o && wasOn) afterShow(o);
}
function placePanel(p, id, quiet) {            // đưa panel p vào khung id (chuyển từ khung kia nếu đang ở đó) và mở nó
  if (paneOf(p) !== id) {
    detach(p);
    $("#" + id + " .tab-list").appendChild(tabOf(p));
    $("#" + id + " .views").insertBefore(bodyOf(p), $("#" + id + " .pane-empty"));
  }
  if (quiet) refreshPane(id); else activate(p);
}
function closePanel(p) {
  const id = paneOf(p); if (!id) return;
  detach(p); savePanes(); renderViews();
}
$$(".item[data-view]").forEach(el => el.addEventListener("click", () => setView(el.dataset.view)));   // menu View
function setView(v) {                     // Ctrl+1..4, ?view=…: mở view v; nếu đang đóng thì đặt vào khung phải
  if (!VIEWS[v]) v = "graph";
  if (paneOf(v)) activate(v); else placePanel(v, "right");
}
// menu ＋ của mỗi khung
const addMenu = $("#addMenu");
function openAddMenu(btn) {
  const id = btn.closest(".pane").id;
  addMenu.innerHTML = Object.entries(PANELS).map(([p, name]) => {
    const where = paneOf(p);
    const note = where === id ? "đang ở đây" : where ? "chuyển từ khung " + (where === "left" ? "trái" : "phải") : "";
    return `<button data-add="${p}" ${where === id ? "disabled" : ""}>${name}<small>${note}</small></button>`;
  }).join("");
  const r = btn.getBoundingClientRect();
  addMenu.hidden = false; addMenu.dataset.pane = id;
  addMenu.style.top = r.bottom + 2 + "px";
  addMenu.style.left = Math.max(4, Math.min(r.left, innerWidth - addMenu.offsetWidth - 4)) + "px";
}
$$(".tab-add").forEach(b => b.addEventListener("click", e => {
  e.stopPropagation();
  if (!addMenu.hidden && addMenu.dataset.pane === b.closest(".pane").id) addMenu.hidden = true; else openAddMenu(b);
}));
addMenu.addEventListener("click", e => {
  e.stopPropagation();
  const b = e.target.closest("[data-add]"); if (!b || b.disabled) return;
  addMenu.hidden = true; placePanel(b.dataset.add, addMenu.dataset.pane);
});
document.addEventListener("click", () => { addMenu.hidden = true; });
document.addEventListener("keydown", e => { if (e.key === "Escape") addMenu.hidden = true; });
// bấm tab: mở; bấm ×: đóng; kéo tab thả lên thanh tab của khung kia: chuyển
for (const p of Object.keys(PANELS)) {
  const t = tabOf(p);
  t.draggable = true;
  t.addEventListener("click", e => { if (e.target.closest(".tab-x")) { e.stopPropagation(); closePanel(p); } else activate(p); });
  t.addEventListener("dragstart", e => { e.dataTransfer.setData("text/kg-panel", p); e.dataTransfer.effectAllowed = "move"; });
}
for (const id of PANES) {
  const bar = $("#" + id + " .tabs");
  bar.addEventListener("dragover", e => { if (e.dataTransfer.types.includes("text/kg-panel")) { e.preventDefault(); bar.classList.add("drop-on"); } });
  bar.addEventListener("dragleave", () => bar.classList.remove("drop-on"));
  bar.addEventListener("drop", e => {
    bar.classList.remove("drop-on");
    const p = e.dataTransfer.getData("text/kg-panel"); if (!PANELS[p]) return;
    e.preventDefault(); placePanel(p, id);
  });
}
function restorePanes(view) {             // bố cục đã lưu; mặc định: Văn bản bên trái, 4 view bên phải
  let L = null; try { L = JSON.parse(localStorage.getItem(PANE_KEY) || "null"); } catch (e) {}
  if (!(L && PANES.every(id => L[id] && Array.isArray(L[id].tabs)))) {
    let v = null; try { v = localStorage.getItem("kgview"); } catch (e) {}
    L = {left: {tabs: ["text"], on: "text"}, right: {tabs: Object.keys(VIEWS), on: VIEWS[v] ? v : "graph"}};
  }
  const want = new Set(PANES.flatMap(id => L[id].tabs));
  for (const p of Object.keys(PANELS)) if (!want.has(p)) detach(p);
  for (const id of PANES) for (const p of L[id].tabs) if (PANELS[p]) placePanel(p, id, true);
  for (const id of PANES) {
    const tabs = paneTabs(id), on = tabs.includes(L[id].on) ? L[id].on : tabs[0];
    showTab(id, on); if (on) afterShow(on);
  }
  if (view && VIEWS[view]) setView(view);   // ?view=… trong URL
  renderViews();
}
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
$("#bSvg").onclick = () => { closeMenus(); if (!shown("graph")) setView("graph"); exportSVG(); };
$("#bSave").onclick = saveNow; $("#bUndo").onclick = undo;
$("#bFoldAll").onclick = () => foldAll(true); $("#bUnfoldAll").onclick = () => foldAll(false);
$("#showTree").onchange = () => { if (S.graph) { edgesDS.clear(); edgesDS.add(visEdges()); } if (S.mode === "link") net.addEdgeMode(); };
$("#showDefs").onchange = e => { S.showDefs = e.target.checked; if (S.graph) render(S.graph); };
function toggleShowHidden() {            // tạm hiện lại node / link có - hide: …
  S.showHidden = !S.showHidden; $("#bShowHidden").classList.toggle("on", S.showHidden);
  status(S.showHidden ? "Đang hiện cả node đã ẩn (hide). Ctrl+H để ẩn lại." : "Đã ẩn lại các node có hide.");
  if (S.graph) render(S.graph);
}
$("#bShowHidden").onclick = toggleShowHidden;
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && e.key.toLowerCase() === "h") { e.preventDefault(); toggleShowHidden(); }
});
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
    setPanel(name, name === "inspector" ? false : L["show_" + name] !== false);   // 0.3: Inspector ẩn mặc định
  }
  if (FROZEN) document.body.classList.add("frozen");
}
const BOOT_URL = new URLSearchParams(location.search);   // đọc trước khi openFile() viết lại URL
function pickFromUrl() {           // ?node=id mở sẵn node đó (link chia sẻ tới một node)
  const id = BOOT_URL.get("node");
  if (id && S.byId[id]) { focusNode(id, true); if (S.byId[id].line) jumpTo(S.byId[id].line); }
}
(async () => {
  setMode("select");
  restorePanes(new URLSearchParams(location.search).get("view"));
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
