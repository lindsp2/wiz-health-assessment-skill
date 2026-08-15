# Wiz MCP Tool Inventory & Reference

This document provides a categorized inventory of all **130+ tools** available via the **Wiz MCP Server** (`https://mcp.app.wiz.io`), along with their primary use cases and parameters.

---

## 1. Platform & Adoption
Tools for tracking user adoption, portal configuration, and organizational deployment.

| Tool | Purpose |
| :--- | :--- |
| `get_platform_adoption_metrics` | Retrieve overall tenant metrics (active users, total projects, integrated cloud services). |
| `get_users_usage` | Fetch user activity logs and login history. |
| `list_users` | List all users and service accounts registered in the Wiz portal. |
| `list_projects` | List Wiz projects with security scores, issue counts, and resource totals. |
| `get_project` | Deep-dive into a specific project's scope, teams, and policies. |
| `list_integrations` | List configured third-party integrations (Slack, Jira, ServiceNow, PagerDuty, etc.). |
| `list_portal_lens` | Inspect configured Lens views and scope filters in the portal. |

---

## 2. Licenses & Cost Management
Tools for license quota monitoring and multi-cloud infrastructure cost analysis.

| Tool | Purpose |
| :--- | :--- |
| `list_licenses` | List all purchased SKUs, start/end dates, total quotas, and consumed units. |
| `get_license` | Detailed status and breakdown for a single SKU license. |
| `get_cost_analysis_grouped` | Multi-cloud cost breakdown grouped by account, provider, or project. |
| `get_cost_investigation` | Investigate historical cost trends and anomalies. |
| `get_cost_optimization_opportunities` | Recommendations for cost savings (idle VMs, unattached disks, over-provisioned resources). |
| `get_kubernetes_cost` | Granular cost breakdown for Kubernetes clusters and workloads. |
| `get_resource_cost` | Direct billing cost attribution for specific cloud resources. |

---

## 3. Monitored Metrics (Historical Trending)
Tools for retrieving time-series metric data over 30d, 90d, and custom windows.

| Tool | Purpose |
| :--- | :--- |
| `list_monitored_metrics` | List all registered historical metrics in the tenant (70+ built-in types). |
| `get_monitored_metric` | Retrieve time-series data points for a specific metric ID (e.g., `wm-active-users`, `wm-security-score`, `wm-data-scan-coverage`). |

---

## 4. Security Posture & Score
Tools for assessing overall risk, compliance benchmarks, and policy controls.

| Tool | Purpose |
| :--- | :--- |
| `get_security_score` | Fetch the overall tenant or project-level security score (0–100). |
| `list_posture_issues` | List configuration issues violating security posture policies. |
| `list_controls` | List all security controls and their passing/failing status. |
| `list_compliance_frameworks` | List supported compliance frameworks (CIS, NIST, ISO 27001, SOC 2, HIPAA, PCI-DSS). |
| `get_compliance_framework` | Detailed breakdown of compliance coverage, gaps, and failing controls. |
| `list_framework_failing_controls`| Identify specific controls failing across one or more compliance benchmarks. |

---

## 5. Security Issues & Graph Intelligence
Tools for managing active risk findings, toxic combinations, and Security Graph attack paths.

| Tool | Purpose |
| :--- | :--- |
| `list_issues` | List all active security issues filtered by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), status (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `REJECTED`), and project. |
| `list_issues_grouped` | Retrieve issue counts grouped by severity, risk category, status, or asset type. |
| `get_issue` | Comprehensive details of a specific issue, including remediation guidance, assigned tickets, and timeline. |
| `get_issue_security_graph` | Retrieve the visual and logical Security Graph representing the toxic combination (e.g., Public Internet $\rightarrow$ VM $\rightarrow$ High Privilege Role $\rightarrow$ Sensitive Data). |
| `get_issue_evidence_records` | Detailed raw evidence collected by Wiz during the scan. |
| `get_issue_resolution_evidence` | Proof and verification logs that an issue was remediated. |
| `graph_search` | Execute arbitrary Wiz Security Graph queries to find complex topologies and attack paths. |
| `get_graph_entity_raw_data` | Fetch full configuration and relationship JSON for any entity in the Security Graph. |
| `list_ignore_rules` | List active suppression and exception rules for issues. |

---

## 6. Vulnerabilities & Software Composition (SBOM / SCA)
Tools for investigating CVEs, vulnerable libraries, OS packages, and SBOMs.

