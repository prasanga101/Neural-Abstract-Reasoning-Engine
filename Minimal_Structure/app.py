from flask import Flask, request
import json

from gemini_call import generate_plan  # your function returning validated plan dict

app = Flask(__name__)

@app.get("/")
def index():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>NARE Visualizer</title>
  <script src="https://unpkg.com/cytoscape@3.27.0/dist/cytoscape.min.js"></script>
  <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
  <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
  <style>
    body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto; }
    #topbar {
      display: flex; gap: 10px; align-items: center;
      padding: 12px 16px; border-bottom: 1px solid #e7e7e7;
    }
    input { width: 520px; padding: 10px 12px; border: 1px solid #ddd; border-radius: 12px; }
    button { padding: 10px 12px; border: 1px solid #ddd; border-radius: 12px; cursor: pointer; }
    #status { color: #555; font-size: 13px; }
    #wrap { display: grid; grid-template-columns: 1fr 360px; height: calc(100vh - 58px); }
    #cy { width: 100%; height: 100%; }
    #panel { border-left: 1px solid #e7e7e7; padding: 14px; overflow: auto; }
    .h { font-weight: 700; margin: 0 0 8px; }
    .muted { color: #666; font-size: 13px; }
    pre { background: #f6f6f6; padding: 10px; border-radius: 12px; overflow: auto; }
  </style>
</head>
<body>
  <div id="topbar">
    <input id="task" value="Sort these in Ascending Order: 5, 2, 9, 1" />
    <button id="run">Run (1 call)</button>
    <div id="status">Idle</div>
  </div>

  <div id="wrap">
    <div id="cy"></div>
    <div id="panel">
      <p class="h">Details</p>
      <p class="muted">Click a node to see full info here.</p>
      <div id="details"></div>
    </div>
  </div>

<script>
  cytoscape.use(cytoscapeDagre);

  const cy = cytoscape({
    container: document.getElementById('cy'),
    elements: [],
    style: [
      { selector: 'node', style: {
          'shape': 'round-rectangle',
          'label': 'data(label)',
          'text-wrap': 'wrap',
          'text-max-width': 170,
          'font-size': 12,
          'padding': 10,
          'border-width': 1
      }},
      { selector: 'node[type="task"]', style: { 'border-width': 2 } },
      { selector: 'node[type="output"]', style: { 'border-width': 2 } },
      { selector: 'edge', style: {
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'width': 2
      }}
    ],
    layout: { name: 'dagre', rankDir: 'LR', nodeSep: 60, rankSep: 90 }
  });

  const statusEl = document.getElementById("status");
  const detailsEl = document.getElementById("details");

  function short(text, n=90) {
    text = (text || "").trim();
    return text.length > n ? text.slice(0, n) + "…" : text;
  }

  function buildGraph(plan) {
    const els = [];

    els.push({ data: { id: "task", type: "task", full: plan, label: "Task\\n" + short(plan.task, 80) } });

    const steps = plan.reasoning_steps || [];
    for (const s of steps) {
      els.push({
        data: {
          id: "s" + s.step_id,
          type: "step",
          full: s,
          label: `Step ${s.step_id}\\n` + short(s.step_description, 85)
        }
      });
    }

    els.push({ data: { id: "out", type: "output", full: { final_output: plan.final_output }, label: "Output\\n" + short(plan.final_output, 80) } });

    if (steps.length) {
      els.push({ data: { id: "e_task", source: "task", target: "s" + steps[0].step_id } });
      for (let i = 0; i < steps.length - 1; i++) {
        els.push({ data: { id: `e_${i}`, source: "s" + steps[i].step_id, target: "s" + steps[i+1].step_id } });
      }
      els.push({ data: { id: "e_out", source: "s" + steps[steps.length - 1].step_id, target: "out" } });
    } else {
      els.push({ data: { id: "e_task_out", source: "task", target: "out" } });
    }

    cy.elements().remove();
    cy.add(els);
    cy.layout({ name: 'dagre', rankDir: 'LR', nodeSep: 60, rankSep: 90 }).run();
    cy.fit();
  }

  function showDetails(node) {
    const data = node.data();
    const t = data.type;

    if (t === "step") {
      const s = data.full;
      detailsEl.innerHTML = `
        <p class="h">Step ${s.step_id}</p>
        <p class="muted">${s.step_description}</p>
        <p class="h" style="margin-top:12px;">Tools</p>
        <pre>${JSON.stringify(s.required_tools || [], null, 2)}</pre>
        <p class="h" style="margin-top:12px;">Produced Content</p>
        <pre>${JSON.stringify(s.produced_content || [], null, 2)}</pre>
      `;
    } else if (t === "task") {
      detailsEl.innerHTML = `
        <p class="h">Task</p>
        <pre>${JSON.stringify(data.full.task || "", null, 2)}</pre>
      `;
    } else {
      detailsEl.innerHTML = `
        <p class="h">Final Output</p>
        <pre>${JSON.stringify(data.full.final_output || "", null, 2)}</pre>
      `;
    }
  }

  cy.on('tap', 'node', (evt) => showDetails(evt.target));

  async function runOnce() {
    const task = document.getElementById("task").value;
    statusEl.textContent = "Calling Gemini (1 request)…";

    const res = await fetch("/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task })
    });

    const data = await res.json();
    if (!res.ok) {
      statusEl.textContent = "Error: " + (data.error || "unknown");
      return;
    }

    statusEl.textContent = "Done ✓ (no auto-calls)";
    buildGraph(data.plan);
    detailsEl.innerHTML = `<p class="muted">Click a node to see details.</p>`;
  }

  document.getElementById("run").addEventListener("click", runOnce);
</script>
</body>
</html>
"""

@app.post("/plan")
def plan():
    payload = request.get_json(force=True) or {}
    task = payload.get("task", "").strip()
    if not task:
        return {"error": "task is required"}, 400

    try:
        plan = generate_plan(task, retries=3)  # one run = one call chain (with retries only if needed)
        return {"plan": plan}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)