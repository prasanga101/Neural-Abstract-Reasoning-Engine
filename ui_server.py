# ui_server.py
from flask import Flask, request
from pathlib import Path
import json

from gemini_call import generate_plan  # uses YOUR existing code

app = Flask(__name__)
DEMO_PLAN_PATH = Path("sample_plan.json")


@app.get("/")
def index():
    return r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>NARE Visualizer</title>

  <!-- Cytoscape (graph) -->
  <script src="https://unpkg.com/cytoscape@3.27.0/dist/cytoscape.min.js"></script>
  <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
  <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>

  <style>
    :root{
      --bg:#0b0f19;
      --card:#111827;
      --card2:#0f172a;
      --muted:#94a3b8;
      --text:#e5e7eb;
      --line:#1f2a44;
      --accent:#60a5fa;
      --good:#34d399;
      --warn:#fbbf24;
      --bad:#f87171;
    }
    *{ box-sizing:border-box; }
    body{ margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto; background:var(--bg); color:var(--text); }

    #topbar{
      display:flex; gap:10px; align-items:center;
      padding:14px 16px;
      border-bottom:1px solid var(--line);
      background: rgba(17,24,39,.8);
      backdrop-filter: blur(8px);
      position: sticky; top:0; z-index: 50;
    }
    #task{
      width: min(620px, 60vw);
      padding: 11px 12px;
      border-radius: 14px;
      border: 1px solid #22304d;
      background: #0b1224;
      color: var(--text);
      outline: none;
    }
    #mode{
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px solid #22304d;
      background: #0b1224;
      color: var(--text);
      outline: none;
      cursor:pointer;
    }
    .btn{
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px solid #22304d;
      background: linear-gradient(180deg, #142042, #0b1224);
      color: var(--text);
      cursor: pointer;
      transition: transform .08s ease;
      user-select: none;
    }
    .btn:active{ transform: scale(.98); }
    .btn.primary{
      border-color: rgba(96,165,250,.35);
      background: linear-gradient(180deg, rgba(96,165,250,.25), rgba(15,23,42,.9));
    }
    .btn.ghost{
      background: transparent;
    }
    #status{ color: var(--muted); font-size: 13px; margin-left: 6px; }

    #wrap{
      height: calc(100vh - 62px);
      display:grid;
      grid-template-columns: 1fr 420px;
    }

    /* Left side: graph + timeline */
    #left{
      height: 100%;
      display:flex;
      flex-direction: column;
      border-right: 1px solid var(--line);
      min-width: 0;
    }

    #cy{
      flex: 1;
      min-height: 0;
      width: 100%;
      background: radial-gradient(1200px 600px at 30% 20%, rgba(96,165,250,.08), transparent 60%),
                  radial-gradient(900px 500px at 70% 70%, rgba(52,211,153,.07), transparent 55%);
    }

    /* Timeline bar */
    #timelineBar{
      border-top: 1px solid var(--line);
      background: rgba(2,6,23,.35);
      padding: 10px 12px 12px;
    }

    .tlRow{
      display:flex;
      gap:10px;
      align-items:center;
      flex-wrap: wrap;
    }

    .tlRow2{
      margin-top: 10px;
      display:grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }

    .tlTitle{
      font-size: 12px;
      color: #cbd5e1;
      border: 1px solid rgba(31,42,68,.8);
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(2,6,23,.35);
    }

    .tlMeta{
      font-size: 12px;
      color: var(--muted);
    }

    #speed{ width: 220px; }
    #scrub{ width: 100%; }

    #timeline{
      width: 100%;
      border: 1px solid rgba(31,42,68,.8);
      border-radius: 14px;
      background: rgba(2,6,23,.45);
      display:block;
    }

    .tlHint{
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
    }

    /* Right panel */
    #panel{
      height: 100%;
      padding: 16px;
      background: linear-gradient(180deg, rgba(17,24,39,.9), rgba(15,23,42,.95));
      overflow:auto;
      min-width: 0;
    }
    .card{
      background: rgba(15,23,42,.7);
      border: 1px solid rgba(31,42,68,.9);
      border-radius: 18px;
      padding: 14px;
      box-shadow: 0 12px 30px rgba(0,0,0,.25);
      margin-bottom: 12px;
    }
    .h{ margin: 0 0 8px; font-size: 14px; color: #eaf0ff; letter-spacing: .2px; }
    .muted{ color: var(--muted); font-size: 13px; line-height: 1.45; }
    pre{
      margin: 10px 0 0;
      background: rgba(2,6,23,.7);
      border: 1px solid rgba(31,42,68,.8);
      padding: 10px;
      border-radius: 14px;
      overflow:auto;
      font-size: 12px;
      color: #dbeafe;
    }
    .pill{
      font-size: 12px;
      color: #cbd5e1;
      border: 1px solid rgba(31,42,68,.8);
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(2,6,23,.35);
    }
  </style>
</head>

<body>
  <div id="topbar">
    <span class="pill">NARE</span>
    <span class="pill">Planner Graph</span>

    <input id="task" value="Sort these in Ascending Order: 5, 2, 9, 1" />

    <select id="mode">
      <option value="demo" selected>Demo (0 calls)</option>
      <option value="live">Live (uses Gemini)</option>
    </select>

    <button class="btn primary" id="run">Run</button>
    <button class="btn ghost" id="layout">Auto-layout</button>
    <button class="btn ghost" id="play">Play steps</button>
    <button class="btn ghost" id="stop">Stop</button>

    <span id="status">Idle • Drag nodes to rearrange</span>
  </div>

  <div id="wrap">
    <div id="left">
      <div id="cy"></div>

      <!-- Timeline / Matplotlib-like animation bar -->
      <div id="timelineBar">
        <div class="tlRow">
          <span class="tlTitle">Linear Processing</span>
          <span class="tlMeta" id="tlMeta">0 / 0</span>
          <span class="tlMeta" id="tlSpeedLabel">1.00×</span>
          <input id="speed" type="range" min="0.25" max="3" step="0.05" value="1">

          <button class="btn ghost" id="tlPrev">⟵</button>
          <button class="btn ghost" id="tlPause">Pause</button>
          <button class="btn ghost" id="tlNext">⟶</button>
          <button class="btn ghost" id="tlReplay">Replay</button>
        </div>

        <div class="tlRow2">
          <input id="scrub" type="range" min="0" max="0" step="1" value="0">
          <canvas id="timeline" height="56"></canvas>
        </div>
        <div class="tlHint" id="tlHint">Play steps to visualize linear processing. Drag the scrubber to jump.</div>
      </div>
    </div>

    <div id="panel">
      <div class="card">
        <p class="h">How to use</p>
        <p class="muted">
          • Click <b>Run</b> to load a plan.<br>
          • Drag nodes to rearrange.<br>
          • Click any node for details.<br>
          • Click <b>Play steps</b> to animate Task → Step 1 → … → Output.<br>
          • Use the timeline to control speed and replay.
        </p>
      </div>

      <div class="card">
        <p class="h">Selected node</p>
        <div id="details" class="muted">Click a node…</div>
      </div>

      <div class="card">
        <p class="h">Raw plan</p>
        <pre id="raw">{}</pre>
      </div>
    </div>
  </div>

<script>
  cytoscape.use(cytoscapeDagre);

  const statusEl = document.getElementById("status");
  const detailsEl = document.getElementById("details");
  const rawEl = document.getElementById("raw");

  // Timeline controls
  let baseIntervalMs = 900;
  let speedMultiplier = 1.0;
  let paused = false;

  const speedEl = document.getElementById("speed");
  const speedLabel = document.getElementById("tlSpeedLabel");
  const scrubEl = document.getElementById("scrub");
  const canvas = document.getElementById("timeline");
  const ctx = canvas.getContext("2d");
  const tlMeta = document.getElementById("tlMeta");
  const tlHint = document.getElementById("tlHint");

  // Playback state
  let playTimer = null;
  let currentOrder = [];
  let currentIndex = 0; // points to the currently highlighted element in currentOrder

  const cy = cytoscape({
    container: document.getElementById("cy"),
    elements: [],
    style: [
      { selector: "node", style: {
          "shape":"round-rectangle",
          "label":"data(label)",
          "text-wrap":"wrap",
          "text-max-width": 190,
          "font-size": 12,
          "padding": 12,
          "border-width": 1,
          "border-color": "rgba(96,165,250,.22)",
          "background-color": "rgba(15,23,42,.85)",
          "color": "#e5e7eb"
      }},
      { selector: 'node[type="task"]', style: {
          "border-width": 2,
          "border-color": "rgba(52,211,153,.45)"
      }},
      { selector: 'node[type="output"]', style: {
          "border-width": 2,
          "border-color": "rgba(251,191,36,.45)"
      }},
      { selector: "edge", style: {
          "curve-style": "bezier",
          "target-arrow-shape": "triangle",
          "width": 2,
          "line-color": "rgba(148,163,184,.35)",
          "target-arrow-color": "rgba(148,163,184,.55)"
      }},
      { selector: ".active", style: {
          "border-width": 3,
          "border-color": "rgba(96,165,250,.9)",
          "background-color": "rgba(30,41,59,.95)"
      }},
      { selector: ".done", style: {
          "border-color": "rgba(52,211,153,.75)"
      }}
    ],
    layout: { name:"dagre", rankDir:"LR", nodeSep: 70, rankSep: 110 }
  });

  function short(text, n=84){
    text = (text || "").trim();
    return text.length > n ? text.slice(0,n) + "…" : text;
  }

  // -------- Timeline drawing --------
  function resizeCanvas(){
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(rect.width * dpr);
    canvas.height = Math.floor(56 * dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }

  window.addEventListener("resize", () => {
    drawTimeline();
  });

  function stepCount(){
    return currentOrder.length;
  }

  function roundRect(ctx, x, y, w, h, r){
    const rr = Math.min(r, w/2, h/2);
    ctx.beginPath();
    ctx.moveTo(x+rr, y);
    ctx.arcTo(x+w, y, x+w, y+h, rr);
    ctx.arcTo(x+w, y+h, x, y+h, rr);
    ctx.arcTo(x, y+h, x, y, rr);
    ctx.arcTo(x, y, x+w, y, rr);
    ctx.closePath();
  }

  function drawTimeline(){
    resizeCanvas();

    const w = canvas.clientWidth;
    const h = canvas.clientHeight;

    ctx.clearRect(0,0,w,h);

    const n = stepCount();
    if(!n){
      ctx.fillStyle = "rgba(148,163,184,.6)";
      ctx.font = "12px system-ui";
      ctx.fillText("No plan loaded.", 12, 28);
      tlMeta.textContent = "0 / 0";
      scrubEl.max = "0";
      scrubEl.value = "0";
      return;
    }

    const pad = 12;
    const barY = 18;
    const barH = 18;
    const gap = 6;
    const usableW = w - pad*2;
    const cellW = Math.max(14, (usableW - gap*(n-1))/n);

    for(let i=0;i<n;i++){
      const x = pad + i*(cellW + gap);

      if(i < currentIndex) ctx.fillStyle = "rgba(52,211,153,.55)";        // done
      else if(i === currentIndex) ctx.fillStyle = "rgba(96,165,250,.65)"; // active
      else ctx.fillStyle = "rgba(148,163,184,.18)";                       // upcoming

      roundRect(ctx, x, barY, cellW, barH, 8);
      ctx.fill();

      ctx.fillStyle = "rgba(229,231,235,.85)";
      ctx.font = "11px system-ui";
      let label = "";
      if(i === 0) label = "T";
      else if(i === n-1) label = "O";
      else label = String(i); // step number index
      ctx.fillText(label, x + 6, barY + 13);
    }

    tlMeta.textContent = `${Math.min(currentIndex, n)} / ${n}`;
  }

  // -------- Graph + details --------
  function showDetails(node){
    const d = node.data();
    if(d.type === "step"){
      const s = d.full;
      detailsEl.innerHTML =
        `<div><b>Step ${s.step_id}</b></div>
         <div style="margin-top:6px;">${s.step_description}</div>
         <div style="margin-top:10px;color:#94a3b8;">Tools</div>
         <pre>${JSON.stringify(s.required_tools || [], null, 2)}</pre>
         <div style="margin-top:10px;color:#94a3b8;">Produced</div>
         <pre>${JSON.stringify(s.produced_content || [], null, 2)}</pre>`;
    } else if(d.type === "task"){
      detailsEl.innerHTML = `<div><b>Task</b></div><div style="margin-top:6px;">${d.full.task || ""}</div>`;
    } else {
      detailsEl.innerHTML = `<div><b>Final Output</b></div><div style="margin-top:6px;">${d.full.final_output || ""}</div>`;
    }
  }

  cy.on("tap", "node", (evt) => showDetails(evt.target));

  function buildGraph(plan){
    const els = [];
    const steps = plan.reasoning_steps || [];

    els.push({
      data: { id:"task", type:"task", full: {task: plan.task}, label:"Task\\n" + short(plan.task, 90) }
    });

    for(const s of steps){
      els.push({
        data: {
          id: "s" + s.step_id,
          type: "step",
          full: s,
          label: "Step " + s.step_id + "\\n" + short(s.step_description, 95)
        }
      });
    }

    els.push({
      data: { id:"out", type:"output", full: {final_output: plan.final_output}, label:"Output\\n" + short(plan.final_output, 90) }
    });

    // Linear edges
    if(steps.length){
      els.push({ data:{ id:"e_task", source:"task", target:"s"+steps[0].step_id } });
      for(let i=0;i<steps.length-1;i++){
        els.push({ data:{ id:`e_${i}`, source:"s"+steps[i].step_id, target:"s"+steps[i+1].step_id }});
      }
      els.push({ data:{ id:"e_out", source:"s"+steps[steps.length-1].step_id, target:"out" }});
    } else {
      els.push({ data:{ id:"e_task_out", source:"task", target:"out" }});
    }

    cy.elements().remove();
    cy.add(els);
    cy.layout({ name:"dagre", rankDir:"LR", nodeSep: 70, rankSep: 110 }).run();
    cy.fit();

    // Playback order
    currentOrder = ["task", ...steps.map(s => "s"+s.step_id), "out"];
    currentIndex = 0;

    // Reset styling
    cy.nodes().removeClass("active done");

    // Timeline reset
    scrubEl.max = String(Math.max(0, currentOrder.length - 1));
    scrubEl.value = "0";
    tlHint.textContent = "Play steps to visualize linear processing. Drag the scrubber to jump.";
    drawTimeline();
  }

  // -------- Playback engine --------
  function stopPlay(){
    if(playTimer) clearInterval(playTimer);
    playTimer = null;
    paused = false;
    document.getElementById("tlPause").textContent = "Pause";
    statusEl.textContent = "Stopped • Drag nodes to rearrange";
    drawTimeline();
  }

  function jumpTo(k){
    const n = stepCount();
    if(!n) return;

    currentIndex = Math.max(0, Math.min(k, n-1));
    scrubEl.max = String(n-1);
    scrubEl.value = String(currentIndex);

    cy.nodes().removeClass("active done");

    for(let i=0;i<currentIndex;i++){
      cy.getElementById(currentOrder[i]).addClass("done");
    }

    const node = cy.getElementById(currentOrder[currentIndex]);
    node.addClass("active");
    showDetails(node);

    cy.animate({ center: { eles: node }, zoom: Math.max(cy.zoom(), 1.1) }, { duration: 250 });
    drawTimeline();
  }

  function tick(){
    if(paused) return;

    const n = stepCount();
    if(!n) return;

    if(currentIndex >= n){
      stopPlay();
      statusEl.textContent = "Done ✓";
      return;
    }

    cy.nodes().removeClass("active");
    if(currentIndex > 0){
      cy.getElementById(currentOrder[currentIndex-1]).addClass("done");
    }

    const node = cy.getElementById(currentOrder[currentIndex]);
    node.addClass("active");
    showDetails(node);

    cy.animate({ center: { eles: node }, zoom: Math.max(cy.zoom(), 1.1) }, { duration: 300 });

    scrubEl.value = String(currentIndex);
    drawTimeline();

    currentIndex += 1;
  }

  function playSteps(){
    stopPlay();

    const n = stepCount();
    if(!n){
      statusEl.textContent = "No plan loaded";
      return;
    }

    paused = false;
    document.getElementById("tlPause").textContent = "Pause";
    statusEl.textContent = "Playing…";
    tlHint.textContent = "Drag scrubber to jump. Adjust speed slider to control animation.";

    // Start from currentIndex as-is (supports replay/jump then play)
    playTimer = setInterval(tick, Math.max(120, baseIntervalMs / speedMultiplier));
  }

  // -------- Controls wiring (ONLY ONCE) --------
  speedEl.addEventListener("input", () => {
    speedMultiplier = parseFloat(speedEl.value);
    speedLabel.textContent = speedMultiplier.toFixed(2) + "×";

    if(playTimer){
      clearInterval(playTimer);
      playTimer = setInterval(tick, Math.max(120, baseIntervalMs / speedMultiplier));
    }
  });

  scrubEl.addEventListener("input", () => {
    stopPlay();
    const target = parseInt(scrubEl.value, 10);
    jumpTo(target);
  });

  document.getElementById("tlPrev").addEventListener("click", () => {
    stopPlay();
    jumpTo(Math.max(0, currentIndex - 1));
  });

  document.getElementById("tlNext").addEventListener("click", () => {
    stopPlay();
    jumpTo(Math.min(stepCount()-1, currentIndex + 1));
  });

  document.getElementById("tlReplay").addEventListener("click", () => {
    stopPlay();
    currentIndex = 0;
    scrubEl.value = "0";
    cy.nodes().removeClass("active done");
    drawTimeline();
    playSteps();
  });

  document.getElementById("tlPause").addEventListener("click", (e) => {
    if(!playTimer) return;
    paused = !paused;
    e.target.textContent = paused ? "Resume" : "Pause";
    statusEl.textContent = paused ? "Paused" : "Playing…";
  });

  document.getElementById("layout").addEventListener("click", () => {
    cy.layout({ name:"dagre", rankDir:"LR", nodeSep: 70, rankSep: 110 }).run();
    cy.fit();
  });

  document.getElementById("play").addEventListener("click", playSteps);
  document.getElementById("stop").addEventListener("click", stopPlay);

  // -------- Run plan (Demo/Live) --------
  async function run(){
    stopPlay();

    const task = document.getElementById("task").value;
    const mode = document.getElementById("mode").value;

    statusEl.textContent = mode === "live" ? "Calling model…" : "Loading demo…";

    const res = await fetch("/plan", {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ task, mode })
    });

    const data = await res.json();
    if(!res.ok){
      statusEl.textContent = "Error: " + (data.error || "unknown");
      return;
    }

    const plan = data.plan;
    rawEl.textContent = JSON.stringify(plan, null, 2);
    buildGraph(plan);

    statusEl.textContent = (data.mode === "live" ? "Live plan ✓" : "Demo plan ✓") + " • Drag nodes freely";
  }

  document.getElementById("run").addEventListener("click", run);

  // Draw empty timeline initially
  drawTimeline();
</script>
</body>
</html>
"""


@app.post("/plan")
def plan():
    payload = request.get_json(force=True) or {}
    mode = (payload.get("mode") or "demo").strip().lower()
    task = (payload.get("task") or "").strip()

    # DEMO mode: 0 API calls
    if mode == "demo":
        if not DEMO_PLAN_PATH.exists():
            return {"error": "sample_plan.json not found. Create it to use Demo mode."}, 400
        plan_obj = json.loads(DEMO_PLAN_PATH.read_text(encoding="utf-8"))
        return {"plan": plan_obj, "mode": "demo"}

    # LIVE mode: uses your Gemini call (quota)
    if not task:
        return {"error": "task is required in live mode"}, 400

    try:
        # If quota is tight, reduce retries to 1
        plan_obj = generate_plan(task, retries=1)
        return {"plan": plan_obj, "mode": "live"}
    except Exception as e:
        msg = str(e)
        code = 429 if ("429" in msg or "RESOURCE_EXHAUSTED" in msg) else 500
        return {"error": msg}, code


if __name__ == "__main__":
    app.run(port=5000, debug=True)