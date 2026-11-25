// run.js - Run button (Ctrl+Enter): POST the editor text to /api/run, show the result in the OUTPUT panel
(() => {
  const panel = $("#outPanel"), body = $("#outBody"), KEY = "kgout";
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; } };
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
  const st = {h:180, open:false, collapsed:false, ...load()};
  function apply() {
    panel.hidden = !st.open || !!ST;
    panel.style.height = st.h + "px";
    panel.classList.toggle("collapsed", st.collapsed);
    $("#outToggle").textContent = st.collapsed ? "▴" : "▾";
  }
  function line(text, cls) {
    const d = document.createElement("div"); d.textContent = text; if (cls) d.className = cls; body.appendChild(d);
  }
  const kind = s => /:\s*E\d+\b|error|not available/i.test(s) ? "err" : /warning/i.test(s) ? "warn" : "";
  const sb = $("#sbRun");
  function status(cls, text) { sb.className = cls; sb.textContent = text; }
  sb.addEventListener("click", () => { st.open = true; st.collapsed = false; apply(); save(); });
  let busy = false;
  async function run() {
    if (ST || !S.name || busy) return;
    busy = true; st.open = true; st.collapsed = false; apply(); save();
    if (body.childNodes.length) line("");
    status("busy", "⟳ Running…");
    let j;
    try {
      const r = await fetch("/api/run", {method:"POST", headers:{"Content-Type":"application/json"},
                                         body:JSON.stringify({name:S.name, text:src.value})});
      j = await r.json().catch(() => ({ok:false, outputs:[], diags:["HTTP " + r.status], ms:0}));
    } catch (e) { j = {ok:false, outputs:[], diags:[String(e.message || e)], ms:0}; }
    busy = false;
    const diags = j.diags || (j.error ? [j.error] : []);
    const nErr = diags.filter(d => kind(d) !== "warn").length;
    status(j.ok ? "ok" : "err", j.ok ? `✓ Run OK · ${(j.outputs || []).length} line(s) · ${j.ms || 0} ms`
                                     : `✗ Run failed · ${nErr || 1} error(s)`);
    line(`> kir run ${S.name} (exit ${j.ok ? 0 : 1}, ${j.ms || 0} ms)`, "cmd");
    for (const o of j.outputs || []) for (const l of String(o).split("\n")) line(l);
    for (const d of diags) line(d, kind(d) || (j.ok ? "" : "err"));
    body.scrollTop = body.scrollHeight;
  }
  $("#bRun").addEventListener("click", run);
  src.addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); }
  });
  $("#outClear").addEventListener("click", () => { body.textContent = ""; });
  $("#outToggle").addEventListener("click", () => { st.collapsed = !st.collapsed; apply(); save(); });
  $("#outClose").addEventListener("click", () => { st.open = false; apply(); save(); });
  $("#outSplit").addEventListener("pointerdown", e => {
    e.preventDefault();
    const y0 = e.clientY, h0 = panel.offsetHeight, max = () => panel.parentElement.clientHeight - 80;
    const mv = ev => { st.h = Math.max(60, Math.min(max(), h0 + y0 - ev.clientY)); apply(); };
    const up = () => { removeEventListener("pointermove", mv); removeEventListener("pointerup", up); save(); };
    addEventListener("pointermove", mv); addEventListener("pointerup", up);
  });
  apply();
})();
