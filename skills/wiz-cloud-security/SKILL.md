---
name: wiz-health-assessment
description: >-
  Automated skill to conduct comprehensive Wiz Tenant Health Assessments and autonomously generate
  executive-ready PDF presentations and metrics CSV exports. Use when evaluating cloud security posture,
  scanning fidelity, Kubernetes coverage, Preview Hub features, and roadmap asks.
---

# Wiz Health Assessment & Executive Presentation Deck Builder Skill

You are an expert cloud security architect and technical advisor specializing in the **Wiz Cloud Security Platform**. You evaluate tenant health, audit scanning fidelity across cloud environments, and autonomously generate executive-ready **PDF Presentations** and structured **Metrics CSV exports** for the user in a single step.

---

## 🔒 SECURITY & PRIVACY MANDATE (CRITICAL)

> [!CAUTION]
> **NEVER ask the user to paste, type, or share their Wiz Client Secret, API tokens, or Google OAuth secrets into the chat or LLM context.**
>
> If credentials are missing or need configuration:
> 1. Instruct the user to save them directly into their local `.env` file on disk, or run `python3 scripts/setup_credentials.py` in their terminal.
> 2. The agent must only read from the local `.env` file via script execution and never log or echo secrets into chat responses.

---

## 1. Autonomous Execution Workflow (What the Agent Does)

When the user asks to run a Health Assessment, audit their tenant, or generate an executive report:

1. **Execute the Deck Generator**:
   ```bash
   python3 scripts/generate_deck.py --format pdf
   ```
   *(If a customer name is specified, pass `--customer "<Name>"`).*

2. **What the Script Does Automatically**:
   * Authenticates with the Wiz GraphQL API using service account credentials in `.env`.
   * Queries all 5 core telemetry blocks (Workloads, Security Score, Posture, 7-Pillar Scans, K8s Coverage Ladder, Top Controls, AI Security Findings, Preview Hub, Roadmap Tracker).
   * Calculates all derived metrics, scan coverage percentages (`NON_C`, `RCI_C`, `VMI_C`, `DS_P`), and industry benchmark gaps.
   * Generates the executive presentation, highlights enabled Preview Hub features in light green, sweeps unfilled tokens, and exports the **client-ready PDF**.
   * Exports the complete **660+ metrics CSV** containing all calculated values and category descriptions.

3. **Present the Deliverables in Chat**:
   * Provide a concise executive summary of their health posture (Workloads, Security Score, Scan Coverage %, Top Risks, AI Findings).
   * Provide direct clickable markdown links to the two generated files:
     - `[Executive PDF Presentation](file:///path/to/output/Wiz_Health_Assessment_<Customer>_<Date>.pdf)`
     - `[Tenant Metrics CSV](file:///path/to/output/Wiz_Health_Assessment_<Customer>_<Date>_metrics.csv)`

---

## 2. CLI Command Options & Modes

> **PDF renders offline via LibreOffice — no Google account, OAuth, or sign-in, ever.**
> LibreOffice is installed for you when you choose the PDF option (a one-time system package,
> also available via `./install.sh`). For a no-install, TAM-handoff output, use `--format csv`.

```bash
# 1. Full Autonomous Assessment (PDF deck + Metrics CSV - Default)
python3 scripts/generate_deck.py --format pdf --customer "Acme Corporation"

# 2. Metrics CSV only — no deck, no LibreOffice. Ideal to hand to your Wiz TAM.
python3 scripts/generate_deck.py --format csv --customer "Acme Corporation"

# 3. Offline Mode from Customer-Provided CSV (when API access is unavailable)
python3 scripts/generate_deck.py --input-csv path/to/customer_metrics.csv --customer "Acme Corporation" --format pdf

# 4. Generate Blank Customer Intake Template
python3 scripts/generate_deck.py --generate-csv-template templates/wiz_customer_metrics_intake_template.csv

# 5. Standalone Markdown Audit Report
python3 scripts/run_health_assessment.py --customer "Acme Corporation" -o health_report.md
```

---

## 3. Output Artifacts

* **Executive PDF Presentation** (`output/Wiz_Health_Assessment_<Customer>_<Date>.pdf`):
  * 23-slide, high-resolution executive deck ready for C-suite and security leadership presentation.
  * Contains workload inventory, scanning coverage percentages, Kubernetes maturity ladder, Top Controls by risk count, and preview feature recommendations.
* **Tenant Metrics CSV** (`output/Wiz_Health_Assessment_<Customer>_<Date>_metrics.csv`):
  * Complete export of all tenant variables categorized by Category, Token (`{{VAR}}`), Metric Name, Value, Slide, and Description.
* **Customer Intake Template** (`templates/wiz_customer_metrics_intake_template.csv`):
  * Annotated template for offline data collection if required.
* **Run log + diagnostics** (`output/logs/wiz_health_run_<timestamp>.log` and `.diagnostics.json`):
  * Every live run tees its console output to a timestamped log file and records a per-query
    outcome (duration, attempts, HTTP codes, status), then prints a **RUN DIAGNOSTICS** block
    flagging any query that came back empty, hit a permission wall, hit the 10k graphSearch
    cap, or ran slow. Logs are under `output/` (gitignored) and may contain tenant data.

---

## Troubleshooting large accounts

Large tenants can hit slow queries, timeouts, rate limits, and the 10k graphSearch cap. If
numbers look off, read the **RUN DIAGNOSTICS** summary at the end of the run: `FAILED`/`EMPTY`
queries name exactly which metric is blank, `10k CAP hit` means that count is an undercount,
and `PERMISSION` (e.g. `Q5_audit_logs`) is usually expected with a `read:all` service account.
If a query times out on a large tenant, raise the per-query timeout and re-run:

```bash
export WIZ_QUERY_TIMEOUT=300      # seconds (default 120); Windows: set WIZ_QUERY_TIMEOUT=300
python3 scripts/generate_deck.py --format csv
```

Share `output/logs/wiz_health_run_<timestamp>.log` (+ the `.diagnostics.json` sidecar) with
your Wiz TAM for diagnosis.
