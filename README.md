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

3. **Standalone Tenant Health Assessment Auditor (`scripts/run_health_assessment.py`)**:
   * Evaluates the 7 core health pillars (Connectors, Workload Scanning, DSPM, CDR, Automation Rules, Identity Governance, Action Plan) and generates an executive Markdown scorecard.

4. **Wiz GraphQL CLI Client (`scripts/wiz_client.py`)**:
   * Zero-external-dependency script providing automatic token caching, schema introspection search, and direct query execution.

---

## 🚀 Quick Start

There are two ways to get this: **install it as a Claude Code plugin** (recommended — no
clone, one-command install, auto-updates) or **clone the repo** (works with any assistant).

### Option A — Install as a Claude Code plugin (recommended)

```
/plugin marketplace add lindsp77/wiz-health-assessment-skill
/plugin install wiz-health-assessment@wiz-health-assessment-skill
```

Then just ask: *"Run a Wiz health assessment and generate my files."* The skill is invokable
explicitly as `/wiz-health-assessment:wiz-health-assessment`. Credentials come from a `.env` in
**your current working directory** (see Step 2) — the plugin never stores them. That's it; skip
to Step 2. (No `git clone`, no `pip install` — the scripts are pure Python standard library.)

### Option B — Clone the repository

```bash
git clone https://github.com/lindsp77/wiz-health-assessment-skill.git
cd wiz-health-assessment-skill
```

> [!IMPORTANT]
> **No installer or `pip install` is required to run the assessment (either option).** The
> scripts are pure Python **standard library** (Python 3.8+) with **zero third-party
> dependencies**. The only setup is your Wiz credentials (Step 2). Just point your AI
> assistant at the folder (or install the plugin) and ask it to run the assessment.

### 2. Configure your Wiz credentials

Create a `.env` in the repo root (copy `.env.example`) with your Wiz Service
Account `WIZ_CLIENT_ID` / `WIZ_CLIENT_SECRET` and datacenter — or run the wizard:
```bash
python3 scripts/setup_credentials.py
```
That's everything needed for the **metrics CSV** (the default output).

### 3. (Optional) Enable the offline PDF deck — LibreOffice

You only need this if you want the polished **PDF** deck. The PDF is rendered
**locally and offline via LibreOffice** (a free system package — **no Google
account, no credentials**). You don't have to run anything up front: when you ask
the assistant for a PDF and LibreOffice isn't installed yet, **it offers to install
it for you**. To provision it yourself instead:

* **Linux / macOS / Git Bash:** `./install.sh --skip-credentials`
* **Windows:** `install.bat` / `.\install.ps1`

> The installer provisions **LibreOffice** plus the deck's design fonts — **Poppins**
> and **DM Sans** (bundled OFL in `assets/fonts/`), **JetBrains Mono**, and free
> metric-compatible substitutes for Arial/Calibri (Liberation Sans / Carlito).
> Without those fonts LibreOffice falls back to DejaVu Sans and the deck looks
> wrong, so the installer handles them for you. It installs **no** Python packages
> (there are none to install). Skip the renderer with `--skip-libreoffice` — you
> still get the PPTX + CSV and can enable PDF later.

---

### 4. Using with AI Assistants (Claude Code, Cursor, Jetski)

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

### 5. Direct CLI Commands

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
├── requirements.txt                         # (none — pure stdlib; kept as a no-op placeholder)
├── skills/
│   ├── wiz-health-assessment/
│   │   └── SKILL.md                         # Skill: Executive Health Assessment & Deck Builder
│   └── wiz-api-expert/
│       └── SKILL.md                         # Skill: Expert Wiz GraphQL API Assistant
├── .claude-plugin/
│   ├── plugin.json                          # Claude Code plugin manifest
│   └── marketplace.json                     # Marketplace listing (for /plugin marketplace add)
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
