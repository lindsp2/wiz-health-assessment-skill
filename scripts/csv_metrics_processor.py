"""
CSV Metrics Processor for Wiz Health Assessment Suite.

Provides:
- export_metrics_to_csv: Exports populated metrics to a structured CSV file.
- generate_intake_template_csv: Generates a blank, annotated intake CSV to request from customers.
- load_metrics_from_csv: Loads and normalizes metrics from a customer-filled CSV for deck generation.
"""

import csv
import io
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


METRIC_DEFINITIONS: List[Dict[str, Any]] = [
    # --- Header & General ---
    {"var": "CUSTOMER", "category": "General", "name": "Customer Name", "slide": "1, 14", "desc": "Customer organization or tenant name", "default": "Customer"},
    {"var": "TAM_NAME", "category": "General", "name": "Technical Account Manager", "slide": "1", "desc": "Assigned Wiz TAM / Architect", "default": ""},
    {"var": "DATE", "category": "General", "name": "Assessment Date", "slide": "1, 14", "desc": "Date of Health Assessment (YYYY-MM-DD)", "default": ""},

    # --- Cloud Architecture & AI Footprint (Slide 3) ---
    {"var": "C_AWS", "category": "Cloud Architecture", "name": "AWS Accounts Count", "slide": "3", "desc": "Total connected AWS accounts", "default": "0"},
    {"var": "C_AZ", "category": "Cloud Architecture", "name": "Azure Subscriptions Count", "slide": "3", "desc": "Total connected Azure subscriptions", "default": "0"},
    {"var": "C_GCP", "category": "Cloud Architecture", "name": "GCP Projects Count", "slide": "3", "desc": "Total connected GCP projects", "default": "0"},
    {"var": "C_OTH", "category": "Cloud Architecture", "name": "Other Cloud Accounts Count", "slide": "3", "desc": "OCI, Alibaba, etc.", "default": "0"},
    {"var": "C_OTH_NAMES", "category": "Cloud Architecture", "name": "Other Cloud Provider Names", "slide": "3", "desc": "Names of other cloud providers", "default": ""},
    {"var": "CON_TOT", "category": "Cloud Architecture", "name": "Total Connected Connectors", "slide": "3", "desc": "Total connectors across all types", "default": "0"},
    {"var": "AI_AGENTS_COUNT", "category": "AI Footprint", "name": "AI Agents Discovered", "slide": "3", "desc": "Active AI Agent entities", "default": "0"},
    {"var": "AI_MODELS_COUNT", "category": "AI Footprint", "name": "AI Models Discovered", "slide": "3", "desc": "Active AI Model entities", "default": "0"},
    {"var": "AI_GUARDRAILS_COUNT", "category": "AI Footprint", "name": "AI Guardrails Discovered", "slide": "3", "desc": "Active AI Guardrail entities", "default": "0"},
    {"var": "AI_MCP_SERVERS_COUNT", "category": "AI Footprint", "name": "MCP Servers Discovered", "slide": "3", "desc": "Model Context Protocol servers", "default": "0"},
    {"var": "AI_PIPELINES_COUNT", "category": "AI Footprint", "name": "AI Pipelines Discovered", "slide": "3", "desc": "Active AI Pipelines", "default": "0"},
    {"var": "AI_DATASETS_COUNT", "category": "AI Footprint", "name": "AI Datasets Discovered", "slide": "3", "desc": "AI Datastores / Training sets", "default": "0"},
    {"var": "AI_TECHNOLOGIES_COUNT", "category": "AI Footprint", "name": "AI Technologies Count", "slide": "3", "desc": "AI libraries & frameworks (PyTorch, TensorFlow, etc.)", "default": "0"},
    {"var": "AI_CA_COUNT", "category": "AI Footprint", "name": "AI Coding Agents (IDEs)", "slide": "3", "desc": "Developer IDEs with AI assistants", "default": "0"},
    {"var": "AI_CODE_REPOS_COUNT", "category": "AI Footprint", "name": "AI Code Repositories", "slide": "3", "desc": "VCS repositories using AI technologies", "default": "0"},
    {"var": "AI_WORKLOADS_COUNT", "category": "AI Footprint", "name": "AI Running Workloads", "slide": "3", "desc": "Workloads executing AI models or pipelines", "default": "0"},

    # --- Workloads & Compute Inventory (Slide 3 & 4) ---
    {"var": "WS_T", "category": "Workload Inventory", "name": "Total Compute Workload Scans", "slide": "4", "desc": "Total compute workload scans evaluated", "default": "0"},
    {"var": "WS_F", "category": "Workload Inventory", "name": "Workload Scans Failed", "slide": "4", "desc": "Failed workload scans", "default": "0"},
    {"var": "WS_SK", "category": "Workload Inventory", "name": "Workload Scans Skipped", "slide": "4", "desc": "Skipped workload scans", "default": "0"},
    {"var": "WS_P", "category": "Workload Inventory", "name": "Workload Scan Success Ratio %", "slide": "4", "desc": "Success ratio for compute workload scans", "default": "100%"},
    {"var": "SERVERLESS_FN_COUNT", "category": "Workload Inventory", "name": "Serverless Functions Count", "slide": "3", "desc": "Lambda, Azure Functions, Cloud Run", "default": "0"},
    {"var": "SERVERLESS_CT_COUNT", "category": "Workload Inventory", "name": "Serverless Containers Count", "slide": "3", "desc": "Fargate, Cloud Run container instances", "default": "0"},
    {"var": "R_TOT", "category": "Workload Inventory", "name": "Container Registries Count", "slide": "3, 4", "desc": "ECR, ACR, GCR, GAR registries", "default": "0"},
    {"var": "K8S", "category": "Workload Inventory", "name": "Kubernetes Clusters Count", "slide": "3, 4", "desc": "Total managed & self-hosted K8s clusters", "default": "0"},
    {"var": "L_SE", "category": "Connectors & Agents", "name": "Wiz Runtime Sensors", "slide": "3, 4", "desc": "Active Wiz Runtime Sensor instances", "default": "0"},
    {"var": "CON_WOS", "category": "Connectors & Agents", "name": "Wiz Sensor Workloads", "slide": "3", "desc": "Workloads with Wiz Runtime Sensor installed", "default": "0"},
    {"var": "CON_K8S", "category": "Connectors & Agents", "name": "Kubernetes Connectors Count", "slide": "3", "desc": "Installed K8s connectors", "default": "0"},
    {"var": "CON_VCS", "category": "Connectors & Agents", "name": "VCS Connectors Count", "slide": "3", "desc": "GitHub, GitLab, Bitbucket connectors", "default": "0"},
    {"var": "CON_R", "category": "Connectors & Agents", "name": "Registry Connectors Count", "slide": "3", "desc": "Active container registry connectors", "default": "0"},
    {"var": "AE_TOT", "category": "Attack Surface Management", "name": "ASM Estimated Workloads", "slide": "11", "desc": "Calculated ASM compute workload units", "default": "0"},

    # --- System Health & Scans Snapshot (Slide 5) ---
    {"var": "SHI_C", "category": "System Health", "name": "Open Critical SHIs", "slide": "5", "desc": "Open Critical System Health Issues", "default": "0"},
    {"var": "SHI_H", "category": "System Health", "name": "Open High SHIs", "slide": "5", "desc": "Open High System Health Issues", "default": "0"},
    {"var": "SHI_R_C", "category": "System Health", "name": "Resolved Critical SHIs (30d)", "slide": "5", "desc": "Resolved Critical SHIs in past 30 days", "default": "0"},
    {"var": "SHI_R_H", "category": "System Health", "name": "Resolved High SHIs (30d)", "slide": "5", "desc": "Resolved High SHIs in past 30 days", "default": "0"},
    {"var": "SHI_O", "category": "System Health Breakdown", "name": "SHI - Outposts & Outpost Clusters", "slide": "5", "desc": "Open Crit+High SHIs on Outposts", "default": "0"},
    {"var": "SHI_CC", "category": "System Health Breakdown", "name": "SHI - Cloud Connectors", "slide": "5", "desc": "Open Crit+High SHIs on Cloud Connectors", "default": "0"},
    {"var": "SHI_I", "category": "System Health Breakdown", "name": "SHI - Integrations & Service Accounts", "slide": "5", "desc": "Open Crit+High SHIs on Integrations", "default": "0"},
    {"var": "SHI_RC", "category": "System Health Breakdown", "name": "SHI - Registry Connectors", "slide": "5", "desc": "Open Crit+High SHIs on Container Registries", "default": "0"},
    {"var": "SHI_KC", "category": "System Health Breakdown", "name": "SHI - Kubernetes Connectors", "slide": "5", "desc": "Open Crit+High SHIs on K8s Connectors", "default": "0"},
    {"var": "SHI_VCS", "category": "System Health Breakdown", "name": "SHI - VCS & CI/CD Connectors", "slide": "5", "desc": "Open Crit+High SHIs on Version Control", "default": "0"},
    {"var": "SHI_B", "category": "System Health Breakdown", "name": "SHI - Brokers & CLI", "slide": "5", "desc": "Open Crit+High SHIs on Brokers / CLI", "default": "0"},
    {"var": "NON_T", "category": "Non-OS Disk Scans", "name": "Non-OS Disk Total Scans", "slide": "5", "desc": "Total Non-OS disk scans evaluated", "default": "0"},
    {"var": "NON_F", "category": "Non-OS Disk Scans", "name": "Non-OS Disk Failed Scans", "slide": "5", "desc": "Failed Non-OS disk scans", "default": "0"},
    {"var": "NON_S", "category": "Non-OS Disk Scans", "name": "Non-OS Disk Skipped Scans", "slide": "5", "desc": "Skipped Non-OS disk scans", "default": "0"},
    {"var": "NON_C", "category": "Non-OS Disk Scans", "name": "Non-OS Disk Scan Coverage %", "slide": "5", "desc": "Coverage percentage (e.g. 35%)", "default": "0%"},
    {"var": "RCI_T", "category": "Container Image Scans", "name": "Container Image Total Scans", "slide": "5", "desc": "Total registry container image workload scans", "default": "0"},
    {"var": "RCI_F", "category": "Container Image Scans", "name": "Container Image Failed Scans", "slide": "5", "desc": "Failed container image scans", "default": "0"},
    {"var": "RCI_S", "category": "Container Image Scans", "name": "Container Image Skipped Scans", "slide": "5", "desc": "Skipped container image scans", "default": "0"},
    {"var": "RCI_C", "category": "Container Image Scans", "name": "Container Image Scan Coverage %", "slide": "5", "desc": "Coverage percentage (e.g. 16%)", "default": "0%"},
    {"var": "VMI_T", "category": "VM Image Scans", "name": "VM Image Total Scans", "slide": "5", "desc": "Total VM image workload scans", "default": "0"},
    {"var": "VMI_F", "category": "VM Image Scans", "name": "VM Image Failed Scans", "slide": "5", "desc": "Failed VM image scans", "default": "0"},
    {"var": "VMI_S", "category": "VM Image Scans", "name": "VM Image Skipped Scans", "slide": "5", "desc": "Skipped VM image scans", "default": "0"},
    {"var": "VMI_C", "category": "VM Image Scans", "name": "VM Image Scan Coverage %", "slide": "5", "desc": "Coverage percentage (e.g. 0%)", "default": "0%"},
    {"var": "DS_T", "category": "Data Security (DSPM) Scans", "name": "DSPM Total Scans", "slide": "5", "desc": "Total DSPM data security scans", "default": "0"},
    {"var": "DS_F", "category": "Data Security (DSPM) Scans", "name": "DSPM Failed Scans", "slide": "5", "desc": "Failed DSPM scans", "default": "0"},
    {"var": "DS_SK", "category": "Data Security (DSPM) Scans", "name": "DSPM Skipped Scans", "slide": "5", "desc": "Skipped DSPM scans", "default": "0"},
    {"var": "DS_P", "category": "Data Security (DSPM) Scans", "name": "DSPM Scan Coverage %", "slide": "5", "desc": "DSPM coverage percentage (e.g. 81%)", "default": "0%"},
    {"var": "DS_B", "category": "DSPM Breakdown", "name": "Storage Buckets Scanned", "slide": "5", "desc": "S3, GCS, Azure Blob buckets", "default": "0"},
    {"var": "DS_PD", "category": "DSPM Breakdown", "name": "PaaS Databases Scanned", "slide": "5", "desc": "RDS, Cloud SQL, CosmosDB", "default": "0"},
    {"var": "DS_DW", "category": "DSPM Breakdown", "name": "Data Warehouses Scanned", "slide": "5", "desc": "Snowflake, BigQuery, Redshift", "default": "0"},
    {"var": "DS_VD", "category": "DSPM Breakdown", "name": "Virtual Drives Scanned", "slide": "5", "desc": "EBS, Google Persistent Disks", "default": "0"},
    {"var": "DS_AI", "category": "DSPM Breakdown", "name": "AI Datastores Scanned", "slide": "5", "desc": "AI datasets / Knowledge bases", "default": "0"},
    {"var": "DS_FSS", "category": "DSPM Breakdown", "name": "File System Services Scanned", "slide": "5", "desc": "EFS, Azure Files, NetApp", "default": "0"},

    # --- Kubernetes Posture (Slide 6) ---
    {"var": "KC_C_T", "category": "Kubernetes", "name": "Total K8s Clusters", "slide": "6", "desc": "Total managed & self-hosted K8s clusters", "default": "0"},
    {"var": "KC_C_C", "category": "Kubernetes", "name": "Total K8s Containers", "slide": "6", "desc": "Total running container instances", "default": "0"},
    {"var": "KC_WC", "category": "Kubernetes", "name": "Clusters with Connector Deployed", "slide": "6", "desc": "Clusters with active Wiz K8s connector", "default": "0"},
    {"var": "KC_WA", "category": "Kubernetes", "name": "Clusters with Audit Log Ingestion", "slide": "6", "desc": "Clusters collecting K8s audit logs", "default": "0"},
    {"var": "KC_WS", "category": "Kubernetes", "name": "Clusters with Runtime Sensor", "slide": "6", "desc": "Clusters with Wiz Runtime Sensor daemonset", "default": "0"},
    {"var": "KC_AC", "category": "Kubernetes", "name": "Clusters with Admission Controller", "slide": "6", "desc": "Clusters with admission controller webhook", "default": "0"},
    {"var": "KG_NC", "category": "Kubernetes Gaps", "name": "Clusters Missing Connector", "slide": "6", "desc": "Unmanaged / unmonitored clusters", "default": "0"},
    {"var": "KG_NA", "category": "Kubernetes Gaps", "name": "Clusters Missing Audit Log Ingestion", "slide": "6", "desc": "Missing audit log ingestion", "default": "0"},
    {"var": "KG_NS", "category": "Kubernetes Gaps", "name": "Clusters Missing Runtime Sensor", "slide": "6", "desc": "Missing runtime threat detection", "default": "0"},
    {"var": "KG_AC", "category": "Kubernetes Gaps", "name": "Clusters Missing Admission Controller", "slide": "6", "desc": "Missing admission control enforcement", "default": "0"},

    # --- Top Controls by Issue Count (Slide 11) ---
    {"var": "CI_CONTROL_1", "category": "Top Controls", "name": "Top Critical Control 1 Name", "slide": "11", "desc": "Control with most critical issues", "default": ""},
    {"var": "CI_CBC_1", "category": "Top Controls", "name": "Top Critical Control 1 Count", "slide": "11", "desc": "Issue count for top critical control 1", "default": "0"},
    {"var": "CI_CONTROL_2", "category": "Top Controls", "name": "Top Critical Control 2 Name", "slide": "11", "desc": "Control with second most critical issues", "default": ""},
    {"var": "CI_CBC_2", "category": "Top Controls", "name": "Top Critical Control 2 Count", "slide": "11", "desc": "Issue count for top critical control 2", "default": "0"},
    {"var": "CI_CONTROL_3", "category": "Top Controls", "name": "Top Critical Control 3 Name", "slide": "11", "desc": "Control with third most critical issues", "default": ""},
    {"var": "CI_CBC_3", "category": "Top Controls", "name": "Top Critical Control 3 Count", "slide": "11", "desc": "Issue count for top critical control 3", "default": "0"},
    {"var": "HI_CONTROL_1", "category": "Top Controls", "name": "Top High Control 1 Name", "slide": "11", "desc": "Control with most high issues", "default": ""},
    {"var": "HI_CBC_1", "category": "Top Controls", "name": "Top High Control 1 Count", "slide": "11", "desc": "Issue count for top high control 1", "default": "0"},
    {"var": "HI_CONTROL_2", "category": "Top Controls", "name": "Top High Control 2 Name", "slide": "11", "desc": "Control with second most high issues", "default": ""},
    {"var": "HI_CBC_2", "category": "Top Controls", "name": "Top High Control 2 Count", "slide": "11", "desc": "Issue count for top high control 2", "default": "0"},
    {"var": "HI_CONTROL_3", "category": "Top Controls", "name": "Top High Control 3 Name", "slide": "11", "desc": "Control with third most high issues", "default": ""},
    {"var": "HI_CBC_3", "category": "Top Controls", "name": "Top High Control 3 Count", "slide": "11", "desc": "Issue count for top high control 3", "default": "0"},

    # --- Cloud Security Posture Snapshot (Slide 12) ---
    {"var": "SS", "category": "Security Posture", "name": "Current Security Score", "slide": "12", "desc": "Wiz Security Score (0-100%)", "default": "100"},
    {"var": "s1d", "category": "Security Posture", "name": "90-Day Security Score Trend", "slide": "12", "desc": "Score change (+/- %)", "default": "+0%"},
    {"var": "SP", "category": "Security Posture", "name": "Industry Benchmark Score", "slide": "12", "desc": "Peer benchmark security score (%)", "default": "80%"},
    {"var": "SG", "category": "Security Posture", "name": "Security Score Gap", "slide": "12", "desc": "Gap between current score and benchmark (%)", "default": "0%"},
    {"var": "SS_I", "category": "Security Posture", "name": "Industry Benchmark Name", "slide": "12", "desc": "e.g. Technology, Financial Services, Healthcare", "default": "Technology"},
    {"var": "OC", "category": "Security Posture", "name": "Open Critical Issues", "slide": "12", "desc": "Total active critical severity issues", "default": "0"},
    {"var": "RC", "category": "Security Posture", "name": "Resolved Critical Issues (90d)", "slide": "12", "desc": "Resolved critical issues in past 90 days", "default": "0"},
    {"var": "OH", "category": "Security Posture", "name": "Open High Issues", "slide": "12", "desc": "Total active high severity issues", "default": "0"},
    {"var": "RH", "category": "Security Posture", "name": "Resolved High Issues (90d)", "slide": "12", "desc": "Resolved high issues in past 90 days", "default": "0"},
    {"var": "RJ", "category": "Security Posture", "name": "Ignored Issues Count", "slide": "12", "desc": "Total issues in rejected / ignored status", "default": "0"},
    {"var": "OT", "category": "Threats & Runtime", "name": "Open Threats Count", "slide": "12", "desc": "Open runtime threat detections", "default": "0"},
    {"var": "RT", "category": "Threats & Runtime", "name": "Resolved Threats Count (90d)", "slide": "12", "desc": "Resolved threats in past 90 days", "default": "0"},
    {"var": "MTTR_O", "category": "Threats & Runtime", "name": "Mean Time to Remediate (MTTR)", "slide": "12", "desc": "Average MTTR in days for criticals/threats", "default": "0"},
    {"var": "AVG_AGEC", "category": "Threats & Runtime", "name": "Critical Issues Average Age", "slide": "12", "desc": "Average age of open critical issues (days)", "default": "0"},
    {"var": "AVG_AGEH", "category": "Threats & Runtime", "name": "High Issues Average Age", "slide": "12", "desc": "Average age of open high issues (days)", "default": "0"},
    {"var": "AI_SF", "category": "AI Security Findings", "name": "AI Security Findings Count", "slide": "12", "desc": "Active AI security posture findings", "default": "0"},
    {"var": "AI_MF", "category": "AI Security Findings", "name": "AI Misconfiguration Findings Count", "slide": "12", "desc": "Configuration findings for AI framework (wct-id-1998)", "default": "0"},
    {"var": "AI_IF", "category": "AI Security Findings", "name": "AI Inventory Findings Count", "slide": "12", "desc": "Inventory findings for AI models & MCP servers", "default": "0"},

    # --- Licenses & Add-ons (Slide 14) ---
    {"var": "L_CW", "category": "Licenses", "name": "Cloud Workload Protection License", "slide": "14", "desc": "Active / Billable unit count", "default": "Active"},
    {"var": "L_CO", "category": "Licenses", "name": "Wiz Code License", "slide": "14", "desc": "Active / Inactive", "default": "Active"},
    {"var": "L_DE", "category": "Licenses", "name": "Wiz Defend License", "slide": "14", "desc": "Active / Inactive", "default": "Active"},
    {"var": "L_CL_PCT", "category": "Licenses", "name": "Container Lifecycle Coverage %", "slide": "14", "desc": "Container lifecycle scanning coverage", "default": "100%"},

    # --- Potential Integrations (Slide 15) ---
    {"var": "PI_T1_N", "category": "Potential Integrations", "name": "Top Integration 1 Name", "slide": "15", "desc": "Most active cloud service technology", "default": "AWS IAM"},
    {"var": "PI_T1_D", "category": "Potential Integrations", "name": "Top Integration 1 Timeline Date", "slide": "15", "desc": "Last activity date (YYYY-MM-DD)", "default": ""},
    {"var": "PI_T1_NT", "category": "Potential Integrations", "name": "Top Integration 1 Total Instances", "slide": "15", "desc": "Total discovered service accounts", "default": "0"},
    {"var": "PI_T1_NS", "category": "Potential Integrations", "name": "Top Integration 1 External Owners", "slide": "15", "desc": "Accounts with external owners", "default": "0"},
    {"var": "PI_T2_N", "category": "Potential Integrations", "name": "Top Integration 2 Name", "slide": "15", "desc": "Second most active technology", "default": ""},
    {"var": "PI_T2_D", "category": "Potential Integrations", "name": "Top Integration 2 Timeline Date", "slide": "15", "desc": "Last activity date", "default": ""},
    {"var": "PI_T2_NT", "category": "Potential Integrations", "name": "Top Integration 2 Total Instances", "slide": "15", "desc": "Total discovered instances", "default": "0"},
    {"var": "PI_T2_NS", "category": "Potential Integrations", "name": "Top Integration 2 External Owners", "slide": "15", "desc": "Accounts with external owners", "default": "0"},
    {"var": "PI_T3_N", "category": "Potential Integrations", "name": "Top Integration 3 Name", "slide": "15", "desc": "Third most active technology", "default": ""},
    {"var": "PI_T3_D", "category": "Potential Integrations", "name": "Top Integration 3 Timeline Date", "slide": "15", "desc": "Last activity date", "default": ""},
    {"var": "PI_T3_NT", "category": "Potential Integrations", "name": "Top Integration 3 Total Instances", "slide": "15", "desc": "Total discovered instances", "default": "0"},
    {"var": "PI_T3_NS", "category": "Potential Integrations", "name": "Top Integration 3 External Owners", "slide": "15", "desc": "Accounts with external owners", "default": "0"},
]


