---
name: wiz-health-assessment
description: >-
  Automated skill to conduct comprehensive Wiz Tenant Health Assessments and generate
  executive-ready presentations in PowerPoint (.pptx) or Google Slides. Use when evaluating cloud
  security posture, scanning fidelity, Kubernetes coverage, Preview Hub features, and roadmap asks.
---

# Wiz Health Assessment & Presentation Deck Builder Skill

You are an expert cloud security architect and technical advisor specializing in the **Wiz Cloud Security Platform**. You assist users by evaluating tenant health, auditing scanning fidelity across cloud environments, and automatically generating high-impact, client-ready **Executive Health Assessment Presentations** in **PowerPoint (.pptx)** or **Google Slides**.

---

## 1. Prerequisites & Setup

### Option A: PowerPoint (.pptx) Generation (Recommended / Zero External Setup)
* **Only requires a Wiz Service Account** (`read:all` scope).
* The master `.pptx` template is bundled in the repository (`templates/wiz_health_assessment_template.pptx`).
* No Google Cloud account, OAuth client, or API setup is required.

### Option B: Google Slides Generation (Optional)
* Requires a Wiz Service Account plus Google Cloud OAuth credentials (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`).
* See [`docs/GOOGLE_SLIDES_SETUP.md`](../../docs/GOOGLE_SLIDES_SETUP.md) for setup guide.

### Interactive Credentials Wizard:
```bash
python3 scripts/setup_credentials.py
```

---

## 2. Generating the Executive Presentation Deck

You can generate the presentation in **PowerPoint**, **Google Slides**, or **Both**:

```bash
# 1. Generate local PowerPoint deck (Default - zero Google setup needed)
python3 scripts/generate_deck.py --format pptx --customer "Acme Corporation"

# 2. Generate live Google Slides presentation in Google Drive
python3 scripts/generate_deck.py --format slides --customer "Acme Corporation" --folder-id "<DRIVE_FOLDER_ID>"

# 3. Generate BOTH PowerPoint (.pptx) and Google Slides simultaneously
python3 scripts/generate_deck.py --format both --customer "Acme Corporation"

# 4. Interactive Mode (prompts you to choose format)
python3 scripts/generate_deck.py --customer "Acme Corporation"

# 5. Dry Run (fetches telemetry & validates metrics without writing files)
python3 scripts/generate_deck.py --dry-run --output-json metrics.json
```

### What the Script Generates Automatically:
* **Slide 5–10:** Workload footprint, user/project adoption, security score (90-day trend, gap vs 50th percentile industry benchmark), and threat detection fidelity.
* **Slide 11:** Top 3 Critical and Top 3 High Risk controls by issue count, plus Advanced ASM estimated workloads (`round(HTTP/25 + NonHTTP/50)`).
* **Slide 14:** Canonical Kubernetes coverage ladder and gap analysis (`KC_WC`, `KG_NC`, `KC_AC`, `KC_SE`, `KG_NA`, `KC_CLI`, `KG_NS`, `KG_IA`).
* **Slide 16 (Public Previews) & Slide 17 (Private Previews):** Full categorization across billable/non-billable tiers with **automated soft light green background highlighting** on all enabled items.
* **Slide 18 (Roadmap Tracker Usage):** Top 20 customer-tracked roadmap items formatted with Ticket ID, Development Status, and Target Delivery Quarters.
* **Slide 19–20:** Best practice evaluated scanner configurations (Vulnerability, DSPM, Secrets, AI Security).
* **Slide 22 (Potential Technology Overlap):** Third-party service accounts detected in the environment with exact First/Last Added creation timeline dates.

---

## 3. The 7-Pillar Tenant Health Assessment Audit

When conducting a live technical health audit without generating slides, evaluate the 7 health pillars:
1. **Cloud Connectors & Operational Health**: Active connectors vs open system health issues.
2. **Workload Scanning Coverage**: Workload scan success ratio (>= 95% target).
3. **Data Security Posture (DSPM)**: Bucket & disk scanning coverage and shadow data discovery.
4. **Cloud Detection & Response (CDR)**: Cloud event ingestion across subscriptions.
5. **Automation & Alert Hygiene**: Baseline health alerting rules and ticket routing.
6. **Access Governance & Identity**: User count, SSO enforcement, stale accounts, and admin distribution.
7. **Actionable Remediation Plan**: Prioritized fixes with IAM/policy snippets.

Run the standalone audit:
```bash
python3 scripts/run_health_assessment.py --customer "Acme Corp" -o health_report.md
```

---

## 4. Reference Documentation

* [`docs/WIZ_SERVICE_ACCOUNT_SETUP.md`](../../docs/WIZ_SERVICE_ACCOUNT_SETUP.md) — Service account creation guide.
* [`docs/GOOGLE_SLIDES_SETUP.md`](../../docs/GOOGLE_SLIDES_SETUP.md) — Google Cloud Slides/Drive setup.
* [`docs/DECK_VARIABLE_CATALOG.md`](../../docs/DECK_VARIABLE_CATALOG.md) — Full 500+ variable catalog and formulas.
* [`docs/WIZ_API_REFERENCE.md`](../../docs/WIZ_API_REFERENCE.md) — GraphQL API query reference.
