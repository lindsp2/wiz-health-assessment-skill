# Comprehensive Tenant Health Assessment & Operational Audit

**Prepared for:** [Client Organization / Business Unit]  
**Assessment Date:** [YYYY-MM-DD]  
**Status:** [Draft / Final Review]  
**Evaluator:** [Cloud Security Team / AI Agent]

---

## 1. Executive Summary & Health Scorecard

The purpose of this Tenant Health Assessment is to audit the operational reliability, connector fidelity, scan coverage, and configuration settings of your Wiz environment. Ensuring 100% operational health guarantees that security posture ratings, toxic combination detections, and vulnerability findings maintain maximum fidelity.

### Tenant Health Scorecard

| Health Pillar | Target Benchmark | Current Status | Health Rating | Impact Summary |
| :--- | :---: | :---: | :---: | :--- |
| **1. Cloud Connectors** | 100% Healthy | [__]% Active | 🟢 / 🟡 / 🔴 | [Summary of active connector issues] |
| **2. Workload Scanning** | $\ge 95\%$ | [__]% Success | 🟢 / 🟡 / 🔴 | [Summary of failed scans or snapshot SCP blocks] |
| **3. Data Scanning (DSPM)** | $\ge 90\%$ | [__]% In Scope | 🟢 / 🟡 / 🔴 | [Summary of bucket / volume scanner coverage] |
| **4. Cloud Events (CDR)** | 100% Target Accts | [__]% Covered | 🟢 / 🟡 / 🔴 | [Summary of audit log stream coverage] |
| **5. Automation Rules** | $\ge 98\%$ Action Rate | [__]% Success | 🟢 / 🟡 / 🔴 | [Summary of webhook/ticketing integration health] |
| **6. User Governance** | SSO Enforced / 0 Stale | [__] Total Users | 🟢 / 🟡 / 🔴 | [Summary of stale accounts or local admins] |
| **7. Proactive Monitoring**| 3 Baseline Rules | [__] Rules Active | 🟢 / 🟡 / 🔴 | [Summary of active system health alerting rules] |

*Rating Key: 🟢 Healthy ($\ge 95\%$) | 🟡 Needs Attention ($85\% - 94\%$) | 🔴 Critical Action Required ($< 85\%$)*

---

## 2. Detailed Diagnostic Findings by Pillar

### Pillar 1: Cloud Account & Connector Health
- **Total Connected Accounts:** `[Count]` (AWS: `[N]`, GCP: `[N]`, Azure: `[N]`, K8s: `[N]`)
- **Active System Health Issues:** `[Total Count]` (Critical: `[N]`, High: `[N]`)
- **Key Diagnostic Observations:**
  - `[Observation 1: e.g., AWS Account 123456789012 is failing connector sync due to missing IAM AssumeRole permissions.]`
  - `[Observation 2: e.g., Kubernetes connector in cluster 'prod-east' has an expired token.]`

---

### Pillar 2: Workload Scanning Fidelity
- **Workload Scan Success Rate (24h):** `[N]%` (`[Successful Scans]` / `[Total Scans]`)
- **Unscanned / Discovered Resources:** `[Count]` assets currently discovered but not fully inventoried.
- **Root Cause Analysis:**
  - `[Analysis 1: e.g., Volume snapshot creation blocked by AWS Organization SCP 'DenyCreateSnapshots' in Sub-Account ABC.]`

---

### Pillar 3: Data Security Scanning (DSPM)
- **Bucket Scanning Coverage:** `[N]%` of public / critical object storage buckets in scope.
- **KMS / Key Permissions:** `[N]` key decrypt errors detected during sampling.
- **Key Recommendations:**
  - `[Recommendation: e.g., Expand data scanner scope to include staging S3 buckets and grant 'kms:Decrypt' on alias/customer-key.]`

---

