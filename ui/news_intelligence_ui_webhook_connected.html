<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>News Intelligence Workspace · Webhook Connected</title>
  <style>
    :root{
      --bg:#08101b; --bg2:#0d1526; --panel:#111b31; --panel2:#16223e; --line:#263658;
      --text:#e9f0ff; --muted:#8fa4cb; --accent:#5fb2ff; --accent2:#8b5cf6;
      --success:#2dd4bf; --warn:#f59e0b; --danger:#ef4444; --radius:18px; --shadow:0 18px 44px rgba(0,0,0,.34);
    }
    *{box-sizing:border-box}
    html,body{margin:0;height:100%}
    body{
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      background:
        radial-gradient(1200px 600px at 10% -10%, rgba(95,178,255,.12), transparent 60%),
        radial-gradient(900px 500px at 100% 0%, rgba(139,92,246,.10), transparent 50%),
        linear-gradient(180deg, #07101d, #0a1222 40%, #08101b);
      color:var(--text);
    }
    .app{display:grid;grid-template-columns:320px 1fr;min-height:100vh}
    .sidebar{
      background:rgba(9,14,27,.84);backdrop-filter:blur(14px);border-right:1px solid var(--line);
      padding:22px 18px;position:sticky;top:0;height:100vh;overflow:auto;
    }
    .brand{
      display:flex;gap:12px;align-items:center;background:linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.01));
      border:1px solid var(--line);border-radius:16px;padding:12px;box-shadow:var(--shadow);margin-bottom:18px;
    }
    .logo{
      width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,var(--accent),var(--accent2));
      display:grid;place-items:center;font-weight:800;letter-spacing:.04em
    }
    .brand h1{font-size:15px;margin:0}
    .brand p{margin:4px 0 0;color:var(--muted);font-size:12px}
    .section-title{margin:16px 8px 8px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
    .field{margin-bottom:12px}
    .label{font-size:12px;color:var(--muted);margin-bottom:6px;display:block}
    input, select, textarea{
      width:100%;background:var(--panel);color:var(--text);border:1px solid var(--line);
      border-radius:14px;padding:12px 13px;outline:none;font:inherit;
    }
    textarea{min-height:420px;resize:vertical;line-height:1.5;font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:13px;background:#0c1426}
    .btn{
      width:100%;border:0;border-radius:14px;padding:12px 14px;font-weight:700;color:white;cursor:pointer;
      background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 14px 26px rgba(95,178,255,.24);margin-top:6px;
    }
    .btn.secondary{background:var(--panel2);border:1px solid var(--line);box-shadow:none}
    .btn-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
    .chip-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
    .chip{background:#182541;border:1px solid var(--line);color:var(--text);font-size:12px;padding:6px 10px;border-radius:999px}
    .nav{display:grid;gap:6px;margin-top:8px}
    .nav button{
      text-align:left;width:100%;background:transparent;border:1px solid transparent;color:var(--text);padding:11px 12px;border-radius:13px;cursor:pointer;
    }
    .nav button.active,.nav button:hover{background:linear-gradient(180deg, rgba(95,178,255,.12), rgba(95,178,255,.04));border-color:var(--line)}
    .tiny{font-size:12px;color:var(--muted)}
    .main{padding:24px}
    .topbar{display:flex;justify-content:space-between;gap:14px;align-items:center;flex-wrap:wrap;margin-bottom:18px}
    .title h2{margin:0;font-size:28px}
    .title p{margin:6px 0 0;color:var(--muted)}
    .status{display:flex;gap:10px;flex-wrap:wrap}
    .pill{background:rgba(255,255,255,.03);border:1px solid var(--line);padding:8px 10px;border-radius:999px;font-size:12px;color:var(--muted)}
    .grid{display:grid;grid-template-columns:repeat(12,1fr);gap:18px}
    .card{
      background:linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.015));
      border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;
    }
    .span-4{grid-column:span 4}.span-5{grid-column:span 5}.span-7{grid-column:span 7}.span-8{grid-column:span 8}.span-12{grid-column:span 12}
    .card-head{padding:16px 18px 0;display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap}
    .card-head h3{margin:0;font-size:17px}
    .card-body{padding:18px}
    .helper{font-size:12px;color:var(--muted)}
    .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
    .kpi{padding:14px;border-radius:16px;background:var(--panel);border:1px solid var(--line)}
    .kpi .label{margin:0}.kpi b{display:block;font-size:23px;margin-top:6px}
    .steps{display:grid;gap:10px}
    .step{display:grid;grid-template-columns:40px 1fr;gap:12px;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:12px}
    .step .n{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2))}
    .editor-toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px}
    .editor-toolbar button{
      background:var(--panel);border:1px solid var(--line);color:var(--text);padding:10px 12px;border-radius:12px;cursor:pointer;font-size:12px;
    }
    .filelist{display:grid;gap:10px;max-height:460px;overflow:auto}
    .fileitem{border:1px solid var(--line);background:var(--panel);border-radius:14px;padding:12px;cursor:pointer}
    .fileitem.active{outline:1px solid rgba(95,178,255,.45);background:#15223e}.fileitem b{display:block;margin-bottom:6px}
    pre{
      margin:0;background:#0c1426;border:1px solid var(--line);border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;
      font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:12px;color:#dce8ff;
    }
    .notice{padding:12px 14px;border-radius:14px;background:rgba(45,212,191,.08);border:1px solid rgba(45,212,191,.20);color:#b6fff1}
    .notice.warn{background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.18);color:#ffe2a4}
    .notice.bad{background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.18);color:#ffc6c6}
    @media (max-width: 1180px){
      .app{grid-template-columns:1fr}.sidebar{position:relative;height:auto}
      .span-4,.span-5,.span-7,.span-8,.span-12{grid-column:span 12}.kpis{grid-template-columns:repeat(2,1fr)}
    }
  </style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="logo">NI</div>
      <div>
        <h1>Webhook-Connected Workspace</h1>
        <p>Topic + days in, markdown artifacts back</p>
      </div>
    </div>

    <div class="section-title">Run Input</div>
    <div class="field">
      <label class="label">Topic</label>
      <input id="topicInput" value="Strait of Hormuz" />
    </div>
    <div class="field">
      <label class="label">Research Window</label>
      <select id="daysInput">
        <option value="3">3 days</option>
        <option value="5">5 days</option>
        <option value="7" selected>7 days</option>
        <option value="14">14 days</option>
        <option value="30">30 days</option>
      </select>
    </div>

    <div class="section-title">Orchestration</div>
    <div class="field">
      <label class="label">Provider</label>
      <select id="providerInput">
        <option value="n8n" selected>n8n</option>
        <option value="make">Make</option>
        <option value="zapier">Zapier</option>
        <option value="custom">Custom Webhook</option>
      </select>
    </div>
    <div class="field">
      <label class="label">Webhook URL</label>
      <input id="webhookUrlInput" placeholder="https://your-webhook-endpoint" />
    </div>
    <div class="field">
      <label class="label">Auth Token (optional)</label>
      <input id="authTokenInput" placeholder="Bearer token or custom token" />
    </div>

    <button class="btn" id="runBtn">Run Orchestration</button>
    <div class="btn-row">
      <button class="btn secondary" id="generateLocalBtn">Generate Local Draft</button>
      <button class="btn secondary" id="resetBtn">Reset</button>
    </div>
    <div class="btn-row">
      <button class="btn secondary" id="downloadCurrentBtn">Download File</button>
      <button class="btn secondary" id="downloadAllBtn">Download All .md</button>
    </div>

    <div class="section-title">Workspace Files</div>
    <div class="nav" id="fileNav"></div>

    <div class="section-title">Run Flags</div>
    <div class="chip-row">
      <span class="chip">Wiki Off</span>
      <span class="chip">Webhook Mode</span>
      <span class="chip">HTML + JS Only</span>
    </div>
  </aside>

  <main class="main">
    <div class="topbar">
      <div class="title">
        <h2 id="heroTitle">Agent Workspace</h2>
        <p>The UI sends only topic, days, and run options to a no-code orchestration layer, then renders returned markdown artifacts for review and editing.</p>
      </div>
      <div class="status">
        <span class="pill" id="statusTopic">Topic: Strait of Hormuz</span>
        <span class="pill" id="statusDays">Window: 7 days</span>
        <span class="pill" id="statusProvider">Provider: n8n</span>
      </div>
    </div>

    <section class="grid">
      <div class="card span-12">
        <div class="card-head">
          <h3>Operator Model</h3>
          <span class="helper">Only two required user inputs</span>
        </div>
        <div class="card-body">
          <div class="kpis">
            <div class="kpi"><span class="label">Required Inputs</span><b>2</b></div>
            <div class="kpi"><span class="label">Workspace Files</span><b id="kpiFiles">11</b></div>
            <div class="kpi"><span class="label">Webhook Mode</span><b>On</b></div>
            <div class="kpi"><span class="label">Wiki Layer</span><b>Off</b></div>
          </div>
        </div>
      </div>

      <div class="card span-4">
        <div class="card-head">
          <h3>How the handoff works</h3>
          <span class="helper">No-code orchestration endpoint</span>
        </div>
        <div class="card-body">
          <div class="steps">
            <div class="step"><div class="n">1</div><div><strong>User enters topic + days</strong><div class="tiny">No manual file setup required.</div></div></div>
            <div class="step"><div class="n">2</div><div><strong>UI sends JSON payload</strong><div class="tiny">Topic, day window, wiki=false, requested artifacts.</div></div></div>
            <div class="step"><div class="n">3</div><div><strong>Orchestrator runs workflow</strong><div class="tiny">Collect, cluster, analyze, and draft markdown artifacts.</div></div></div>
            <div class="step"><div class="n">4</div><div><strong>UI receives files</strong><div class="tiny">Returned markdown becomes editable in-browser.</div></div></div>
          </div>
        </div>
      </div>

      <div class="card span-8">
        <div class="card-head">
          <h3>Request / Response Preview</h3>
          <span class="helper">Use this JSON shape in your no-code tool</span>
        </div>
        <div class="card-body">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
            <div>
              <div class="tiny" style="margin-bottom:8px">Outbound request</div>
              <pre id="payloadPreview"></pre>
            </div>
            <div>
              <div class="tiny" style="margin-bottom:8px">Expected response shape</div>
              <pre>{
  "status": "ok",
  "topic": "Strait of Hormuz",
  "days": 7,
  "files": {
    "run_brief.md": "# Run Brief ...",
    "source_ledger.md": "# Source Ledger ...",
    "final_report.md": "# Final Report ..."
  },
  "meta": {
    "provider": "n8n",
    "generated_at": "2026-04-15T00:00:00Z"
  }
}</pre>
            </div>
          </div>
          <div id="runMessage" class="notice warn" style="margin-top:14px">Add a webhook URL, then click “Run Orchestration.” If no webhook is supplied, you can still generate a local draft workspace.</div>
        </div>
      </div>

      <div class="card span-5">
        <div class="card-head">
          <h3>Generated Files</h3>
          <span class="helper">Returned by the webhook or created locally</span>
        </div>
        <div class="card-body">
          <div class="filelist" id="fileList"></div>
        </div>
      </div>

      <div class="card span-7">
        <div class="card-head">
          <h3>Markdown Editor</h3>
          <span class="helper" id="editorFileName">run_brief.md</span>
        </div>
        <div class="card-body">
          <div class="editor-toolbar">
            <button id="restoreTemplateBtn">Restore Template</button>
            <button id="downloadEditorBtn">Download Current .md</button>
            <button id="copyBtn">Copy Current</button>
          </div>
          <textarea id="editor"></textarea>
        </div>
      </div>
    </section>
  </main>
</div>

<script>
  let files = {};
  let templatesStore = {};
  let activeFile = "run_brief.md";

  function todayISO(){ return new Date().toISOString().slice(0,10); }

  function scenarioTemplates(topic, days){
    return {
      "run_brief.md": `# Run Brief\n\n- Topic: ${topic}\n- Date Window: Past ${days} days ending ${todayISO()}\n- Wiki: Off\n- Depth: Extensive\n- Scope: Auto-generated from UI inputs\n`,
      "source_ledger.md": `# Source Ledger\n\n## Topic\n${topic}\n\n| Source | Date | Title | URL | Relevance |\n|---|---|---|---|---|\n|  |  |  |  |  |\n`,
      "article_registry.md": `# Article Registry\n\n| Article ID | Date | Source | Title | Level | Cluster |\n|---|---|---|---|---|---|\n|  |  |  |  |  |  |\n`,
      "deduplication_log.md": `# Deduplication Log\n\n- Deduplicate before escalating evidence.\n- Same event across multiple outlets should not be counted as multiple underlying events.\n`,
      "cluster_registry.md": `# Cluster Registry\n\n| Cluster ID | Name | Description | Key Articles |\n|---|---|---|---|\n| C1 |  |  |  |\n| C2 |  |  |  |\n`,
      "temporal_dataset.md": `# Temporal Dataset\n\n| Date | Count | Dominant Cluster | Notes |\n|---|---:|---|---|\n|  |  |  |  |\n`,
      "geospatial_dataset.md": `# Geospatial Dataset\n\n| Location | Type | Cluster | Notes |\n|---|---|---|---|\n|  |  |  |  |\n`,
      "sentiment_analysis_memo.md": `# Sentiment Analysis Memo\n\n## Topic\n${topic}\n\n## Tone Shifts\n-\n`,
      "narrative_comparison_memo.md": `# Narrative Comparison Memo\n\n## Agreements\n-\n\n## Divergences\n-\n`,
      "citation_index.md": `# Citation Index\n\n| Claim | Cluster | Articles | Sources | Label |\n|---|---|---|---|---|\n|  |  |  |  | supported |\n`,
      "final_report.md": `# Final Report\n\n## Topic\n${topic}\n\n## Window\nPast ${days} days ending ${todayISO()}\n\n## Executive Summary\n-\n`
    };
  }

  function currentPayload(){
    const topic = document.getElementById("topicInput").value.trim() || "Untitled Topic";
    const days = parseInt(document.getElementById("daysInput").value, 10);
    const provider = document.getElementById("providerInput").value;
    return {
      topic,
      days,
      wiki: false,
      provider,
      requested_artifacts: [
        "run_brief.md",
        "source_ledger.md",
        "article_registry.md",
        "deduplication_log.md",
        "cluster_registry.md",
        "temporal_dataset.md",
        "geospatial_dataset.md",
        "sentiment_analysis_memo.md",
        "narrative_comparison_memo.md",
        "citation_index.md",
        "final_report.md"
      ]
    };
  }

  function updatePayloadPreview(){
    const payload = currentPayload();
    document.getElementById("payloadPreview").textContent = JSON.stringify(payload, null, 2);
    document.getElementById("statusTopic").textContent = `Topic: ${payload.topic}`;
    document.getElementById("statusDays").textContent = `Window: ${payload.days} days`;
    document.getElementById("statusProvider").textContent = `Provider: ${payload.provider}`;
    document.getElementById("heroTitle").textContent = `${payload.topic} · Agent Workspace`;
  }

  function saveEditor(){
    const editor = document.getElementById("editor");
    if(activeFile && editor) files[activeFile] = editor.value;
  }

  function selectFile(name){
    saveEditor();
    activeFile = name;
    document.getElementById("editor").value = files[name] || "";
    document.getElementById("editorFileName").textContent = name;
    renderFileNav();
    renderFileList();
  }

  function renderFileNav(){
    const nav = document.getElementById("fileNav");
    nav.innerHTML = "";
    Object.keys(files).forEach(name => {
      const btn = document.createElement("button");
      btn.textContent = name;
      btn.className = name === activeFile ? "active" : "";
      btn.onclick = () => selectFile(name);
      nav.appendChild(btn);
    });
  }

  function renderFileList(){
    const list = document.getElementById("fileList");
    list.innerHTML = "";
    Object.keys(files).forEach(name => {
      const div = document.createElement("div");
      div.className = "fileitem" + (name === activeFile ? " active" : "");
      div.innerHTML = `<b>${name}</b><div class="tiny">${(files[name].split("\\n")[0] || "").replace(/^#\\s*/,"")}</div>`;
      div.onclick = () => selectFile(name);
      list.appendChild(div);
    });
    document.getElementById("kpiFiles").textContent = Object.keys(files).length;
  }

  function setFiles(newFiles){
    files = newFiles;
    templatesStore = JSON.parse(JSON.stringify(newFiles));
    activeFile = Object.keys(files)[0] || "run_brief.md";
    renderFileNav();
    renderFileList();
    selectFile(activeFile);
  }

  function setMessage(msg, type="warn"){
    const el = document.getElementById("runMessage");
    el.className = "notice" + (type === "warn" ? " warn" : type === "bad" ? " bad" : "");
    el.textContent = msg;
  }

  function generateLocalDraft(){
    const payload = currentPayload();
    setFiles(scenarioTemplates(payload.topic, payload.days));
    setMessage("Local draft generated. Connect a webhook URL to replace these templates with orchestrator output.", "warn");
  }

  function downloadText(filename, text){
    const blob = new Blob([text], {type:"text/markdown;charset=utf-8"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function runWebhook(){
    saveEditor();
    const url = document.getElementById("webhookUrlInput").value.trim();
    const token = document.getElementById("authTokenInput").value.trim();
    const payload = currentPayload();
    updatePayloadPreview();

    if(!url){
      setMessage("No webhook URL found. Add a webhook endpoint or use “Generate Local Draft.”", "bad");
      return;
    }

    setMessage("Running orchestration… waiting for webhook response.", "warn");

    try{
      const headers = { "Content-Type": "application/json" };
      if(token) headers["Authorization"] = token.startsWith("Bearer ") ? token : `Bearer ${token}`;

      const res = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(payload)
      });

      const text = await res.text();
      let data = {};
      try { data = JSON.parse(text); } catch {
        throw new Error("Webhook did not return valid JSON.");
      }

      if(!res.ok) throw new Error(data.message || `HTTP ${res.status}`);
      if(!data.files || typeof data.files !== "object") throw new Error("Webhook response is missing a files object.");

      setFiles(data.files);
      setMessage(`Run complete. Loaded ${Object.keys(data.files).length} markdown files from the orchestration layer.`, "ok");
    } catch(err){
      setMessage(`Run failed: ${err.message}`, "bad");
    }
  }

  document.getElementById("topicInput").addEventListener("input", updatePayloadPreview);
  document.getElementById("daysInput").addEventListener("change", updatePayloadPreview);
  document.getElementById("providerInput").addEventListener("change", updatePayloadPreview);

  document.getElementById("runBtn").addEventListener("click", runWebhook);
  document.getElementById("generateLocalBtn").addEventListener("click", generateLocalDraft);
  document.getElementById("resetBtn").addEventListener("click", () => {
    document.getElementById("topicInput").value = "Strait of Hormuz";
    document.getElementById("daysInput").value = "7";
    document.getElementById("providerInput").value = "n8n";
    document.getElementById("webhookUrlInput").value = "";
    document.getElementById("authTokenInput").value = "";
    updatePayloadPreview();
    generateLocalDraft();
  });

  document.getElementById("downloadCurrentBtn").addEventListener("click", () => {
    saveEditor();
    downloadText(activeFile, files[activeFile] || "");
  });

  document.getElementById("downloadEditorBtn").addEventListener("click", () => {
    saveEditor();
    downloadText(activeFile, files[activeFile] || "");
  });

  document.getElementById("downloadAllBtn").addEventListener("click", () => {
    saveEditor();
    Object.entries(files).forEach(([name, text], idx) => setTimeout(() => downloadText(name, text), idx * 150));
  });

  document.getElementById("copyBtn").addEventListener("click", async () => {
    saveEditor();
    await navigator.clipboard.writeText(files[activeFile] || "");
    setMessage("Current markdown copied to clipboard.", "ok");
  });

  document.getElementById("restoreTemplateBtn").addEventListener("click", () => {
    if(templatesStore[activeFile]) {
      files[activeFile] = templatesStore[activeFile];
      document.getElementById("editor").value = files[activeFile];
      renderFileList();
      setMessage(`Restored template for ${activeFile}.`, "ok");
    }
  });

  document.getElementById("editor").addEventListener("input", saveEditor);

  updatePayloadPreview();
  generateLocalDraft();
</script>
</body>
</html>