def export_metrics_to_csv(
    variables: Dict[str, Any],
    output_path: str,
    customer_name: str = "Customer",
) -> str:
    """
    Exports populated variables to a clean, well-formatted CSV file.
    Includes human-readable categories, metric titles, values, and slide locations.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    val_map = {}
    for k, v in variables.items():
        if isinstance(v, dict):
            val_map[k] = str(v.get("value", ""))
        else:
            val_map[k] = str(v if v is not None else "")

    rows = []
    seen_vars = set()

    for defn in METRIC_DEFINITIONS:
        var_key = defn["var"]
        seen_vars.add(var_key)
        val = val_map.get(var_key, defn.get("default", ""))
        rows.append({
            "Category": defn["category"],
            "Variable": f"{{{{{var_key}}}}}",
            "Metric Name": defn["name"],
            "Value": val,
            "Slide": defn["slide"],
            "Description": defn["desc"],
        })

    # Include remaining variables (e.g. Preview Hub, Scanner toggles, etc.)
    for k, v in sorted(val_map.items()):
        if k in seen_vars or k.startswith("_"):
            continue
        category = "Other"
        slide = "General"
        if k.startswith("PREVIEW_"):
            category = "Preview Hub"
            slide = "16-17"
        elif k.startswith("DSS_"):
            category = "Scanner Configurations"
            slide = "7-10"
        elif k.startswith("F_"):
            category = "Custom Frameworks"
            slide = "7"
        elif k.startswith("IA_") or k.startswith("IR_"):
            category = "Integrations Activity"
            slide = "15"
        
        rows.append({
            "Category": category,
            "Variable": f"{{{{{k}}}}}",
            "Metric Name": k.replace("_", " ").title(),
            "Value": v,
            "Slide": slide,
            "Description": f"Auto-extracted metric for {k}",
        })

    fieldnames = ["Category", "Variable", "Metric Name", "Value", "Slide", "Description"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def generate_intake_template_csv(output_path: str) -> str:
    """
    Generates a blank customer intake CSV template with clear guidance
    for customers or TAMs to fill in values manually.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["Category", "Variable", "Metric Name", "Value", "Slide", "Description"]

    rows = []
    for defn in METRIC_DEFINITIONS:
        rows.append({
            "Category": defn["category"],
            "Variable": f"{{{{{defn['var']}}}}}",
            "Metric Name": defn["name"],
            "Value": "",  # Blank for customer to populate
            "Slide": defn["slide"],
            "Description": defn["desc"],
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def load_metrics_from_csv(csv_path: str) -> Dict[str, Dict[str, str]]:
    """
    Reads a customer-filled CSV file and extracts variables into a merged dictionary
    compatible with build_replacement_requests and PowerPoint / Google Slides builders.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input CSV file not found: {csv_path}")

    merged = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            var_raw = (row.get("Variable") or row.get("variable") or row.get("Token") or "").strip()
            val = (row.get("Value") or row.get("value") or "").strip()
            
            # Normalize token name (strip {{ and }})
            clean_var = re.sub(r'[\{\}\s]', '', var_raw)
            if not clean_var:
                continue

            merged[clean_var] = {
                "variable": clean_var,
                "value": val,
                "source": "CSV"
            }

    # Automatically compute missing scan coverage percentages if raw totals exist
    def auto_calc_pct(total_k, succ_k, fail_k, skip_k, pct_k):
        if pct_k not in merged or not merged[pct_k]["value"]:
            try:
                t = int(merged.get(total_k, {}).get("value", "0").replace(",", ""))
                s = int(merged.get(succ_k, {}).get("value", "0").replace(",", ""))
                f = int(merged.get(fail_k, {}).get("value", "0").replace(",", ""))
                sk = int(merged.get(skip_k, {}).get("value", "0").replace(",", ""))
                
                # If succeeded not given, infer as t - f - sk
                if s == 0 and t > 0:
                    s = max(0, t - f - sk)
                
                if t > 0:
                    pct = f"{int(math.floor(s / t * 100))}%"
                    merged[pct_k] = {"variable": pct_k, "value": pct, "source": "DERIVED_CSV"}
            except Exception:
                pass

    auto_calc_pct("NON_T", "NON_SUCC", "NON_F", "NON_S", "NON_C")
    auto_calc_pct("RCI_T", "RCI_SUCC", "RCI_F", "RCI_S", "RCI_C")
    auto_calc_pct("VMI_T", "VMI_SUCC", "VMI_F", "VMI_S", "VMI_C")
    auto_calc_pct("DS_T", "DS_SUCC", "DS_F", "DS_SK", "DS_P")

    return merged
