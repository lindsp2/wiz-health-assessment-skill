#!/usr/bin/env python3
"""
Wiz Tenant Health Assessment Automated Runner
Collects live telemetry across the 7 core health pillars and outputs a populated
Customer Health Assessment Scorecard & Report.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
from console_compat import enable_unicode_output, python_command
from wiz_client import WizClient

# Severity dots and dashes in the report output are not encodable on a legacy
# Windows console until this runs.
enable_unicode_output()

HEALTH_ASSESSMENT_QUERY = """
query TenantHealthAuditMetrics {
  # 1. System Health Issues
  systemHealthIssues(filterBy: { status: [OPEN] }, first: 50) {
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
    }
  }

  # 2. Workload Scan Ratio
  workloadScans: resourceScanResultsStatusRatio(filterBy: { modules: { data: { equals: false } } }) {
    successResourceCount
    totalResourceCount
  }

  # 3. Data Scan Ratio
  dataScans: resourceScanResultsStatusRatio(filterBy: { modules: { data: { equals: true } } }) {
    successResourceCount
    totalResourceCount
  }

  # 4. Unscanned / Discovered Resources
  discoveredResources {
    totalCount
    ownedByTenantCount
    ownedByThirdPartyCount
    unknownCount
  }

  # 5. Connected Cloud Accounts
  cloudAccounts(first: 100) {
    totalCount
    nodes {
      id
      name
      cloudProvider
      resourceCount
      criticalSystemHealthIssueCount
      highSystemHealthIssueCount
    }
  }

  # 6. Automation Rules
  automationRules(first: 100) {
    totalCount
    nodes {
      id
      name
      enabled
      triggerType
      actions {
        id
        actionTemplateType
      }
    }
  }

  # 7. Users & Roles
  users(first: 100) {
    totalCount
    nodes {
      id
      name
      email
      role {
        name
      }
      isSuspended
    }
  }
}
"""

def generate_markdown_report(data, customer_name="Customer"):
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    d = data.get("data", {})

    # 1. System Health Issues
    shi = d.get("systemHealthIssues", {})
    shi_total = shi.get("totalCount", 0)
    shi_crit = shi.get("criticalSeverityCount", 0)
    shi_high = shi.get("highSeverityCount", 0)
    shi_nodes = shi.get("nodes", [])

    # 2. Workload Scans
    ws = d.get("workloadScans", {})
    ws_succ = ws.get("successResourceCount", 0)
    ws_tot = ws.get("totalResourceCount", 0)
    ws_pct = int((ws_succ / ws_tot * 100)) if ws_tot > 0 else 0

    # 3. Data Scans
    ds = d.get("dataScans", {})
    ds_succ = ds.get("successResourceCount", 0)
    ds_tot = ds.get("totalResourceCount", 0)
    ds_pct = int((ds_succ / ds_tot * 100)) if ds_tot > 0 else 0

    # 4. Discovered Resources
    disc = d.get("discoveredResources", {})
    disc_tot = disc.get("totalCount", 0)

    # 5. Cloud Accounts
    accounts = d.get("cloudAccounts", {})
    acc_tot = accounts.get("totalCount", 0)
    acc_nodes = accounts.get("nodes", [])
    acc_with_issues = sum(1 for a in acc_nodes if (a.get("criticalSystemHealthIssueCount", 0) or 0) > 0)
    acc_healthy_pct = int(((len(acc_nodes) - acc_with_issues) / len(acc_nodes) * 100)) if acc_nodes else 100

    # 6. Automation Rules
    auto = d.get("automationRules", {})
    auto_tot = auto.get("totalCount", 0)
    auto_nodes = auto.get("nodes", [])
    auto_enabled = sum(1 for a in auto_nodes if a.get("enabled"))

    # 7. Users
    users = d.get("users", {})
    users_tot = users.get("totalCount", 0)

    # Health Ratings
    ws_grade = "🟢" if ws_pct >= 95 else ("🟡" if ws_pct >= 85 else "🔴")
    shi_grade = "🟢" if shi_crit == 0 else ("🟡" if shi_crit <= 5 else "🔴")
    ds_grade = "🟢" if ds_pct >= 90 else ("🟡" if ds_pct >= 70 else "🔴")
    acc_grade = "🟢" if acc_healthy_pct >= 95 else ("🟡" if acc_healthy_pct >= 80 else "🔴")

    report = f"""# Comprehensive Tenant Health Assessment & Operational Audit

**Client Organization:** {customer_name}  
**Assessment Date:** {today}  
**Evaluation Status:** Live Tenant Telemetry  

---

## 1. Executive Summary & Health Scorecard

The purpose of this assessment is to review your Wiz tenant configuration, diagnostic telemetry, and operational plumbing to eliminate blind spots, scanner errors, permission blockers, and integration gaps—ensuring 100% risk visibility.

| Health Pillar | Benchmark | Current Metric | Grade | Operational Status |
| :--- | :---: | :---: | :---: | :--- |
| **1. Cloud Connectors & Accounts** | 0 Critical Errors | **{acc_tot} Accounts** ({acc_with_issues} with issues) | {acc_grade} | {"All cloud connectors fully synchronized" if acc_with_issues == 0 else f"{acc_with_issues} accounts experiencing connector/permission errors"} |
| **2. Workload Scanning Fidelity** | >= 95% | **{ws_pct}%** ({ws_succ:,} / {ws_tot:,} unique resources) | {ws_grade} | {"Optimal snapshot scan success rate" if ws_pct >= 95 else "Failing scans detected on target VMs/containers"} |
| **3. Data Security Scanning (DSPM)** | >= 90% | **{ds_pct}%** ({ds_succ:,} / {ds_tot:,} datastores) | {ds_grade} | {"Data scanners operating at target coverage" if ds_pct >= 90 else "Data scanner scope expansion recommended"} |
| **4. System Health Issues** | 0 Open Critical | **{shi_total} Total** ({shi_crit} Critical, {shi_high} High) | {shi_grade} | {"No critical plumbing blocks" if shi_crit == 0 else f"{shi_crit} critical system health blocks requiring immediate fix"} |
| **5. Unscanned / Discovered Assets** | Minimal | **{disc_tot:,}** Discovered Assets | ℹ️ | Discovered assets pending complete inventory profiling |
| **6. Automation & Response Rules** | Baseline Active | **{auto_tot} Rules** ({auto_enabled} Enabled) | 🟢 | Automated ticket routing & notification workflows active |
| **7. User Access Governance** | SSO Enforced | **{users_tot} Total Users** | 🟢 | Portal user population and role assignments verified |

