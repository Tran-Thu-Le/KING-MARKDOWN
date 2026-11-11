// explorer.js - chọn thư mục, tạo file; View Tree (cây section → node, node con part-of / contain dưới node cha)
// ---------- thư mục ----------
async function listDirs(p) {
  try {
    const r = await api("/api/dirs?path=" + encodeURIComponent(p || ""));
    $("#dpath").value = r.path;
    $("#dlist").innerHTML = (r.parent ? `<div data-p="${esc(r.parent)}">⬆ ..</div>` : "") +
      r.dirs.map(d => `<div data-p="${esc(d.path)}">📁 ${esc(d.name)}${d.kg ? ` <small>${d.kg} file .kg.md</small>` : ""}</div>`).join("") +
      (r.files.length ? `<div style="cursor:default;color:var(--mute)">Trong thư mục: ${r.files.map(esc).join(", ")}</div>` : "");
    $$("#dlist [data-p]").forEach(d => d.onclick = () => listDirs(d.dataset.p));
  } catch (e) { alert(e.message); }
}
function openFolderDialog() { closeMenus(); listDirs(S.root); $("#dlg").showModal(); }
$("#bFolder").onclick = openFolderDialog; $("#exFolder").onclick = openFolderDialog;
$("#dpath").onkeydown = e => { if (e.key === "Enter") { e.preventDefault(); listDirs(e.target.value); } };
$("#dcancel").onclick = () => $("#dlg").close();
$("#dok").onclick = async () => {
  try {
    if (S.dirty) await save();
    await api("/api/open-folder", {path:$("#dpath").value}); $("#dlg").close();
    const s = await refreshState(); await openFile(s.files[0] || "");
    if (!s.files.length) status("Thư mục chưa có file .kg.md: File → File mới…");
  } catch (e) { alert(e.message); }
};
$("#bNew").onclick = $("#exNew").onclick = async () => {
  closeMenus();
  const n = (prompt("Tên file mới (không cần đuôi .kg.md):") || "").trim(); if (!n) return;
  try { const r = await api("/api/new", {name:n}); await refreshState(); await openFile(r.name); } catch (e) { alert(e.message); }
};
$("#exRefresh").onclick = async () => { try { await refreshState(); status("Đã tải lại danh sách file."); } catch (e) { status(e.message, "err"); } };

// ---------- Explorer: file trong thư mục (schema / style mở và sửa trực tiếp) + outline ----------
function fileRole(f) {
  const used = (S.graph && S.graph.graph.use) || [];
  if (/^schema\b/.test(f) || (used.includes(f) && /schema/.test(f))) return "schema";
  if (/^style\b/.test(f) || (used.includes(f) && /style/.test(f))) return "style";
  return "";
}
function renderExplorer() {
  const files = ST ? [ST.name] : (S.files || []);
  $("#exRoot").textContent = ST ? "BẢN TĨNH" : (S.root.split(/[\\/]/).pop() || S.root);
  $("#exRoot").title = S.root;
  const role = f => { const r = fileRole(f); return r ? `<span class="role ${r}">${r}</span>` : ""; };
  $("#exFiles").innerHTML = files.length
    ? files.map(f => `<div class="fi${f === S.name ? " on" : ""}" data-f="${esc(f)}" title="${esc(f)}"><span class="ic">K</span><span class="nm">${esc(f)}</span>${role(f)}</div>`).join("")
    : '<div class="fi" style="cursor:default;color:var(--mute)">(chưa có file .kg.md)</div>';
  $$("#exFiles [data-f]").forEach(el => el.onclick = () => { if (!ST && el.dataset.f !== S.name) openFile(el.dataset.f); });
  renderTree($("#exOutline"));
}

