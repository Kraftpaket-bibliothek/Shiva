from __future__ import annotations

import json
from pathlib import Path
import sys
import threading
from typing import Any, Callable, Dict
import webbrowser
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.textProcessor import DataInput, buildDefaultRecipe
from src.logicEngine import LogicEngine


# ======================================================================
# SECTION 1: EMBEDDED SLEEK HTML & OPEN SANS STYLING
# ======================================================================

def buildHtmlTemplate() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Yukti // Neuro-Symbolic Verification Engine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111724;
      --card-border: #1e293b;
      --input-bg: #0c101a;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --success: #10b981;
      --danger: #ef4444;
      --mono: 'JetBrains Mono', monospace;
      --sans: 'Open Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text-main);
      font-family: var(--sans);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px 16px;
      -webkit-font-smoothing: antialiased;
    }
    .container { width: 100%; max-width: 1080px; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 28px;
    }
    .brand h1 { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }
    .brand p { font-size: 13px; color: var(--text-muted); font-weight: 400; margin-top: 2px; }
    .badge {
      font-family: var(--mono);
      font-size: 11px;
      padding: 4px 10px;
      border-radius: 4px;
      background: #1e293b;
      color: #38bdf8;
      border: 1px solid #334155;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .presets-bar {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      align-items: center;
    }
    .presets-label { font-size: 12px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; }
    .preset-btn {
      background: transparent;
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-family: var(--sans);
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .preset-btn:hover { background: #1e293b; color: var(--text-main); border-color: #334155; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 20px;
      display: flex;
      flex-direction: column;
    }
    .card-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
    }
    .card-title span { font-size: 11px; color: var(--text-dim); font-weight: 400; text-transform: none; }
    textarea, input[type="text"] {
      width: 100%;
      background: var(--input-bg);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      color: var(--text-main);
      font-family: var(--mono);
      font-size: 13px;
      line-height: 1.6;
      padding: 12px;
      resize: vertical;
      outline: none;
      transition: border-color 0.15s;
    }
    textarea:focus, input[type="text"]:focus { border-color: var(--accent); }
    textarea { height: 180px; }
    .target-card { margin-bottom: 24px; }
    .target-card input { height: 42px; font-size: 13px; }
    .actions { display: flex; justify-content: flex-end; margin-bottom: 32px; }
    .submit-btn {
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 12px 28px;
      border-radius: 6px;
      font-family: var(--sans);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: background 0.15s;
    }
    .submit-btn:hover { background: var(--accent-hover); }
    .submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
    .results-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 24px;
      display: none;
    }
    .status-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-radius: 6px;
      margin-bottom: 24px;
    }
    .status-banner.accepted { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); }
    .status-banner.rejected { background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.3); }
    .status-badge-lg { font-size: 16px; font-weight: 700; letter-spacing: 0.05em; display: flex; align-items: center; gap: 10px; }
    .accepted .status-badge-lg { color: var(--success); }
    .rejected .status-badge-lg { color: var(--danger); }
    .metrics { font-family: var(--mono); font-size: 12px; color: var(--text-muted); }
    .violation-group { margin-bottom: 20px; }
    .section-heading {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
    }
    .rule-item {
      background: var(--input-bg);
      border-left: 3px solid;
      padding: 12px 16px;
      border-radius: 0 6px 6px 0;
      margin-bottom: 8px;
      font-size: 13px;
    }
    .rule-item.fail { border-color: var(--danger); }
    .rule-item.pass { border-color: var(--success); }
    .rule-id { font-family: var(--mono); font-weight: 600; font-size: 12px; margin-bottom: 2px; }
    .rule-text { color: var(--text-main); }
    .model-box {
      background: var(--input-bg);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 14px;
      font-family: var(--mono);
      font-size: 12px;
      color: #38bdf8;
      overflow-x: auto;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <h1>YUKTI // Neuro-Symbolic Engine</h1>
        <p>Zero-hallucination policy adjudication via pure NumPy DPLL(T) SMT</p>
      </div>
      <div class="badge">DPLL(T) SMT Engine</div>
    </header>

    <div class="presets-bar">
      <span class="presets-label">Quick Presets:</span>
      <button class="preset-btn" onclick="loadPreset('finance')">Finance Mortgage</button>
      <button class="preset-btn" onclick="loadPreset('aerospace')">Aerospace Pre-Flight</button>
      <button class="preset-btn" onclick="loadPreset('healthcare')">Healthcare Triage</button>
    </div>

    <div class="grid">
      <div class="card">
        <div class="card-title">
          1. Policy Rules
          <span>One rule constraint per line</span>
        </div>
        <textarea id="rulesInput" placeholder="Credit score needs to be at least 680.&#10;Debt to income ratio should stay under 43%.&#10;Tax return years must be at least 2 when self employed is true."></textarea>
      </div>
      <div class="card">
        <div class="card-title">
          2. Case Facts
          <span>Key: Value pairs (one per line)</span>
        </div>
        <textarea id="factsInput" placeholder="Credit score: 640&#10;Debt to income ratio: 36%&#10;Self employed: true&#10;Tax return years: 1"></textarea>
      </div>
    </div>

    <div class="card target-card">
      <div class="card-title">
        3. Required Outcome / Target
        <span>Target goal variable or 'ALL_RULES'</span>
      </div>
      <input type="text" id="targetInput" value="ALL_RULES" />
    </div>

    <div class="actions">
      <button class="submit-btn" id="runBtn" onclick="runAdjudication()">
        <span>Run Formal Verification</span>
      </button>
    </div>

    <div class="results-card" id="resultsBox">
      <div class="status-banner" id="statusBanner">
        <div class="status-badge-lg" id="statusBadge">VERDICT</div>
        <div class="metrics" id="metricsDisplay">Solving time: --</div>
      </div>
      <div class="violation-group" id="violationsGroup">
        <div class="section-heading">Violated Policy Rules (UNSAT Core)</div>
        <div id="violationsList"></div>
      </div>
      <div class="violation-group" id="satisfiedGroup">
        <div class="section-heading">Entailed / Satisfied Constraints</div>
        <div id="satisfiedList"></div>
      </div>
      <div class="violation-group" id="modelGroup" style="display:none;">
        <div class="section-heading">Certified Model Assignment</div>
        <div class="model-box" id="modelDisplay"></div>
      </div>
    </div>
  </div>

  <script>
    async function loadPreset(domain) {
      const res = await fetch('/api/demo/' + domain);
      const data = await res.json();
      document.getElementById('rulesInput').value = data.rules.join('\\n');
      document.getElementById('factsInput').value = data.facts.join('\\n');
      document.getElementById('targetInput').value = data.target;
    }

    async function runAdjudication() {
      const runBtn = document.getElementById('runBtn');
      const resultsBox = document.getElementById('resultsBox');
      const rules = document.getElementById('rulesInput').value.split('\\n').map(s => s.trim()).filter(Boolean);
      const facts = document.getElementById('factsInput').value.split('\\n').map(s => s.trim()).filter(Boolean);
      const target = document.getElementById('targetInput').value.trim() || 'ALL_RULES';

      runBtn.disabled = true;
      runBtn.innerText = 'Solving via SMT...';

      const startTime = performance.now();
      try {
        const res = await fetch('/api/adjudicate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ Rules: rules, Facts: facts, RequiredOutcome: [target] })
        });
        const data = await res.json();
        const duration = (performance.now() - startTime).toFixed(1);
        renderDecision(data, duration);
      } catch (err) {
        alert('Adjudication error: ' + err.message);
      } finally {
        runBtn.disabled = false;
        runBtn.innerText = 'Run Formal Verification';
      }
    }

    function renderDecision(data, duration) {
      const resultsBox = document.getElementById('resultsBox');
      const banner = document.getElementById('statusBanner');
      const badge = document.getElementById('statusBadge');
      const metrics = document.getElementById('metricsDisplay');
      const vList = document.getElementById('violationsList');
      const sList = document.getElementById('satisfiedList');
      const modelGroup = document.getElementById('modelGroup');
      const modelDisplay = document.getElementById('modelDisplay');

      resultsBox.style.display = 'block';
      const isAccepted = data.status === 'ACCEPTED';
      banner.className = 'status-banner ' + (isAccepted ? 'accepted' : 'rejected');
      badge.innerText = isAccepted ? 'VERDICT: ACCEPTED (MATHEMATICALLY ENTAILED)' : 'VERDICT: REJECTED (REFUTATION PROVED)';
      metrics.innerText = 'Time: ' + duration + ' ms | Clauses: ' + (data.details.numClauses || 0) + ' | Vars: ' + (data.details.numVariables || 0);

      vList.innerHTML = '';
      if (!isAccepted && data.violatedRules && data.violatedRules.length > 0) {
        document.getElementById('violationsGroup').style.display = 'block';
        data.violatedRules.forEach(r => {
          vList.innerHTML += '<div class="rule-item fail"><div class="rule-id" style="color:var(--danger)">[VIOLATION] ' + r.ruleId + '</div><div class="rule-text">' + r.rawText + '</div></div>';
        });
      } else {
        document.getElementById('violationsGroup').style.display = 'none';
      }

      sList.innerHTML = '';
      if (data.satisfiedRules && data.satisfiedRules.length > 0) {
        document.getElementById('satisfiedGroup').style.display = 'block';
        data.satisfiedRules.forEach(r => {
          sList.innerHTML += '<div class="rule-item pass"><div class="rule-id" style="color:var(--success)">[ENTAILED] ' + r.ruleId + '</div><div class="rule-text">' + r.rawText + '</div></div>';
        });
      } else {
        document.getElementById('satisfiedGroup').style.display = 'none';
      }

      if (isAccepted && Object.keys(data.certifiedModel).length > 0) {
        modelGroup.style.display = 'block';
        modelDisplay.innerText = JSON.stringify(data.certifiedModel, null, 2);
      } else {
        modelGroup.style.display = 'none';
      }
      resultsBox.scrollIntoView({ behavior: 'smooth' });
    }
  </script>
