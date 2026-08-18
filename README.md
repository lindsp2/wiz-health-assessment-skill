# Wiz Tenant Health Assessment & Executive Presentation Suite

> A portable, customer-facing AI agent skill, automation engine, and GraphQL toolkit for the **Wiz Cloud Security Platform**.

Works out-of-the-box with **Claude Code**, **Claude Desktop**, **Cursor**, **ChatGPT**, **VS Code (Cline / Roo-Code / Continue)**, **Google Antigravity**, and **Jetski**.

---

## 🌟 What This Repository Provides

1. **Automated Executive Presentation Deck Builder (`scripts/generate_deck.py`)**:
   * Authenticates with the Wiz GraphQL API and queries live tenant posture, inventory, and configuration settings.
   * Generates a **22-slide PowerPoint presentation (`.pptx`)** or **Google Slides deck**.
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

### 3. Generate the Executive Presentation Deck

* **PowerPoint (.pptx) - Local file, zero Google setup needed (Default):**
  ```bash
  python scripts/generate_deck.py --format pptx --customer "Acme Corporation"
  ```
  *Output:* `output/Wiz_Health_Assessment_Acme_Corporation_YYYY-MM-DD.pptx`

* **Google Slides - Live deck in Google Drive:**
  ```bash
  python scripts/generate_deck.py --format slides --customer "Acme Corporation" --folder-id "<GOOGLE_DRIVE_FOLDER_ID>"
  ```

* **Both Formats Simultaneously:**
  ```bash
  python scripts/generate_deck.py --format both --customer "Acme Corporation"
  ```

* **Interactive Mode (prompts for format choice):**
  ```bash
  python scripts/generate_deck.py --customer "Acme Corporation"
  ```

* **Dry Run (validates metrics without writing presentation files):**
  ```bash
  python scripts/generate_deck.py --dry-run --output-json metrics.json
  ```

---

### 4. Using with AI Assistants (Claude Code, Cursor, Jetski)

Once cloned or installed, simply open your AI assistant in the repository folder and ask:
* *"Run a health assessment for Acme Corp and generate a PowerPoint deck."*
* *"Build an executive review presentation for my tenant."*
* *"Query open critical issues in my Wiz tenant."*

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
│   ├── generate_deck.py                     # Main CLI tool: Live API -> PPTX / Google Slides deck
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
