# Wiz Tenant Health Assessment — Execution & Remediation Guide

This guide provides the complete methodology for conducting a comprehensive, customer-facing **Wiz Tenant Health Assessment**.

---

## 1. Objectives & Outcomes

### Goal
Review a customer's Wiz tenant configuration, diagnostic telemetry, and operational plumbing to identify and resolve blind spots, scanner errors, permission blockers, and integration gaps—ensuring 100% risk visibility.

### Key Customer Outcomes
1. **Zero Visibility Blind Spots:** Unblock failing connectors, workload scanners, and data scanners so the Security Graph reflects all cloud assets.
2. **Operational Reliability:** Ensure automated ticket routing, event ingestion, and posture scans maintain >95% success rates.
3. **Actionable Remediation Roadmap:** A prioritized action plan with clear root causes, exact fix snippets (IAM/SCP policies), and agreed completion ETAs.

---

## 2. The 7 Core Health Pillars & Benchmarks

| Pillar | Diagnostic Focus | Healthy Benchmark | Warning / Critical Trigger |
| :--- | :--- | :--- | :--- |
| **1. Cloud Connectors** | AWS, GCP, Azure, K8s, and Outpost connector sync status & permissions. | 100% Active / Healthy | Any `DISCONNECTED`, `ERROR`, or permission failure. |
| **2. Workload Scanning** | VM & container disk snapshot scanning success rate (24h window). | $\ge 95\%$ Success Rate | $< 90\%$ Success Rate or high snapshot permission errors. |
| **3. Data Scanning (DSPM)** | Cloud bucket & non-OS volume scanning coverage and KMS permissions. | $\ge 90\%$ Configured Scope | Unscanned public buckets or KMS access denied. |
| **4. Cloud Events (CDR)** | Audit log ingestion coverage across cloud accounts/subscriptions. | $100\%$ Target Accounts | High-volume accounts missing Cloud Event ingestion. |
| **5. Automation Rules** | Action execution rates (webhooks, Jira/ServiceNow, Slack, PagerDuty). | $\ge 98\%$ Action Success | Any recurring action execution failures (4xx/5xx). |
| **6. Access & Governance** | Wiz portal user logins, inactive accounts, SSO, and admin roles. | SSO Enforced, 0 Stale Admins | Inactive admin accounts (>60d) or local non-SSO logins. |
| **7. Health Monitoring** | Automated detection rules catching scanner & connector degradation. | Baseline Rules Active | No alerting rules for system health issue spikes. |

---

## 3. Pillar-by-Pillar Audit Queries & Diagnostics

### Pillar 1: Connector & Ingestion Health
- **MCP Tool:** `list_connectors`, `list_system_health_issues_grouped_by_deployment`, `list_system_health_issues`
- **GraphQL Query:**
  ```graphql
  query ConnectorHealthAudit {
    systemHealthIssues(
      filterBy: { status: [OPEN], severity: [CRITICAL, HIGH] }
      first: 50
    ) {
      totalCount
      criticalSeverityCount
      highSeverityCount
      nodes {
        id
        name
        severity
        deployment {
          id
          name
        }
        sourceSnapshot {
          id
          name
          type
        }
        details {
          ... on SystemHealthIssuePermissionsCategoryTypeDetails {
            principal {
              id
              type
              providerUniqueId
            }
          }
        }
      }
    }
  }
  ```
- **Common Root Causes & Fixes:**
  - *AWS Service Control Policy (SCP) Denials:* The customer's AWS Organization SCP blocks `AssumeRole` or snapshot creation.
    - **Fix:** Add Wiz role ARN to SCP `Condition` exclusions:
      ```json
      "Condition": {
        "ArnNotLike": {
          "aws:PrincipalArn": ["arn:aws:iam::*:role/Wiz*"]
        }
      }
      ```
  - *KMS Key Decryption Failures:* Missing `kms:Decrypt` and `kms:DescribeKey` on customer-managed encryption keys (CMK).

---