</body>
</html>"""


# ======================================================================
# SECTION 2: DOMAIN PRESETS & DEMO CATALOG
# ======================================================================

def buildFinancePreset() -> Dict[str, Any]:
    return {
        "rules": [
            "Credit score needs to be at least 680.",
            "Debt to income ratio should stay under 43%.",
            "Tax return years must be at least 2 when self employed is true.",
        ],
        "facts": [
            "Credit score: 640",
            "Debt to income ratio: 36%",
            "Self employed: true",
            "Tax return years: 1",
        ],
        "target": "ALL_RULES",
    }


def buildAerospacePreset() -> Dict[str, Any]:
    return {
        "rules": [
            "Hydraulic pressure must be at least 3000.",
            "Cabin altitude must stay under 8000.",
            "Deicing active must be equal to true when ambient temp is under 0.",
        ],
        "facts": [
            "Hydraulic pressure: 3150",
            "Cabin altitude: 6200",
            "Ambient temp: -4",
            "Deicing active: true",
        ],
        "target": "ALL_RULES",
    }


def buildHealthcarePreset() -> Dict[str, Any]:
    return {
        "rules": [
            "Systolic blood pressure must stay under 140.",
            "Oxygen saturation needs to be at least 95.",
            "Emergency referral must be equal to true when heart rate exceeds 120.",
        ],
        "facts": [
            "Systolic blood pressure: 128",
            "Oxygen saturation: 97",
            "Heart rate: 135",
            "Emergency referral: false",
        ],
        "target": "ALL_RULES",
    }


def getPresetByDomain(domain: str) -> Dict[str, Any]:
    dispatchTable: Dict[str, Callable[[], Dict[str, Any]]] = {
        "finance": buildFinancePreset,
        "aerospace": buildAerospacePreset,
        "healthcare": buildHealthcarePreset,
    }
    loader = dispatchTable.get(domain.lower(), buildFinancePreset)
    return loader()


# ======================================================================
# SECTION 3: PIPELINE EXECUTION & ADJUDICATION DISPATCHER
# ======================================================================

def adjudicatePayload(inputData: DataInput) -> Dict[str, Any]:
    processor = buildDefaultRecipe()
    engine = LogicEngine()
    jsonPayload = processor.executePipeline(inputData)
    parsedOutput = json.loads(jsonPayload)
    decision = engine.solvePolicy(jsonPayload)
    parsedRules = parsedOutput.get("rules", [])
    violated = [r for r in parsedRules if r["ruleId"] in decision.unsatCore]
    satisfied = [r for r in parsedRules if r["ruleId"] not in decision.unsatCore]
    return {
        "status": decision.status,
        "unsatCore": decision.unsatCore,
        "violatedRules": violated,
        "satisfiedRules": satisfied,
        "certifiedModel": decision.certifiedModel,
        "details": decision.details,
    }


# ======================================================================
# SECTION 4: FASTAPI APPLICATION & ROUTE DEFINITIONS
# ======================================================================

def createFastApiApp() -> FastAPI:
    app = FastAPI(title="Yukti Neuro-Symbolic Decision Engine")

    @app.get("/", response_class=HTMLResponse)
    def serveHtmlIndex() -> str:
        return buildHtmlTemplate()

    @app.get("/api/demo/{domain}")
    def getDemoEndpoint(domain: str) -> Dict[str, Any]:
        return getPresetByDomain(domain)

    @app.post("/api/adjudicate")
    def adjudicateEndpoint(inputData: DataInput) -> Dict[str, Any]:
        return adjudicatePayload(inputData)

    return app


# ======================================================================
# SECTION 5: BROWSER AUTO-LAUNCH & SERVER RUNNER
# ======================================================================

def openDefaultBrowser(host: str, port: int) -> None:
    targetUrl = f"http://{host}:{port}"
    webbrowser.open(targetUrl)


def startWebServer(host: str = "127.0.0.1", port: int = 8000) -> None:
    threading.Timer(1.2, lambda: openDefaultBrowser(host, port)).start()
    app = createFastApiApp()
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    startWebServer()