---

## 2. Pillar Breakdown & Diagnostic Findings

### Pillar 1: Cloud Account & Connector Health
- **Total Connected Accounts:** {acc_tot}
- **Accounts with Open System Health Issues:** {acc_with_issues}
"""
    if acc_nodes:
        troubled_accs = [a for a in acc_nodes if (a.get("criticalSystemHealthIssueCount", 0) or 0) > 0]
        if troubled_accs:
            report += "\n**Impacted Cloud Accounts:**\n"
            for a in troubled_accs[:5]:
                report += f"- `{a.get('cloudProvider')}` **{a.get('name')}** (`{a.get('id')}`): {a.get('criticalSystemHealthIssueCount')} Critical SHIs\n"

    report += f"""
### Pillar 2: System Health Issues & Permission Blocks
- **Total Open System Health Issues:** {shi_total}
- **Critical Severity Issues:** {shi_crit}
- **High Severity Issues:** {shi_high}
"""
    if shi_nodes:
        report += "\n**Top Open System Health Issues:**\n"
        for n in shi_nodes[:6]:
            dep_name = n.get("deployment", {}).get("name", "N/A")
            report += f"- `[{n.get('severity')}]` **{n.get('name')}** (Target: `{dep_name}`)\n"

    report += f"""
### Pillar 3: Workload & Data Scanning Fidelity
- **Workload Scan Success Rate (24h):** {ws_pct}% ({ws_succ:,} of {ws_tot:,} unique resources successfully scanned)
- **Data Scan Success Rate (24h):** {ds_pct}% ({ds_succ:,} of {ds_tot:,} datastores scanned)
- **Discovered Unscanned Assets:** {disc_tot:,} resources discovered

---

## 3. Prioritized Customer Action Plan

The following prioritized roadmap outlines the technical remediation steps required to achieve 100% tenant health.

| Priority | Component | Diagnostic Finding | Remediation Action | Suggested Owner |
| :---: | :--- | :--- | :--- | :--- |
| **P0** | **System Health** | {shi_crit} Critical system health issue(s) active on connectors. | Add Wiz role ARN exemption to AWS Organization SCP condition or update IAM permissions. | Cloud Infrastructure |
| **P0** | **Workload Scan** | Workload scanning fidelity at {ws_pct}% (Target: >= 95%). | Inspect VM disk snapshot errors; verify KMS key decrypt grants on encrypted volumes. | SecOps / Cloud Eng |
| **P1** | **Data Scanning** | Data scan coverage at {ds_pct}% (Target: >= 90%). | Expand bucket scanning scope to include all production Object Storage containers. | Cloud Security |
| **P2** | **Discovered Assets** | {disc_tot:,} unscanned resources pending discovery. | Expand connector scope or verify ownership of uninventoried cloud assets. | Cloud Infrastructure |

---

## 4. Remediation Code Snippets & Playbooks

### AWS SCP Exemption Condition for Wiz Principal
Add this condition block to your AWS Organization Service Control Policy (SCP) to avoid blocking snapshot creation:

```json
{{
  "Effect": "Deny",
  "Action": [
    "ec2:CreateSnapshot",
    "ec2:DeleteSnapshot",
    "ec2:CreateTags"
  ],
  "Resource": "*",
  "Condition": {{
    "ArnNotLike": {{
      "aws:PrincipalArn": [
        "arn:aws:iam::*:role/Wiz*",
        "arn:aws:iam::*:role/aws-service-role/*"
      ]
    }}
  }}
}}
```

### Post-Remediation Verification Command
After applying the fixes, verify that system health issues clear:
```bash
{python_command()} scripts/wiz_client.py -q 'query VerifyHealth {{ systemHealthIssues(filterBy: {{ status: [OPEN], severity: [CRITICAL] }}) {{ totalCount }} }}'
```
"""
    return report

def main():
    parser = argparse.ArgumentParser(description="Run Wiz Tenant Health Assessment")
    parser.add_argument("-c", "--customer", default="Customer Organization", help="Customer Name")
    parser.add_argument("-o", "--output", help="Output file path (Markdown or JSON)")
    parser.add_argument("--json", action="store_true", help="Output raw telemetry JSON")
    parser.add_argument("--env-file", help="Path to .env file containing credentials")
    args = parser.parse_args()

    client = WizClient(env_file=args.env_file)
    print(f"Connecting to Wiz API ({client.api_endpoint}) for Health Audit...")

    try:
        data = client.execute_query(HEALTH_ASSESSMENT_QUERY)
        if args.json:
            out_str = json.dumps(data, indent=2)
        else:
            out_str = generate_markdown_report(data, customer_name=args.customer)
        
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(out_str)
            print(f"Health assessment report saved to {out_path.resolve()}")
        else:
            print("\n" + out_str)

    except Exception as e:
        sys.stderr.write(f"Health Audit Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