// ---------- View Tree ----------
const treeClosed = new Set();
function treeChildren() {
  // cha trong cây: node part-of / được contain → node cha đó; còn lại → section chứa nó
  const kids = {}, roots = [], byLine = (a, b) => (a.line || 1e9) - (b.line || 1e9);
  const nodes = S.graph.nodes.slice().sort(byLine);
  for (const n of nodes) {
    const ps = [...(S.parents[n.id] || [])].filter(p => S.byId[p]);
    const via = ps.length ? (S.graph.links.some(l => l.type === "part-of" && l.source === n.id && l.target === ps[0]) ? "part-of" : "contain") : null;
    const p = ps[0] || n.parent;
    if (p && S.byId[p]) (kids[p] = kids[p] || []).push({n, via}); else roots.push({n, via:null});
  }
  return {kids, roots};
}
const isOutput = r => /^(output|xuất|xuat)$/i.test(String(r || "").trim());   // role: output (hoặc Xuất của v0.2)
function treeRow(n, depth, has, via, dim) {
  const ic = n.kind === "section" ? ["sec", "#"] : n.kind === "external" ? ["ext", "↗"] : ["nod", "@"];
  // chỉ hiện label + kiểu node + role khi là output; các attribute khác (và role input / scaffold…) ẩn,
  // xem khi rê chuột, ở Book hoặc khung văn bản
  const meta = Object.entries(n.meta || {}).filter(([k]) => !["contain", "type", "ask", "show", "label"].includes(k))
    .map(([k, v]) => `${k}: ${v}`).join("\n");
  const role = n.meta && n.meta.role, out = isOutput(role);
  return `<div class="tr${n.show === "none" || n.def || dim ? " hide" : ""}" data-id="${esc(n.id)}" style="padding-left:${8 + depth * 14}px" title="${esc(n.id)}${n.def ? " (" + n.def + ")" : ""}${via ? " · " + via : ""}${meta ? "\n" + esc(meta) : ""}">` +
    `<span class="tw">${has ? (treeClosed.has(n.id) ? "▸" : "▾") : ""}</span>` +
    `<span class="ic ${ic[0]}">${ic[1]}</span><span class="nm ${ic[0]}">${esc(n.title || n.id)}</span>` +
    (n.type ? `<span class="ty">${esc(n.type)}</span>` : "") +
    (out ? `<span class="ro">${esc(role)}</span>` : "") +
    (n.ask ? '<span class="ask">✎</span>' : "") + "</div>";
}
function renderTree(el) {           // vẽ vào View Tree, hoặc vào Outline của Explorer
  el = el || $("#treeView");
  if (!S.graph) { el.innerHTML = '<div class="tr"><span class="nm" style="color:var(--mute)">(chưa có dữ liệu)</span></div>'; return; }
  const {kids, roots} = treeChildren(), out = [];
  // - hide: tree / all: View Tree bỏ hẳn; Outline vẫn hiện (mờ) để còn tìm và sửa
  const hid = hiddenIn("tree"), isView = el.id === "treeView";
  const walk = (items, depth, path) => {
    for (const {n, via} of items) {
      if (path.has(n.id)) continue;                      // phòng vòng lặp
      if (isView && hid.has(n.id)) continue;
      const ch = (kids[n.id] || []).filter(c => !(isView && hid.has(c.n.id)));
      out.push(treeRow(n, depth, ch.length > 0, via, hid.has(n.id)));
      if (ch.length && !treeClosed.has(n.id)) walk(ch, depth + 1, new Set([...path, n.id]));
    }
  };
  walk(roots, 0, new Set());
  el.innerHTML = out.join("");
  el.querySelectorAll(".tr[data-id]").forEach(r => r.onclick = e => {
    const id = r.dataset.id, n = S.byId[id];
    if (e.target.classList.contains("tw") && e.target.textContent) {
      if (treeClosed.has(id)) treeClosed.delete(id); else treeClosed.add(id);
      renderTree($("#exOutline")); if (shown("tree")) renderTree();
      return;
    }
    if (n && n.kind !== "external") jumpTo(n.line);
    focusNode(id, false);
  });
  if (S.selected) markSelected(S.selected, false);
}

// ---------- chọn node: đánh dấu ở Tree / Outline / Book / Graph, hiện ở Inspector ----------
function markSelected(id, scroll) {
  for (const el of $$(".tr.on, .book article.on, .mod.on")) el.classList.remove("on");
  if (!id) return;
  const sel = `[data-id="${CSS.escape(id)}"]`;
  for (const el of $$(`#treeView .tr${sel}, #exOutline .tr${sel}, #bookView article${sel}, #moduleView .mod${sel}`)) {
    el.classList.add("on");
    if (el.closest("#moduleView")) continue;                // SVG có pan / zoom riêng, không cuộn
    if (scroll !== false || el.closest(".view.on, #exOutline")) el.scrollIntoView({block:"nearest"});
  }
}
function focusNode(id, scroll) {
  S.selected = id; S.selLink = null;
  if (nodesDS.get(id) && !S.hidden.has(id) && !net.getSelectedNodes().includes(id)) net.selectNodes([id]);
  markSelected(id, scroll);
  renderInspector();
}
