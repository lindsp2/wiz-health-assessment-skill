# Wiz Tenant Health Assessment & Executive Presentation Suite

> A portable, customer-facing AI agent skill, automation engine, and GraphQL toolkit for the **Wiz Cloud Security Platform**.

Works out-of-the-box with **Claude Code**, **Claude Desktop**, **Cursor**, **ChatGPT**, **VS Code (Cline / Roo-Code / Continue)**, **Google Antigravity**, and **Jetski**.

---

## 🌟 What This Repository Provides

1. **Automated Executive Presentation Deck Builder (`scripts/generate_deck.py`)**:
   * Authenticates with the Wiz GraphQL API and queries live tenant posture, inventory, and configuration settings.
   * Generates a **23-slide executive deck** as an **offline PDF** (rendered locally via LibreOffice — no Google account) or **PowerPoint (`.pptx`)**, plus a metrics CSV on every run.
   * Populates **500+ variables** including canonical Kubernetes coverage ladder & gaps, Top 3 Critical & High controls, Advanced ASM estimated workloads, and Tracked Roadmap items.
   * Automatically applies **soft light green background highlighting** (`#E0F5E0`) to all enabled Public and Private Preview Hub features.
   * Sweeps remaining unfilled template tokens and cleans up unused date placeholders.

2. **Universal AI Agent Skills (`skills/`)**:
   * `skills/wiz-health-assessment/SKILL.md`: Guides the AI assistant to conduct end-to-end tenant health assessments and generate client-ready presentations.
   * `skills/wiz-api-expert/SKILL.md`: Expert assistant for constructing, optimizing, and executing custom GraphQL queries against the Wiz API.
   * `skills/wiz-cloud-security/SKILL.md`: Universal cloud security assessment and MCP tool suite.

3. **Standalone Tenant Health Assessment Auditor (`scripts/run_health_assessment.py`)**:
   * Evaluates the 7 core health pillars (Connectors, Workload Scanning, DSPM, CDR, Automation Rules, Identity Governance, Action Plan) and generates an executive Markdown scorecard.

4. **Wiz GraphQL CLI Client (`scripts/wiz_client.py`)**:
   * Zero-external-dependency script providing automatic token caching, schema introspection search, and direct query execution.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/lindsp77/wiz-health-assessment-skill.git