### Pillar 4: Cloud Events (CDR) & Runtime Ingestion
- **Subscriptions / Accounts Ingesting Events:** `[N]` / `[Total Accounts]`
- **Unmonitored Subscriptions:** `[List of key high-value subscriptions lacking CloudTrail / Audit Log routing]`

---

### Pillar 5: Automation Rules & Ticket Routing
- **Active Automation Rules:** `[Count]`
- **24-Hour Execution Success Rate:** `[N]%`
- **Failed Actions:** `[Count]` failed Jira/ServiceNow webhook dispatches.
- **Root Cause:** `[e.g., Jira Service Account API token expired or field mapping error on 'Security Issue' issue type.]`

---

### Pillar 6: User Access & Identity Governance
- **Total Registered Portal Users:** `[Count]` (SSO Managed: `[N]`, Local: `[N]`)
- **Inactive Accounts (>60 days without login):** `[Count]`
- **Global Administrator Count:** `[Count]`
- **Governance Recommendations:**
  - `[e.g., De-provision 4 inactive contractor accounts; enforce SSO for remaining local users.]`

---

### Pillar 7: Proactive System Health Monitoring
- **Recommended Baseline Automations Status:**
  - [ ] Rule 1: Automated Slack / Email alert on new Critical System Health Issues.
  - [ ] Rule 2: Alert when Workload Scan failure rate exceeds 5% in 24 hours.
  - [ ] Rule 3: Notification on Cloud Connector disconnection.

---

## 3. Prioritized Customer Action Plan

The following table details the prioritized technical action items required to achieve 100% tenant health and risk visibility.

| Priority | Pillar / Component | Specific Issue & Root Cause | Recommended Remediation Action | Owner | Target ETA |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **P0** | **Connector (AWS)** | Connector `AWS-Prod-Core` failing sync due to SCP block. | Add Wiz role ARN exemption to AWS Org SCP condition. | Cloud Infra | [YYYY-MM-DD] |
| **P0** | **Workload Scan** | 35 VMs failing snapshot scan in account `Dev-East`. | Attach IAM policy granting `ec2:CreateSnapshot` and `ec2:DeleteSnapshot` to Wiz scanner role. | SecOps | [YYYY-MM-DD] |
| **P1** | **Cloud Events** | 4 production subscriptions missing CloudTrail routing. | Enable CloudTrail event stream integration in Wiz portal. | Cloud Sec | [YYYY-MM-DD] |
| **P1** | **Automation** | Jira integration webhook failing with 401 Unauthorized. | Rotate and update Jira API token in Wiz Integration settings. | IT / DevOps | [YYYY-MM-DD] |
| **P2** | **Governance** | 5 inactive admin accounts older than 90 days. | Remove stale users and re-verify role assignments. | IAM Admin | [YYYY-MM-DD] |
| **P2** | **Monitoring** | No alert configured for connector degradation. | Enable Wiz built-in System Health notification rule. | SecOps | [YYYY-MM-DD] |

---

## 4. Remediation Technical Snippets & Playbooks

### A. AWS SCP Exemption Condition for Wiz Principal
Add the following block to your AWS Organization Service Control Policy to prevent Wiz scanner and connector interruptions:

```json
{
  "Effect": "Deny",
  "Action": [
    "ec2:CreateSnapshot",
    "ec2:DeleteSnapshot",
    "ec2:CreateTags"
  ],
  "Resource": "*",
  "Condition": {
    "ArnNotLike": {
      "aws:PrincipalArn": [
        "arn:aws:iam::*:role/Wiz*",
        "arn:aws:iam::*:role/aws-service-role/*"
      ]
    }
  }
}
```

### B. Verification Query
After applying the fixes above, run the following verification query via the Wiz CLI or API client to verify all connector and scan issues are resolved:

```bash
python3 scripts/wiz_client.py -q 'query VerifyHealth { systemHealthIssues(filterBy: { status: [OPEN] }) { totalCount } }'
```
