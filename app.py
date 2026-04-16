from __future__ import annotations

import json
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.news_app.workflow import RunInput, run_workflow

HTML = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>News Discovery MVP</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    .row { display: flex; gap: 12px; margin-bottom: 12px; }
    .panel { border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-top: 12px; }
    label { display: block; font-weight: 600; margin-bottom: 4px; }
    input { padding: 6px; width: 100%; }
    button { padding: 8px 14px; cursor: pointer; }
    pre { white-space: pre-wrap; max-height: 320px; overflow: auto; background: #f9f9f9; padding: 10px; }
    #timeline { width: 100%; height: 220px; border: 1px solid #eee; }
    .error { color: #a00; }
  </style>
</head>
<body>
  <h1>News Discovery MVP (Vertical Slice)</h1>
  <p>UI intake → real ingestion → normalization → daily timeline.</p>

  <div class=\"row\">
    <div style=\"flex:2\">
      <label for=\"topic\">Topic</label>
      <input id=\"topic\" placeholder=\"e.g., semiconductor\" />
    </div>
    <div style=\"flex:1\">
      <label for=\"start\">Start date</label>
      <input id=\"start\" type=\"date\" />
    </div>
    <div style=\"flex:1\">
      <label for=\"end\">End date</label>
      <input id=\"end\" type=\"date\" />
    </div>
  </div>

  <button id=\"runBtn\">Run Workflow</button>
  <p id=\"status\"></p>

  <div class=\"panel\">
    <h3>Run Metadata</h3>
    <pre id=\"meta\"></pre>
  </div>

  <div class=\"panel\">
    <h3>Step 1: Ingestion Validation</h3>
    <pre id=\"ingestion\"></pre>
  </div>

  <div class=\"panel\">
    <h3>Step 2: Normalization Validation</h3>
    <pre id=\"normalization\"></pre>
  </div>

  <div class=\"panel\">
    <h3>Step 3: Aggregation + Timeline Validation</h3>
    <svg id=\"timeline\"></svg>
    <pre id=\"aggregation\"></pre>
  </div>

<script>
const today = new Date();
const prior = new Date(today.getTime() - 7*24*60*60*1000);
document.getElementById('start').valueAsDate = prior;
document.getElementById('end').valueAsDate = today;

function drawTimeline(points) {
  const svg = document.getElementById('timeline');
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  if (!points || points.length === 0) return;

  const width = svg.clientWidth || 800;
  const height = svg.clientHeight || 220;
  const pad = 30;
  const maxY = Math.max(...points.map(p => p.article_count), 1);

  const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
  line.setAttribute('fill', 'none');
  line.setAttribute('stroke', '#1f77b4');
  line.setAttribute('stroke-width', '2');

  const coords = points.map((p, i) => {
    const x = pad + (i * (width - 2*pad) / Math.max(points.length - 1, 1));
    const y = height - pad - ((p.article_count / maxY) * (height - 2*pad));
    return `${x},${y}`;
  }).join(' ');

  line.setAttribute('points', coords);
  svg.appendChild(line);

  points.forEach((p, i) => {
    const x = pad + (i * (width - 2*pad) / Math.max(points.length - 1, 1));
    const y = height - pad - ((p.article_count / maxY) * (height - 2*pad));

    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('cx', x); dot.setAttribute('cy', y); dot.setAttribute('r', 3); dot.setAttribute('fill', '#1f77b4');
    svg.appendChild(dot);
  });
}

document.getElementById('runBtn').addEventListener('click', async () => {
  const topic = document.getElementById('topic').value.trim();
  const start_date = document.getElementById('start').value;
  const end_date = document.getElementById('end').value;

  const status = document.getElementById('status');
  status.className = '';

  if (!topic) {
    status.textContent = 'Topic is required.';
    status.className = 'error';
    return;
  }

  status.textContent = 'Running...';

  const res = await fetch('/run', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({topic, start_date, end_date})
  });

  const data = await res.json();

  if (!res.ok) {
    status.textContent = data.error || 'Workflow failed.';
    status.className = 'error';
    return;
  }

  status.textContent = `Completed: ${data.run_id}`;
  document.getElementById('meta').textContent = JSON.stringify({run_id: data.run_id, started_at: data.started_at, input: data.input}, null, 2);
  document.getElementById('ingestion').textContent = JSON.stringify(data.stages.ingestion, null, 2);
  document.getElementById('normalization').textContent = JSON.stringify(data.stages.normalization, null, 2);
  document.getElementById('aggregation').textContent = JSON.stringify(data.stages.aggregation, null, 2);
  drawTimeline(data.stages.aggregation.daily_counts);
});
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/":
            self.send_error(404)
            return

        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/run":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))

        try:
            topic = str(payload.get("topic", "")).strip()
            start_date = date.fromisoformat(payload["start_date"])
            end_date = date.fromisoformat(payload["end_date"])
        except Exception:
            self._send_json(400, {"error": "Invalid request payload."})
            return

        if not topic:
            self._send_json(400, {"error": "Topic is required."})
            return
        if start_date > end_date:
            self._send_json(400, {"error": "Start date must be on or before end date."})
            return
        if (end_date - start_date).days > 30:
            self._send_json(400, {"error": "Date range must be 30 days or less."})
            return
        if end_date > datetime.utcnow().date():
            self._send_json(400, {"error": "End date cannot be in the future."})
            return

        try:
            result = run_workflow(RunInput(topic=topic, start_date=start_date, end_date=end_date))
            self._send_json(200, result)
        except Exception as exc:
            self._send_json(500, {"error": f"Workflow execution failed: {exc}"})


def main() -> None:
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("News Discovery MVP running at http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
