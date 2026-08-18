# Wiz Tenant Health Assessment & Executive Presentation Suite

> A portable, customer-facing AI agent skill, automation engine, and GraphQL toolkit for the **Wiz Cloud Security Platform**.

Works out-of-the-box with **Claude Code**, **Cursor**, **ChatGPT**, **VS Code (Cline / Roo-Code)**, **Google Antigravity**, and **Jetski**.

---

## 🌟 What This Repository Provides

1. **Automated Executive Presentation Deck Builder (`scripts/generate_deck.py`)**:
   * Authenticates with the Wiz GraphQL API and queries live tenant posture, inventory, and configuration settings.
   * Copies the master 22-slide executive presentation template in Google Slides.
   * Populates **500+ variables** including canonical Kubernetes coverage ladder & gaps, Top 3 Critical & High controls, Advanced ASM estimated workloads, and Tracked Roadmap items.
   * Automatically applies **soft light green background highlighting** (`#E0F5E0`) to all enabled Public and Private Preview Hub features.
   * Sweeps remaining unfilled template tokens and archives prior customer decks.

2. **Universal AI Agent Skills (`skills/`)**:
   * `skills/wiz-health-assessment/SKILL.md`: Guides the AI assistant to conduct end-to-end tenant health assessments and generate client-ready Google Slides presentations.
   * `skills/wiz-api-expert/SKILL.md`: Expert assistant for constructing, optimizing, and executing custom GraphQL queries against the Wiz API.
   * `skills/wiz-cloud-security/SKILL.md`: Universal cloud security assessment and MCP tool suite.

3. **Standalone Tenant Health Assessment Auditor (`scripts/run_health_assessment.py`)**:
   * Evaluates the 7 core health pillars (Connectors, Workload Scanning, DSPM, CDR, Automation Rules, Identity Governance, Action Plan) and generates an executive Markdown/PDF scorecard.

4. **Wiz GraphQL CLI Client (`scripts/wiz_client.py`)**:
   * Zero-external-dependency script providing automatic token caching, schema introspection search, and direct query execution.

---

## 🚀 Quick Start

Requires **Python 3.8 or newer**. Everything below works on Windows, macOS, and Linux.

### 1. Installation

Clone the repository, then run the installer for your platform. It installs the
Python dependencies, copies the skills into your AI agent, and launches the
credentials wizard if you have not configured it yet.

**Windows (PowerShell)**
```powershell
git clone https://github.com/your-org/wiz-health-assessment-skill.git
cd wiz-health-assessment-skill
.\install.ps1
```
If Windows blocks the script, run it once as
`powershell -ExecutionPolicy Bypass -File .\install.ps1`.

**macOS / Linux**
```bash
git clone https://github.com/your-org/wiz-health-assessment-skill.git
cd wiz-health-assessment-skill
./install.sh
```

**Any platform**, if you would rather skip the shell wrappers:
```bash
python install.py     # Windows
python3 install.py    # macOS / Linux
```

All three routes do the same work. Options:

| Flag | Effect |
|---|---|
| `--target NAME` | Install to `claude`, `jetski`, `cursor`, `workspace`, or `all` instead of choosing from the menu |
| `--yes` | Accept defaults and never prompt (unattended installs) |
| `--skip-credentials` | Do not launch the credentials wizard |
| `--skip-deps` | Do not install Python dependencies |

> **Note on Windows symlinks:** skills are symlinked when permitted, which keeps
> them in sync with the repo. Windows only allows symlinks under Developer Mode
> or an elevated shell, so the installer falls back to copying. If you pulled
> updates, re-run the installer to refresh the copies.

### 2. Configure Credentials
Run the interactive setup wizard:
```bash
python scripts/setup_credentials.py     # Windows
python3 scripts/setup_credentials.py    # macOS / Linux
```
The wizard needs a real terminal because it reads your client secret without
echoing it. Your credentials are written to a local `.env` file, which is
git-ignored and never leaves your machine.
*Follow the on-screen prompts to enter your Wiz Service Account (`read:all` scope) and optional Google Cloud OAuth credentials.*

### 3. Generate the Executive Presentation Deck

> The commands below use `python3`. On Windows, substitute `python`.

```bash
# Full deck generation
# Generate local PowerPoint (.pptx) - no Google account needed
python3 scripts/generate_deck.py --format pptx --customer "Acme Corporation"

# Generate live Google Slides presentation in Google Drive
python3 scripts/generate_deck.py --format slides --customer "Acme Corporation" --folder-id "<GOOGLE_DRIVE_FOLDER_ID>"

# Generate both formats
python3 scripts/generate_deck.py --format both --customer "Acme Corporation"

# Dry run mode (validate metrics and variables without modifying Google Slides)
python3 scripts/generate_deck.py --dry-run --output-json metrics.json
```

### 4. Run an Automated Tenant Health Audit
```bash
python3 scripts/run_health_assessment.py --customer "Acme Corporation" -o health_report.md
```

---

## 📂 Repository Structure

```text
.
├── README.md                                # Overview & Quickstart
├── SKILL.md                                 # Root universal agent skill definition
├── .env.example                             # Environment variables template
├── requirements.txt                         # Python dependencies
├── install.py                               # Cross-platform installer (the real entry point)
├── install.sh                               # macOS/Linux wrapper -> install.py
├── install.ps1                              # Windows PowerShell wrapper -> install.py
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
│   ├── generate_deck.py                     # Main CLI tool: Live API -> Google Slides deck
│   ├── setup_credentials.py                 # Interactive setup wizard to test & create .env
│   ├── run_health_assessment.py             # Automated 7-pillar tenant health assessment script
│   ├── install_skills.py                    # Installs the skills into your AI agent environment
│   ├── console_compat.py                    # Cross-platform console encoding & prompt helpers
│   ├── refresh_schema.py                    # Fetches the full GraphQL introspection schema
│   ├── wiz_client.py                        # Standalone GraphQL client with token caching & schema search
│   ├── api_delta_processor.py               # Telemetry transformation & metric calculations
│   ├── pptx_processor.py                    # Local PowerPoint template engine (no Office APIs)
│   ├── preview_hub.py                       # Preview Hub & Tracked Roadmap items formatter
│   └── google_slides_client.py              # Google Slides/Drive API client & token sweep engine
└── templates/
    ├── CUSTOMER_HEALTH_ASSESSMENT_REPORT.md # Markdown scorecard template
    └── env.example                          # Backup environment template
```

---

## 🔒 Security & Privacy

* **Zero Hardcoded Credentials**: All secrets are strictly loaded from environment variables or `.env`.
* **Read-Only by Default**: The API client operates in read-only mode (`read:all` scope) and performs no destructive operations.
* **Sanitized Documentation**: No customer names, tenant IDs, or private data are committed to the repository.

---

## 📄 License
Apache 2.0 / MIT.
