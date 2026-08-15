# Executive Presentation Deck Variable Catalog

This document details the core variables, calculations, and data sources across all slides of the Executive Health Assessment & Review Presentation.

---

## 1. General & Tenant Metadata

| Variable | Description | Source / Formula |
|---|---|---|
| `{{Customer}}` | Customer Organization Name | CLI argument or `viewerV2.tenant.name` |
| `{{TODAY}}` | Generation Date (`MM/DD/YYYY`) | Current timestamp |
| `{{CONTRACT_END_FMT}}` | Renewal Date | Renewal tracking |
| `{{CUS_NOD}}` | Customer Days Active | Days since onboarding |

---

## 2. Slide 10: Posture, Security Score & Threat Detection

| Variable | Description | Source / Formula |
|---|---|---|
| `{{SS}}` | Current Security Score (%) | `securityScores(first: 1).nodes[0].score` |
| `{{SP}}` | 50th Percentile Industry Benchmark | `ssBench.securityScore.byIndustry.percentile50` |
| `{{SG}}` | Security Score Gap (%) | `SS - SP` |
| `{{s1d}}` | 90-Day Score Trend Delta | Delta from 90 days ago (`+X%` / `-X%`) |
| `{{OC}}` / `{{OH}}` | Open Critical / High Issues | `issuesTable(status: [OPEN, IN_PROGRESS])` |
| `{{RC}}` / `{{RH}}` | Resolved Critical / High Issues (90d) | `issuesTable(status: [RESOLVED])` past 90 days |
| `{{MTTR_O}}` | Mean Time to Remediation (Days) | `issuesTable` MTTR analytics |
| `{{AVG_AGEC}}` / `{{AVG_AGEH}}` | Average Age of Open Critical/High (Days) | Average age data points |
| `{{OT}}` / `{{RT}}` | Open Threats / Resolved Threats (90d) | Threat Detection engine (`N/A` if unlicensed) |

---

## 3. Slide 11: Top Risk Controls & Advanced Workloads

| Variable | Description | Source / Formula |
|---|---|---|
| `{{CI_CONTROL_1..3}}` | Top 3 Critical Controls by Issue Count | `issuesGroupedByValue(groupBy: SOURCE_RULE, severity: [CRITICAL])` |
| `{{CI_CBC_1..3}}` | Issue Counts for Top 3 Critical Controls | Associated issue count per control |
| `{{HI_CONTROL_1..3}}` | Top 3 High Risk Controls by Issue Count | `issuesGroupedByValue(groupBy: SOURCE_RULE, severity: [HIGH])` |
| `{{HI_CBC_1..3}}` | Issue Counts for Top 3 High Risk Controls | Associated issue count per control |
| `{{AE_HTTP}}` | HTTP Application Endpoints | `applicationEndpoints(protocol: [HTTP, HTTPS])` |
| `{{AE_NHTTP}}` | Non-HTTP Application Endpoints | `applicationEndpoints(protocol: not [HTTP, HTTPS])` |
| `{{AE_TOT}}` | Advanced ASM Estimated Workloads | `round(AE_HTTP / 25.0 + AE_NHTTP / 50.0)` |

---

## 4. Slide 14: Canonical Kubernetes Coverage Ladder & Gaps

| Variable | Description | Property Filter (`type: KUBERNETES_CLUSTER`) |
|---|---|---|
| `{{KC_WC}}` | K8s Workload / Cloud Scanning Coverage | `deploymentCoverage_cloudScanner_deploymentStatus: Installed` |
| `{{KG_NC}}` | K8s Workload Scanning Gap (Not Installed) | `deploymentCoverage_cloudScanner_deploymentStatus: NotInstalled` |
| `{{KC_AC}}` | K8s Admission Controller Installed | `deploymentCoverage_admissionController_deploymentStatus: Installed` |
| `{{KC_SE}}` | K8s Runtime Sensor Installed | `deploymentCoverage_sensor_deploymentStatus: Installed` |
| `{{KG_NA}}` | K8s Audit Log Collector Gap | `deploymentCoverage_auditLogCollector_deploymentStatus: NotInstalled` |
| `{{KC_CLI}}` | K8s Audit Log Collector Installed | `deploymentCoverage_auditLogCollector_deploymentStatus: Installed` |
| `{{KG_NS}}` | K8s Runtime Sensor Gap | `deploymentCoverage_sensor_deploymentStatus: NotInstalled` |
| `{{KG_IA}}` | Internet-Accessible Clusters | `isInternetFacing: true` |

---

## 5. Slides 16 & 17: Preview Hub Features & Automated Highlighting

* **Public Previews (Slide 16)**: `{{BILLABLE_ADVANCED}}`, `{{BILLABLE_DEFEND}}`, `{{BILLABLE_SENSOR}}`, `{{BILLABLE_CODE}}`, `{{ALL_NON_BILLABLE_PREVIEW}}`
* **Private Previews (Slide 17)**: `{{PRIVATE_BILLABLE}}`, `{{PRIVATE_NON_BILLABLE}}`
* **Automated Highlighting**: Script scans Slides 16 & 17 and applies `#E0F5E0` (soft light green background) to all enabled features.

---

## 6. Slide 18: Roadmap Tracker Usage

* **`{{ROADMAP_TRACKER}}`**: Top 20 customer-tracked roadmap items formatted as:
  `• Title [Ticket ID] — Development Status (Target Quarter/Year)`

---

## 7. Slide 22: Potential Technology Overlap

* **`{{PI_T1_1..8}}`**: Cloud Security Platform third-party technologies detected.
* **`{{PI_T1_1..8_SA}}`**: Total service accounts per technology.
* **`{{PI_T1_1..8_FA}} / {{PI_T1_1..8_LA}}`**: First Added / Latest Added creation dates (`MM-DD-YY`).