cd wiz-health-assessment-skill
```

> [!NOTE]
> **Offline PDF export (no Google required).** The installer also provisions
> **LibreOffice**, a free, offline renderer used to convert the generated deck to
> PDF with zero Google credentials. For faithful output it installs the deck's
> design fonts — **Poppins** and **DM Sans** are bundled in `assets/fonts/` (free
> OFL) and copied to your user font directory; **JetBrains Mono** comes from the
> package manager; and **Arial/Calibri** map to free metric-compatible substitutes
> (Liberation Sans / Carlito). Without the bundled fonts, LibreOffice silently
> falls back to DejaVu Sans and the deck looks wrong — so the installer handles
> them for you. Skip all of this with `--skip-libreoffice` (you still get PPTX +
> CSV, and can enable PDF later).

### 2. Run the One-Step Installer

* **Linux / macOS / Git Bash:**
  ```bash
  ./install.sh
  ```
* **Windows (Command Prompt `cmd.exe`):**
  ```cmd
  install.bat
  ```
* **Windows (PowerShell):**
  ```powershell
  .\install.ps1
  ```
* **Or via Python directly (Any OS):**
  ```bash
  python -m pip install -r requirements.txt
  python scripts/install_skills.py
  ```

---

### 3. Using with AI Assistants (Claude Code, Cursor, Jetski)

Once cloned, open your AI assistant in the repository folder and simply tell it:
> **"Run a health assessment for my Wiz tenant and generate my files"**

The AI assistant will:
1. Ask for your **Customer Name** and **Wiz Datacenter**.
2. Ask **which output you want**:
   * 📄 **PDF deck** — a board-ready executive presentation. Needs a **one-time LibreOffice install** (free, offline); the assistant offers to run `./install.sh` for you.
   * 📊 **CSV export** — the full metrics CSV only, **no install required** — ideal to hand to your **Wiz Technical Account Manager (TAM)** to review together.
3. Guide you to securely configure your Service Account credentials (via `.env` or the isolated `setup_credentials.py` wizard).
4. Autonomously execute the assessment and deliver your chosen output:
   * 📄 **Executive PDF Presentation** (`output/Wiz_Health_Assessment_<Customer>_<Date>.pdf`) — 23-slide board-ready presentation *(PDF path)*.
   * 📊 **Tenant Metrics CSV** (`output/Wiz_Health_Assessment_<Customer>_<Date>_metrics.csv`) — 660+ metric export *(always produced)*.

---

### 4. Direct CLI Commands

* **Generate PDF Presentation & Metrics CSV (Default):**
  ```bash
  python3 scripts/generate_deck.py --format pdf --customer "Acme Corporation"
  ```
  The PDF is **always rendered locally and offline via LibreOffice — no Google account,
  OAuth, or credentials.** LibreOffice is installed for you when you choose the PDF option
  (or via `./install.sh`); if it is missing, the script prints the exact one-line install
  command instead of silently producing only a PPTX.

* **Generate the Metrics CSV only (no deck, no LibreOffice needed):**
  ```bash
  python3 scripts/generate_deck.py --format csv --customer "Acme Corporation"
  ```
  Fastest path — queries the tenant and writes just the 660+ metric CSV. Ideal to hand to
  your Wiz TAM.

* **Generate a local PowerPoint (.pptx) + CSV:**
  ```bash
  python3 scripts/generate_deck.py --format pptx --customer "Acme Corporation"
  ```

* **(Advanced, optional) Live Google Slides deck:**
  ```bash
  python3 scripts/generate_deck.py --format slides --customer "Acme Corporation"
  ```
  Requires you to set your own Google API env vars (`GOOGLE_CLIENT_ID`,
  `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`). This is **not** needed for the PDF and is
  never part of the default flow — see `docs/GOOGLE_SLIDES_SETUP.md`.

* **Offline Mode from Customer Intake CSV:**
  ```bash
  python3 scripts/generate_deck.py --input-csv path/to/metrics.csv --customer "Acme Corporation"
  ```

---

## 📂 Repository Structure

```text
.
├── README.md                                # Overview & Quickstart
├── SKILL.md                                 # Root universal agent skill definition
├── install.sh                               # Linux / macOS installer
├── install.bat                              # Windows Command Prompt installer
├── install.ps1                              # Windows PowerShell installer
├── .env.example                             # Environment variables template
├── requirements.txt                         # Python dependencies
├── skills/
│   ├── wiz-health-assessment/
│   │   └── SKILL.md                         # Skill: Executive Health Assessment & Deck Builder
│   ├── wiz-api-expert/
│   │   └── SKILL.md                         # Skill: Expert Wiz GraphQL API Assistant
│   └── wiz-cloud-security/
│       └── SKILL.md                         # Skill: Universal Cloud Security & MCP Suite
├── docs/
│   ├── WIZ_SERVICE_ACCOUNT_SETUP.md         # Guide: Minting a Wiz Service Account (read:all)
│   ├── GOOGLE_SLIDES_SETUP.md               # Guide: Enabling Google Slides/Drive OAuth
│   ├── DECK_VARIABLE_CATALOG.md             # Full 500+ slide variable catalog & formulas
│   ├── WIZ_API_REFERENCE.md                 # 3,000+ lines of GraphQL queries & graphSearch recipes
│   ├── TENANT_HEALTH_ASSESSMENT_GUIDE.md    # 7-Pillar Health Audit Methodology
│   └── MCP_INSTALLATION_GUIDE.md            # Connecting Wiz MCP across AI clients
├── scripts/
│   ├── generate_deck.py                     # Main CLI tool: Live API -> PDF / PPTX / Google Slides deck
│   ├── local_pdf.py                         # Offline PPTX -> PDF via LibreOffice (zero Google)
│   ├── ensure_libreoffice.py                # Cross-platform LibreOffice + font provisioner (installer)
│   ├── pptx_processor.py                    # Pure-Python OpenXML parser, bullet expander & highlighter
│   ├── setup_credentials.py                 # Interactive setup wizard to test & create .env
│   ├── install_skills.py                    # Cross-platform skills linker & installer
│   ├── run_health_assessment.py             # Automated 7-pillar tenant health assessment script
│   ├── wiz_client.py                        # Standalone GraphQL client with token caching & schema search
│   ├── api_delta_processor.py               # Telemetry transformation & metric calculations
│   ├── preview_hub.py                       # Preview Hub & Tracked Roadmap items formatter
│   └── google_slides_client.py              # Google Slides/Drive API client & token sweep engine
├── templates/
│   ├── wiz_health_assessment_template.pptx  # Bundled 22-slide PowerPoint master template
│   ├── CUSTOMER_HEALTH_ASSESSMENT_REPORT.md # Markdown scorecard template
│   └── env.example                          # Backup environment template
```

---

## 🔒 Security & Privacy

* **Zero Credentials Sent to LLM**: Secrets are stored strictly in your local `.env` file on disk. The AI skill explicitly mandates never asking for or echoing secrets in chat.
* **Read-Only by Default**: The API client operates in read-only mode (`read:all` scope) and performs no destructive operations.
* **Sanitized Documentation**: No customer names, tenant IDs, or private data are committed to the repository.

---

## 📄 License
Apache 2.0 / MIT.
