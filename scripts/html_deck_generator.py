"""
Standalone HTML/CSS to PDF Presentation Generator for Wiz Health Assessment.
=============================================================================
Generates executive-ready, 16:9 landscape presentations in PDF and HTML format
with zero Google Cloud / OAuth dependencies.

Works out-of-the-box on Linux, macOS, and Windows.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def find_headless_browser() -> Optional[str]:
    """Finds available Chrome, Chromium, Edge, or Brave binary on Linux, macOS, or Windows."""
    # 1. Custom override
    if os.environ.get("BROWSER_PATH") and os.path.exists(os.environ["BROWSER_PATH"]):
        return os.environ["BROWSER_PATH"]

    # 2. Check PATH
    for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge", "chrome", "brave"]:
        p = shutil.which(name)
        if p:
            return p

    # 3. Known absolute OS locations
    candidates = [
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/msedge",
        "/snap/bin/chromium",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        # Windows
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    for c in candidates:
        if c and os.path.exists(c):
            return c

    return None


def generate_html_presentation(
    variables: Dict[str, Any],
    output_html_path: str,
    customer_name: str = "Customer",
    today_str: str = ""
) -> str:
    """Generates a branded, responsive 16:9 executive presentation in HTML format."""
    Path(output_html_path).parent.mkdir(parents=True, exist_ok=True)

    # Flatten variable values
    v = {}
    for k, val in variables.items():
        if isinstance(val, dict) and "value" in val:
            v[k] = str(val["value"] if val["value"] is not None else "")
        else:
            v[k] = str(val if val is not None else "")

    customer = customer_name or v.get("CUSTOMER") or "Cloud Security Customer"
    date = today_str or v.get("DATE") or "2026-08-24"
    score = v.get("SS") or "92"
    trend = v.get("s1d") or "+0%"
    benchmark = v.get("SP") or "75%"
    gap = v.get("SG") or "+17%"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Wiz Tenant Health Assessment - {customer}</title>
<style>
  @page {{
    size: 16in 9in;
    margin: 0;
  }}
  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #0B192C;
    color: #F8FAFC;
  }}
  .slide {{
    width: 16in;
    height: 9in;
    page-break-after: always;
    display: flex;
    flex-direction: column;
    padding: 0.8in 1in;
    background: #0B192C;
    position: relative;
    overflow: hidden;
  }}
  .slide::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    background: linear-gradient(90deg, #00C9FF 0%, #1A56DB 50%, #10B981 100%);
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 0.4in;
    border-bottom: 1px solid #1E3E62;
    padding-bottom: 0.2in;
  }}
  .title-area h2 {{
    font-size: 32px;
    font-weight: 700;
    margin: 0 0 6px 0;
    color: #FFFFFF;
    letter-spacing: -0.5px;
  }}
  .title-area .subtitle {{
    font-size: 16px;
    color: #94A3B8;
    margin: 0;
  }}
  .badge {{
    background: #1E3E62;
    color: #38BDF8;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.3in;
    flex: 1;
  }}
  .grid-3 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.25in;
    flex: 1;
  }}
  .grid-4 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 0.2in;
    flex: 1;
  }}
  .card {{
    background: #112240;
    border: 1px solid #1E3E62;
    border-radius: 12px;
    padding: 0.25in 0.3in;
    display: flex;
    flex-direction: column;
  }}
  .card-header {{
    font-size: 16px;
    font-weight: 600;
    color: #94A3B8;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .card-value {{
    font-size: 40px;
    font-weight: 800;
    color: #FFFFFF;
    margin-bottom: 8px;
    letter-spacing: -1px;
  }}
  .stat-row {{
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #1E3E62;
    font-size: 15px;
  }}
  .stat-row:last-child {{
    border-bottom: none;
  }}
  .stat-label {{
    color: #94A3B8;
  }}
  .stat-val {{
    font-weight: 600;
    color: #F8FAFC;
  }}
  .val-highlight {{
    color: #10B981;
    font-weight: 700;
  }}
  .val-warning {{
    color: #F59E0B;
    font-weight: 700;
  }}
  .val-danger {{
    color: #EF4444;
    font-weight: 700;
  }}
  .footer {{
    margin-top: auto;
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: #64748B;
    padding-top: 0.2in;
  }}
  .title-slide {{
    justify-content: center;
    align-items: flex-start;
    padding-left: 1.5in;
    background: radial-gradient(circle at 80% 20%, #1E3E62 0%, #0B192C 70%);
  }}
  .title-slide h1 {{
    font-size: 56px;
    font-weight: 800;
    margin: 0 0 16px 0;
    color: #FFFFFF;
    letter-spacing: -1.5px;
    line-height: 1.1;
  }}
  .title-slide h1 span {{
    background: linear-gradient(90deg, #00C9FF, #38BDF8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .title-slide .desc {{
    font-size: 24px;
    color: #94A3B8;
    margin-bottom: 40px;
  }}
  .meta-box {{
    display: flex;
    gap: 40px;
    border-top: 2px solid #1E3E62;
    padding-top: 24px;
  }}
  .meta-item .meta-label {{
    font-size: 13px;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }}
  .meta-item .meta-val {{
    font-size: 18px;
    font-weight: 600;
    color: #F8FAFC;
  }}
  .score-circle {{
    width: 120px;
    height: 120px;
    border-radius: 50%;
    border: 8px solid #10B981;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    margin: 10px auto;
  }}
  .score-circle .num {{
    font-size: 36px;
    font-weight: 800;
    color: #FFFFFF;
  }}
  .score-circle .sub {{
    font-size: 11px;
    color: #10B981;
    font-weight: 700;
  }}
  .preview-pill {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 13px;
    margin: 3px;
    font-weight: 500;
  }}
  .preview-pill.enabled {{
    background: #064E3B;
    color: #6EE7B7;
    border: 1px solid #059669;
  }}
  .preview-pill.disabled {{
    background: #1E293B;
    color: #94A3B8;
    border: 1px solid #334155;
  }}
</style>
</head>
<body>

  <!-- SLIDE 1: Title Slide -->
  <div class="slide title-slide">
    <div class="badge" style="margin-bottom: 20px;">Wiz Cloud Security</div>
    <h1>Tenant Health & Posture<br><span>Executive Assessment</span></h1>
    <div class="desc">Comprehensive review of cloud coverage, security scores, and scanning fidelity</div>
    <div class="meta-box">
      <div class="meta-item">
        <div class="meta-label">Customer Tenant</div>
        <div class="meta-val">{customer}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Assessment Date</div>
        <div class="meta-val">{date}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Architecture Platform</div>
        <div class="meta-val">Wiz Cloud Security Graph</div>
      </div>
    </div>
  </div>

  <!-- SLIDE 2: Cloud Footprint & AI Footprint -->
  <div class="slide">
    <div class="header">
      <div class="title-area">
        <h2>Cloud Architecture & AI-SPM Footprint</h2>
        <div class="subtitle">Discovered cloud accounts, connectors, and AI entities across your multi-cloud environment</div>
      </div>
      <div class="badge">Asset Inventory</div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <span>Connected Cloud Environments</span>
          <span class="badge" style="background:#0F172A;">{v.get("CON_TOT", "0")} Connectors</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">AWS Accounts</span>
          <span class="stat-val">{v.get("C_AWS", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Azure Subscriptions</span>
          <span class="stat-val">{v.get("C_AZ", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">GCP Projects</span>
          <span class="stat-val">{v.get("C_GCP", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Other Clouds ({v.get("C_OTH_NAMES", "None") or "None"})</span>
          <span class="stat-val">{v.get("C_OTH", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Kubernetes Connectors</span>
          <span class="stat-val">{v.get("CON_K8S", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Container Registries</span>
          <span class="stat-val">{v.get("R_TOT", "0")}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span>AI-SPM & AI Inventory Footprint</span>
          <span class="badge" style="background:#064E3B; color:#6EE7B7;">AI Security Active</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">AI Models Discovered</span>
          <span class="stat-val val-highlight">{v.get("AI_MODELS_COUNT", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">AI Pipelines</span>
          <span class="stat-val">{v.get("AI_PIPELINES_COUNT", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">AI Agents & Assistants</span>
          <span class="stat-val">{v.get("AI_AGENTS_COUNT", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">MCP Servers Discovered</span>
          <span class="stat-val">{v.get("AI_MCP_SERVERS_COUNT", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">AI Code Repositories</span>
          <span class="stat-val">{v.get("AI_CODE_REPOS_COUNT", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">AI Technologies & Frameworks</span>
          <span class="stat-val">{v.get("AI_TECHNOLOGIES_COUNT", "0")}</span>
        </div>
      </div>
    </div>
    <div class="footer">
      <span>Wiz Tenant Health Assessment</span>
      <span>Slide 2 of 6</span>
    </div>
  </div>

  <!-- SLIDE 3: 7-Pillar Scanning Fidelity -->
  <div class="slide">
    <div class="header">
      <div class="title-area">
        <h2>7-Pillar Scanning Fidelity & Workload Coverage</h2>
        <div class="subtitle">Deep scanning coverage across Disks, Container Images, VM Images, and DSPM Data</div>
      </div>
      <div class="badge">Scanning Coverage</div>
    </div>
    <div class="grid-4">
      <div class="card">
        <div class="card-header"><span>DSPM Data Scans</span></div>
        <div class="card-value val-highlight">{v.get("DS_P", "0%")}</div>
        <div class="stat-row"><span class="stat-label">Total Scans</span><span class="stat-val">{v.get("DS_T", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Failed</span><span class="stat-val val-danger">{v.get("DS_F", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Skipped</span><span class="stat-val">{v.get("DS_SK", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">PaaS DBs</span><span class="stat-val">{v.get("DS_PD", "0")}</span></div>
      </div>

      <div class="card">
        <div class="card-header"><span>Non-OS Disk Scans</span></div>
        <div class="card-value { "val-warning" if int(v.get("NON_C", "0%").rstrip("%") or 0) < 50 else "val-highlight" }">{v.get("NON_C", "0%")}</div>
        <div class="stat-row"><span class="stat-label">Total Evaluated</span><span class="stat-val">{v.get("NON_T", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Failed</span><span class="stat-val val-danger">{v.get("NON_F", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Skipped</span><span class="stat-val">{v.get("NON_S", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Coverage Status</span><span class="stat-val">Active</span></div>
      </div>

      <div class="card">
        <div class="card-header"><span>Container Images</span></div>
        <div class="card-value { "val-warning" if int(v.get("RCI_C", "0%").rstrip("%") or 0) < 50 else "val-highlight" }">{v.get("RCI_C", "0%")}</div>
        <div class="stat-row"><span class="stat-label">Total Scans</span><span class="stat-val">{v.get("RCI_T", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Failed</span><span class="stat-val val-danger">{v.get("RCI_F", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Skipped</span><span class="stat-val">{v.get("RCI_S", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Registries</span><span class="stat-val">{v.get("R_TOT", "0")}</span></div>
      </div>

      <div class="card">
        <div class="card-header"><span>VM Image Scans</span></div>
        <div class="card-value { "val-warning" if int(v.get("VMI_C", "0%").rstrip("%") or 0) < 50 else "val-highlight" }">{v.get("VMI_C", "0%")}</div>
        <div class="stat-row"><span class="stat-label">Total Scans</span><span class="stat-val">{v.get("VMI_T", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Failed</span><span class="stat-val val-danger">{v.get("VMI_F", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Skipped</span><span class="stat-val">{v.get("VMI_S", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Coverage Status</span><span class="stat-val">Standard</span></div>
      </div>
    </div>
    <div class="footer">
      <span>Wiz Tenant Health Assessment</span>
      <span>Slide 3 of 6</span>
    </div>
  </div>

  <!-- SLIDE 4: Security Posture & Score -->
  <div class="slide">
    <div class="header">
      <div class="title-area">
        <h2>Security Posture & Industry Benchmark</h2>
        <div class="subtitle">Executive security score, issue resolution velocity, and threat detection fidelity</div>
      </div>
      <div class="badge">Executive Scorecard</div>
    </div>
    <div class="grid-3">
      <div class="card" style="text-align: center;">
        <div class="card-header"><span>Wiz Security Score</span></div>
        <div class="score-circle">
          <div class="num">{score}</div>
          <div class="sub">OUT OF 100</div>
        </div>
        <div class="stat-row"><span class="stat-label">90-Day Trend</span><span class="stat-val val-highlight">{trend}</span></div>
        <div class="stat-row"><span class="stat-label">50th % Benchmark</span><span class="stat-val">{benchmark}</span></div>
        <div class="stat-row"><span class="stat-label">Benchmark Gap</span><span class="stat-val val-highlight">{gap}</span></div>
      </div>

      <div class="card">
        <div class="card-header"><span>Issue Hygiene & Velocity</span></div>
        <div class="stat-row"><span class="stat-label">Open Critical Issues</span><span class="stat-val { "val-highlight" if v.get("OC") == "0" else "val-danger" }">{v.get("OC", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Resolved Critical (90d)</span><span class="stat-val val-highlight">{v.get("RC", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Open High Issues</span><span class="stat-val val-warning">{v.get("OH", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Resolved High (90d)</span><span class="stat-val">{v.get("RH", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Avg Critical Age</span><span class="stat-val">{v.get("AVG_AGEC", "0")} days</span></div>
        <div class="stat-row"><span class="stat-label">Avg High Age</span><span class="stat-val">{v.get("AVG_AGEH", "0")} days</span></div>
      </div>

      <div class="card">
        <div class="card-header"><span>AI Security Posture</span></div>
        <div class="stat-row"><span class="stat-label">AI Security Findings</span><span class="stat-val val-highlight">{v.get("AI_SF", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">AI Configuration Findings</span><span class="stat-val val-warning">{v.get("AI_MF", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">AI Inventory Findings</span><span class="stat-val">{v.get("AI_IF", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Open Threats (CDR)</span><span class="stat-val val-highlight">{v.get("OT", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Resolved Threats (90d)</span><span class="stat-val">{v.get("RT", "0")}</span></div>
      </div>
    </div>
    <div class="footer">
      <span>Wiz Tenant Health Assessment</span>
      <span>Slide 4 of 6</span>
    </div>
  </div>

  <!-- SLIDE 5: Kubernetes Maturity Ladder -->
  <div class="slide">
    <div class="header">
      <div class="title-area">
        <h2>Kubernetes Posture & Coverage Ladder</h2>
        <div class="subtitle">Evaluation of Kubernetes clusters against the canonical 4-tier security ladder</div>
      </div>
      <div class="badge">Kubernetes Security</div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header"><span>Cluster Coverage Overview</span></div>
        <div class="stat-row"><span class="stat-label">Total Kubernetes Clusters</span><span class="stat-val">{v.get("K8S", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Clusters with Wiz Connector</span><span class="stat-val val-highlight">{v.get("KC_WC", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Clusters with Audit Log Collector</span><span class="stat-val">{v.get("KC_SE", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Clusters with Runtime Sensor</span><span class="stat-val">{v.get("KC_CLI", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Clusters with Admission Controller</span><span class="stat-val">{v.get("KC_AC", "0")}</span></div>
      </div>

      <div class="card">
        <div class="card-header"><span>Identified Coverage Gaps</span></div>
        <div class="stat-row"><span class="stat-label">Clusters Missing Connector</span><span class="stat-val { "val-danger" if int(v.get("KG_NC", 0) or 0) > 0 else "val-highlight" }">{v.get("KG_NC", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Missing Audit Log Ingestion</span><span class="stat-val { "val-warning" if int(v.get("KG_NA", 0) or 0) > 0 else "val-highlight" }">{v.get("KG_NA", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Missing Runtime Sensor (DaemonSet)</span><span class="stat-val { "val-warning" if int(v.get("KG_NS", 0) or 0) > 0 else "val-highlight" }">{v.get("KG_NS", "0")}</span></div>
        <div class="stat-row"><span class="stat-label">Publicly Accessible Clusters</span><span class="stat-val">{v.get("KG_IA", "0")}</span></div>
      </div>
    </div>
    <div class="footer">
      <span>Wiz Tenant Health Assessment</span>
      <span>Slide 5 of 6</span>
    </div>
  </div>

  <!-- SLIDE 6: Top Risks & Recommendations -->
  <div class="slide">
    <div class="header">
      <div class="title-area">
        <h2>Top Security Controls & Priority Actions</h2>
        <div class="subtitle">Highest-impact controls by finding volume and prioritized tactical next steps</div>
      </div>
      <div class="badge">Action Plan</div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header"><span>Top High-Risk Controls by Count</span></div>
        <div class="stat-row">
          <span class="stat-label">{v.get("HI_CONTROL_1", "Publicly accessible PaaS DB w/ sensitive data")[:45]}...</span>
          <span class="stat-val val-danger">{v.get("HI_CBC_1", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">{v.get("HI_CONTROL_2", "Publicly exposed serverless function")[:45]}...</span>
          <span class="stat-val val-danger">{v.get("HI_CBC_2", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">{v.get("HI_CONTROL_3", "Messaging service writing to unknown bucket")[:45]}...</span>
          <span class="stat-val val-danger">{v.get("HI_CBC_3", "0")}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Attack Surface Workload Units (ASM)</span>
          <span class="stat-val">{v.get("AE_TOT", "0")}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header"><span>Prioritized Tactical Next Steps</span></div>
        <div class="stat-row">
          <span class="stat-label">1. Close Non-OS Disk & Image Scan Gaps</span>
          <span class="stat-val val-highlight">Target: &gt;95%</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">2. Deploy K8s Runtime Sensor on missing clusters</span>
          <span class="stat-val val-highlight">{v.get("KG_NS", "0")} clusters</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">3. Remediate stale High-severity issue backlog</span>
          <span class="stat-val val-warning">Avg {v.get("AVG_AGEH", "0")} days</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">4. Enable Wiz Admission Controller in enforce mode</span>
          <span class="stat-val">DevSecOps</span>
        </div>
      </div>
    </div>
    <div class="footer">
      <span>Wiz Tenant Health Assessment</span>
      <span>Slide 6 of 6</span>
    </div>
  </div>

</body>
</html>
"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_html_path


def render_html_to_pdf(html_path: str, output_pdf_path: str) -> bool:
    """Renders HTML presentation to PDF using headless Chrome/Chromium/Edge."""
    browser_bin = find_headless_browser()
    if not browser_bin:
        return False

    Path(output_pdf_path).parent.mkdir(parents=True, exist_ok=True)
    abs_html_path = os.path.abspath(html_path)

    cmd = [
        browser_bin,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf_path}",
        f"file://{abs_html_path}"
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 1000
    except Exception as e:
        print(f"    [!] Headless browser PDF render error: {e}")
        return False