| Tool | Purpose |
| :--- | :--- |
| `list_vulnerability_findings` | List CVE findings across VMs, serverless functions, container images, and pods. |
| `list_vulnerability_findings_grouped`| Group vulnerability findings by CVE ID, severity, CVSS score, or asset. |
| `get_vulnerability_finding` | Deep dive into a specific vulnerability instance, fixed version, and CVSS vector. |
| `get_vulnerability_catalog` | Query Wiz's global threat and vulnerability knowledge base. |
| `get_vulnerability_ai_description`| Retrieve AI-synthesized explanation of vulnerability exploitability and impact. |
| `list_sca_library_findings` | List vulnerable open-source dependencies (npm, PyPI, Maven, Go, Cargo, etc.). |
| `list_sbom` | Retrieve Software Bill of Materials (SBOM) for container images and VM disks. |
| `list_package_dependencies` | Inspect package dependency tree on workloads. |

---

## 7. Cloud Infrastructure & Inventory
Tools for querying cloud accounts, resources, Kubernetes, and network exposures.

| Tool | Purpose |
| :--- | :--- |
| `list_cloud_resources` | Query cloud inventory across AWS, GCP, Azure, OCI, and Alibaba Cloud. |
| `list_cloud_resources_grouped` | Group resources by resource type, region, cloud account, or tag. |
| `get_cloud_resource` | Fetch detailed configuration and metadata for a single cloud asset. |
| `list_cloud_resource_revisions` | View historical configuration changes and drift for an asset. |
| `list_subscriptions` | List all connected cloud accounts, projects, and subscriptions. |
| `list_kubernetes_clusters` | List managed and unmanaged K8s clusters (EKS, GKE, AKS, OpenShift). |
| `list_container_images` | List discovered container images, registries, and scan states. |
| `list_connectors` | Check deployment health and sync status of cloud connectors. |
| `list_endpoint_attack_surfaces` | List all externally exposed IPs, domains, and internet-facing entry points. |
| `get_network_exposure` | Inspect ingress/egress rules and exposure paths for a workload. |

---

## 8. Data Security Posture Management (DSPM)
Tools for discovering sensitive data, PII, financial records, and datastore configurations.

| Tool | Purpose |
| :--- | :--- |
| `list_data_findings` | List exposed buckets, databases, and unencrypted sensitive data stores. |
| `list_data_findings_grouped` | Group data findings by classifier (e.g., PII, Credit Cards, API Keys, Health Data). |
| `list_datastores` | Inventory of all discovered databases, Object Storage buckets, and file shares. |
| `list_data_classifiers` | List custom and built-in data classifier patterns. |
| `get_data_scan_results` | Inspect data discovery scan status and classified object sample counts. |

---

## 9. Identity & Access Management (CIEM)
Tools for evaluating identity permissions, privilege escalation, and excessive access.

| Tool | Purpose |
| :--- | :--- |
| `list_identities` | Inventory of IAM users, roles, service accounts, and identity providers. |
| `list_excessive_access_findings` | Identify identities with unused admin privileges or dangerous permissions. |
| `list_principals` | List human and machine principals across cloud accounts. |
| `list_entitlements` | Inspect granted permissions, effective permissions, and privilege paths. |

---

## 10. Threat Detection & Runtime (Wiz Defend & Sensor)
Tools for runtime security monitoring, CDR (Cloud Detection and Response), and active threats.

| Tool | Purpose |
| :--- | :--- |
| `list_threats` | List active runtime security alerts detected by Wiz Sensor or Cloud Events. |
| `get_threat` | Detailed analysis of an attack, kill chain stage, process tree, and target asset. |
| `list_detections` | Query detection alerts triggered by behavioral or signature-based rules. |
| `list_cloud_events` | Query audit logs and cloud trail events (e.g. AWS CloudTrail, GCP Audit Logs). |
| `list_sensor_cloud_events` | Query runtime sensor events (process execution, file integrity, network sockets). |
| `list_threat_actors` | Match detected indicators with known threat actor TTPs. |

---

## 11. Secrets Detection & IaC Security
Tools for static code analysis, exposed API keys, and Infrastructure-as-Code checks.

| Tool | Purpose |
| :--- | :--- |
| `list_secret_findings` | List exposed credentials, private keys, and tokens discovered on disks or repositories. |
| `list_secrets_detection_rules` | List rules used for pattern matching secrets. |
| `list_iac_findings` | List misconfigurations found in Terraform, CloudFormation, Helm, or Bicep files. |
| `list_cicd_scans` | List scan outcomes executed during CI/CD build pipelines via the Wiz CLI. |
| `list_code_repositories` | List connected GitHub, GitLab, Bitbucket, and Azure DevOps repositories. |

---

## 12. Automation & System Health
Tools for configuring response workflows, automation rules, and monitoring scanner health.

| Tool | Purpose |
| :--- | :--- |
| `list_automation_rules` | List automated action rules (ticket creation, Slack alert, auto-remediation). |
| `get_automation_rule` | Detailed trigger conditions and action parameters for an automation rule. |
| `list_system_health_issues` | Check scanner errors, connector connectivity issues, and permission gaps. |
| `list_audit_log_entries` | Review administrative actions performed inside the Wiz portal. |