### Pillar 2: Workload Scanning Fidelity
- **MCP Tool:** `list_cloud_resources_grouped`, `get_workload_scan_status`
- **GraphQL Queries:**
  1. *Scan Success Ratio (Widget parity):*
     ```graphql
     query WorkloadScanRatio {
       resourceScanResultsStatusRatio(filterBy: { modules: { data: { equals: false } } }) {
         successResourceCount
         totalResourceCount
       }
     }
     ```
     $$\text{Workload Coverage \%} = \left\lfloor \frac{\text{successResourceCount}}{\text{totalResourceCount}} \times 100 \right\rfloor$$

  2. *Unscanned Resources Discovery (`U_RES`):*
     ```graphql
     query UnscannedResourcesCount {
       discoveredResources {
         totalCount
         ownedByTenantCount
         ownedByThirdPartyCount
         unknownCount
       }
     }
     ```
- **Common Root Causes & Fixes:**
  - *DenyCreateSnapshots SCP:* Customer policy blocks volume snapshots in specific sub-accounts.
  - *Unsupported OS / Encrypted Non-Standard Filesystems:* Inspect scan failure logs for unmounted LVM/LUKS volumes.

---

### Pillar 3: Data Security Scanning (DSPM)
- **MCP Tool:** `list_datastores`, `list_data_findings_grouped`, `get_data_scan_results`
- **GraphQL Query:**
  ```graphql
  query DataScanRatio {
    resourceScanResultsStatusRatio(filterBy: { modules: { data: { equals: true } } }) {
      successResourceCount
      totalResourceCount
    }
  }
  ```
- **Diagnostic Focus:** Ensure public buckets and crown-jewel databases are within scanning scope and that scanner roles have read-only sampling rights.

---

### Pillar 4: Cloud Events Ingestion Coverage
- **MCP Tool:** `list_cloud_events_grouped`, `list_log_ingestion_coverage`
- **GraphQL Query:**
  ```graphql
  query CloudEventCoverage {
    subscriptions(first: 100) {
      totalCount
      nodes {
        id
        name
        cloudProvider
        isEventIngestionEnabled
      }
    }
  }
  ```
- **Remediation:** Enable CloudTrail / GCP Audit Log / Azure Activity Log stream forwarding on all production subscriptions.

---

### Pillar 5: Automation Rules Health
- **MCP Tool:** `list_automation_rules`, `get_automation_rule`
- **GraphQL Query:**
  ```graphql
  query AutomationRulesAudit {
    automationRules(first: 100) {
      totalCount
      nodes {
        id
        name
        enabled
        triggerType
        triggerSource
        actions {
          type
        }
      }
    }
  }
  ```
- **Diagnostic Focus:** Verify that high-priority rules (e.g. Critical Issue $\rightarrow$ Jira Ticket) are enabled and have no webhook delivery failures in the audit log.

---

### Pillar 6: Access & Governance Review
- **MCP Tool:** `list_users`, `get_users_usage`
- **GraphQL Query:**
  ```graphql
  query AccessReview {
    users(first: 100) {
      totalCount
      nodes {
        id
        name
        email
        role {
          name
        }
        lastLoginAt
        isSuspended
      }
    }
  }
  ```
- **Remediation:** Remove inactive users (>90 days without login), convert local email/password accounts to SSO/SAML, and audit Global Admin assignments.

---

### Pillar 7: Baseline System Health Monitoring
- **Recommended Minimum Automation Rules:**
  1. *Rule 1 (System Health Alert):* Trigger on new `CRITICAL` or `HIGH` `SystemHealthIssue` $\rightarrow$ Send alert to Cloud SecOps channel.
  2. *Rule 2 (Workload Scan Failure Alert):* Trigger when workload scan fails on production tags $\rightarrow$ Notify Infrastructure Owner.
  3. *Rule 3 (Connector Disconnect):* Trigger immediately if connector status changes to `ERROR`.

---

## 4. Customer Deliverable Format

When presenting the health assessment, always output:
1. **Executive Scorecard Table** (Current Status, Health Grade, Trend).
2. **Pillar-by-Pillar Detailed Findings & Diagnostic Observations**.
3. **Prioritized Action Plan Matrix** (Priority, Root Cause, Remediation Steps, Owner, Target ETA).
