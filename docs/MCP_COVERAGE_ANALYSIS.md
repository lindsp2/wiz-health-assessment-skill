# Wiz MCP Coverage Analysis — can the Health Assessment run without a service account?

**Date:** 2026-09-02
**Question:** The Wiz `wiz-ai-plugin` authenticates via the remote Wiz MCP (browser OAuth) with **no service account**. Could our Health Assessment do the same — i.e., source all its data through Wiz MCP tools instead of direct GraphQL with a service-account token?

**Short answer:** Partially. ~70% of the deck's metrics are reachable through purpose-built MCP tools (with real rework), but ~30% — dominated by the **scanner-configuration toggles** on slides 17–18 — are not exposed by any MCP tool and still require direct GraphQL. So a fully service-account-free version is **not achievable today** without dropping those slides.

---

## Why the mismatch exists

There are two different surfaces in Wiz:

| | Security Graph (`graph_search` / `execute_graph_query`) | GraphQL API (top-level fields) |
|---|---|---|
| Models | Your **cloud estate** — resources + relationships | The **Wiz platform itself** — config, analytics, billing |
| Answers | "Which resources match / are connected?" | "What's the setting / ratio / trend / license / count?" |
| Examples | exposed VM with admin role; buckets that were scanned | scan success %, MTTR trend, license SKU, scanner toggles, Preview Hub |

The Wiz MCP exposes `execute_graph_query`/`graph_search` (Security-Graph **only**) plus ~hundreds of **curated** domain tools (23 expert domains). It does **not** expose a generic "run any GraphQL operation" tool. Our deck is ~22 graph-style queries and ~60+ top-level GraphQL fields, so it can't be handed to the MCP as-is — each metric family has to be re-sourced from whatever curated tool (if any) returns equivalent data.

## Coverage by metric family (verified against a live tenant, 2026-09-02)

| Family | # | Best MCP tool(s) | Verdict |
|---|---|---|---|
| Data Security Scanner Config (`dataScannerSettings`) | 38 | none | **NONE** |
| Workload Scanner Config | 28 | `get_non_os_disk_scanning_settings`, `get_ebs_snapshot_scanner_settings` | PARTIAL — only non-OS/EBS; FIM/exclusions/event-triggered/lambda missing |
| Vulnerability Scanner Config | 26 | `get_vulnerability_assessment_settings` | **FULL** |
| Attack Surface Mgmt Config | 37 | `list_attack_surface_rules` | PARTIAL — rule enable-state only; scanner block / redAgent modules / exposure-level absent |
| Cloud Events | 26 | `list_cloud_events_grouped` | **FULL** |
| Potential Integrations | 72 | `graph_search` TECHNOLOGY→SERVICE_ACCOUNT | **GRAPH** |
| Top Controls | 12 | `list_issues_grouped` (SOURCE_RULE) | **FULL** |
| Container Registries | 12 | `list_cloud_resources_grouped` | **FULL** |
| AI Footprint + AI Findings | 13 | `get_ai_security_summary`, `list_ai_security_findings` | **FULL** |
| Threats & Runtime | 5 | `list_threats` / `list_detections` | **FULL** |
| Workload Inventory | 8 | `get_workload_scan_status`, `list_kubernetes_clusters` | PARTIAL — stitched from several tools |
| DSPM Breakdown + Scans | 10 | `list_datastores_grouped`, `get_data_scan_results` | **FULL** |
| Container / VM / Non-OS Image Scans | 12 | `get_workload_scan_status`, `list_workload_scan_failures` | PARTIAL — per-status SECURITY_TOOL_SCAN split is graph |
| Adoption & Governance | 13 | `list_automation_rules`, `list_inventory_rules`, `list_monitored_metrics` | PARTIAL — tagging/discovery rules, agent toggles, extension/MCP-user counts missing |
| Metrics (misc scalars) | 50 | `list_api_endpoints`, cicd scans, `get_connector`, license/adoption | PARTIAL — many one-off tools; a few graph-only |
| **success-covered:** Licenses, Preview Hub, Security Posture, Kubernetes, System Health, Projects, Cloud Architecture, Connectors | ~55 | `list_licenses`, `list_preview_migration_hub_items`, `get_security_score`, `list_kubernetes_clusters`, `list_system_health_issues*`, `list_projects`, `list_subscriptions` | **FULL** |

## Tally (of ~440 template variables)

- **~160 FULL** — a purpose-built tool returns essentially the data
- **~150 PARTIAL** — topic covered but shape differs, or must be stitched from several tools
- **~72 GRAPH-only** — Potential Integrations traversal (doable via `graph_search`)
- **~38 NONE** — `dataScannerSettings` block has no MCP tool at all

## The crux: scanner-config toggles (~129 metrics, slides 17–18)

- Vulnerability Scanner config (26) → **FULL** via `get_vulnerability_assessment_settings`
- Data Security Scanner config (38) → **NONE** (no tool exposes `dataScannerSettings`)
- Workload Scanner config (28) → **PARTIAL** (only non-OS-disk + EBS-snapshot settings)
- Attack Surface config (37) → **PARTIAL** (rule enable-state only; no scanner-settings block, red-agent modules, or endpoint exposure level)

These raw ON/OFF configuration toggles are a defining part of the deck (the "aligned with Wiz recommendation ✓/✗" scanner-configuration slides) and are only reachable via direct GraphQL.

## Recommendation

Ship the **plugin packaging** now (marketplace install, no `git clone`) while keeping the proven Python pipeline + service-account auth — it delivers the headline UX win without losing deck fidelity. Treat a service-account-free, MCP-sourced rebuild as a **separate future project**: it would require re-sourcing ~150 PARTIAL metrics from different tool shapes, moving Potential Integrations to `graph_search`, and either dropping or GraphQL-supplementing the ~129 scanner-config toggles. Revisit if/when Wiz adds MCP tools for the scanner-settings blocks (esp. `dataScannerSettings`).
