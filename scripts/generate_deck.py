#!/usr/bin/env python3
"""
Wiz Tenant Health Assessment & Executive Presentation Deck Builder
===================================================================
Automated CLI tool to:
1. Authenticate with the Wiz GraphQL API using service account credentials.
2. Query live tenant telemetry across posture, inventory, vulnerabilities,
   canonical Kubernetes coverage ladder, Top Controls, Preview Hub, and Tracked Roadmap items.
3. Compute all derived metrics, ratios, and best-practice evaluations.
4. Copy the master Google Slides executive presentation template.
5. Populate all 500+ variables, apply soft green highlighting on enabled previews,
   clean up empty date pairs, and sweep unfilled tokens.
6. Return the live, client-ready Google Slides URL.
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from api_delta_processor import build_replacement_requests, process_raw_api_delta
from console_compat import enable_unicode_output, python_command
from google_slides_client import GoogleSlidesClient, QBR_TEMPLATE_ID
from preview_hub import transform_preview_hub, format_tracked_roadmap_items
from pptx_processor import process_pptx_template

# Configure the console before anything prints: this module and its helpers
# emit checkmarks and bullets that a legacy Windows code page cannot encode.
enable_unicode_output()

def get_wiz_access_token():
    env_vars = {}
    env_path = os.environ.get("ENV_FILE", ".env")
    if not os.path.exists(env_path):
        for p in [Path.cwd() / ".env", SCRIPT_DIR / ".env", SCRIPT_DIR.parent / ".env"]:
            if p.exists():
                env_path = str(p)
                break
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")

    client_id = env_vars.get("WIZ_CLIENT_ID") or os.environ.get("WIZ_CLIENT_ID")
    client_secret = env_vars.get("WIZ_CLIENT_SECRET") or os.environ.get("WIZ_CLIENT_SECRET")
    auth_url = env_vars.get("WIZ_AUTH_URL") or os.environ.get("WIZ_AUTH_URL", "https://auth.wiz.io/oauth/token")
    datacenter = env_vars.get("WIZ_DATACENTER") or os.environ.get("WIZ_DATACENTER", "us100")
    api_endpoint = env_vars.get("WIZ_API_ENDPOINT") or os.environ.get("WIZ_API_ENDPOINT", f"https://api.{datacenter}.app.wiz.io/graphql")

    if not (client_id and client_secret):
        print("\n[!] Wiz Service Account credentials not found.")
        print(f"    Please run: {python_command()} scripts/setup_credentials.py")
        print("    Or create a .env file with WIZ_CLIENT_ID and WIZ_CLIENT_SECRET.\n")
        sys.exit(1)

    auth_data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": "wiz-api"
    }).encode("utf-8")

    req = urllib.request.Request(auth_url, data=auth_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as resp:
        token = json.loads(resp.read()).get("access_token")
    return token, api_endpoint

def run_gql(api_endpoint, access_token, query, variables=None, retries=4):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    for attempt in range(retries):
        try:
            time.sleep(1.5)
            req = urllib.request.Request(
                api_endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
            )
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait_s = 4 * (attempt + 1)
                print(f"    [Rate limit 429] Waiting {wait_s}s before retry...")
                time.sleep(wait_s)
                continue
            raise

def main():
    parser = argparse.ArgumentParser(description="Wiz Tenant Health Assessment & Executive Presentation Deck Builder")
    parser.add_argument("--customer", "-c", help="Customer name for title slides (default: auto-detected from tenant name)")
    parser.add_argument("--folder-id", "-f", help="Target Google Drive folder ID (default: GOOGLE_FOLDER_ID from .env)")
    parser.add_argument("--template-id", "-t", help="Master Google Slides template ID (default: QBR_TEMPLATE_ID from .env)")
    parser.add_argument("--env-file", "-e", help="Path to custom .env file (default: .env)")
    parser.add_argument("--format", choices=["pptx", "slides", "both"], help="Presentation output format: 'pptx' (local PowerPoint), 'slides' (Google Slides), or 'both'")
    parser.add_argument("--output-pptx", help="Path to output local PowerPoint file (default: output/Wiz_Health_Assessment_<Customer>.pptx)")
    parser.add_argument("--pptx-template", help="Path to PowerPoint master template (default: templates/wiz_health_assessment_template.pptx)")
    parser.add_argument("--google-slides", action="store_true", help="Alias for --format slides")
    parser.add_argument("--dry-run", action="store_true", help="Fetch telemetry and calculate metrics without modifying files")
    parser.add_argument("--output-json", "-o", help="Save extracted metrics dictionary to a JSON file")
    args = parser.parse_args()

    if args.env_file:
        os.environ["ENV_FILE"] = args.env_file
    print("[*] Authenticating with Wiz API...")
    access_token, api_endpoint = get_wiz_access_token()

    now = datetime.datetime.now(datetime.timezone.utc)
    end_str = now.strftime("%Y-%m-%dT00:00:00.000Z")
    start_30d = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")
    start_90d = (now - datetime.timedelta(days=90)).strftime("%Y-%m-%dT00:00:00.000Z")

    # 1. Q1: Settings & Workloads & Endpoints
    print("\n[1/5] Running Q1 (Settings, Workloads, Endpoints)...")
    q1 = """
    query TamApiDeltaSettings {
      discoveredResources {
        totalCount
        ownedByTenantCount
        ownedByThirdPartyCount
        unknownCount
        ignoredCount
      }
      disc_all: graphSearch(first: 1, query: {
        type: [CONTAINER_IMAGE, KUBERNETES_CLUSTER, CONTAINER_REPOSITORY, CONTAINER_REGISTRY],
        select: true, where: {_partial: {EQUALS: true}}
      }) { totalCount }
      disc_img:  graphSearch(first: 1, query: {type: [CONTAINER_IMAGE],        select: true, where: {_partial: {EQUALS: true}}}) { totalCount }
      disc_k8s:  graphSearch(first: 1, query: {type: [KUBERNETES_CLUSTER],     select: true, where: {_partial: {EQUALS: true}}}) { totalCount }
      disc_repo: graphSearch(first: 1, query: {type: [CONTAINER_REPOSITORY],   select: true, where: {_partial: {EQUALS: true}}}) { totalCount }
      disc_reg:  graphSearch(first: 1, query: {type: [CONTAINER_REGISTRY],     select: true, where: {_partial: {EQUALS: true}}}) { totalCount }

      workloadScans: resourceScanResultsGroupedByValues(
        first: 10
        filterBy: { modules: { data: { equals: false } } }
        groupBy: [STATUS]
      ) {
        nodes {
          scanCount
          values { status }
        }
      }
      workloadScanRatio: resourceScanResultsStatusRatio(
        filterBy: { modules: { data: { equals: false } } }
      ) {
        successResourceCount
        totalResourceCount
      }

      appEndpointsHttp: applicationEndpoints(first: 1, filterBy: { protocol: { equals: [HTTP, HTTPS] } }) { totalCount }
      appEndpointsNonHttp: applicationEndpoints(first: 1, filterBy: { protocol: { notEquals: [HTTP, HTTPS] } }) { totalCount }
      appEndpointsAll: applicationEndpoints(first: 1) { totalCount }

      kg_ia: cloudResourcesV2(first: 1, filterBy: {
        type: {equals: ["KUBERNETES_CLUSTER"]},
        isAccessibleFromInternet: {equals: true}
      }) { totalCount }

      kc_al: cloudResourcesV2(first: 1, filterBy: {
        type: {equals: ["CONTAINER_IMAGE"]},
        property: [
          {propertyName: "lifecycleStagesV2_build_detected", valueFilter: {booleanFilter: {equals: true}}},
          {propertyName: "imageTags", valueFilter: {isSet: true}}
        ]
      }) { totalCount }

      imgLifecycle: cloudResourcesGroupedByValues(
        filterBy: {type: {equals: ["CONTAINER_IMAGE"]}}
        groupBy:  {fields: [LIFECYCLE_STAGE]}
        first: 20
      ) { nodes { lifecycleStage analytics { resources { count } } } }

      totalContainerImages: cloudResourcesV2(first: 0, filterBy: { type: { equals: ["CONTAINER_IMAGE"] } }) { totalCount }

      registries: containerRegistries(first: 500) {
        totalCount
        nodes { type scanningConfigurationType }
      }
      customRegistries: containerRegistries(first: 1, filterBy: {
        scanningConfigurationType: [CUSTOM]
      }) { totalCount }

      ss: scannerSettings {
        computeResourceGroupMemberScanSamplingEnabled
        virtualMachineImages { enabled scanImagesWithoutInstances }
        aws {
          snapshotReencryptionSettings { sharedCustomerManagedKeysArnPatterns }
          workloadScanningUsingTemporaryVolumesSettings { enabled }
          lightsailScanningSettings { enabled }
          lambdaSettings { scannedVersionCount }
        }
        azure {
          privateEndpointKeyVaults { enabled }
          privateEndpointKeyVaultsWithFirewall { enabled }
        }
      }
      nod: nonOsDiskScanningSettings { enabled daysInterval }
      et:  eventTriggeredScanningSettings { enabled workloadScanningEnabled }
      srt: scannerResourceTagSettings { tags { key value } tagInheritanceEnabled }
      sex: scannerExclusionSettings  { tags { key value } }
      fim: fileIntegrityMonitoringSettings { enabled }

      asm: externalExposureScannerSettings {
        isEnabled
        advancedCapabilities { isEnabled }
        scanners {
          customTargets { isEnabled }
          recon { isEnabled }
          code { isEnabled }
          apiSecurity { isEnabled }
          runtimeSensor { isEnabled }
          saas { isEnabled }
        }
        misconfigurationScanning { isEnabled }
        defaultCredentialsScanning { isEnabled }
        highProfileThreatScanning { isEnabled }
        dastScanning { isEnabled }
        exploitabilityValidationScanning { isEnabled }
        earlyAccessRules { isEnabled }
        vulnerabilityScanning { isEnabled }
        dataScanning { isEnabled }
        secretScanning { isEnabled }
      }

      vas: vulnerabilityAssessmentSettings {
        latestKernelVersionVulnerabilitiesDetectionEnabled
        osPackageManagedCodeLibrariesVulnerabilitiesDetectionEnabled
        windowsManagedVulnerabilitiesDetectionEnabled
        goStandardLibraryVulnerabilitiesEnabled
        legacyCodeLibraryExclusionPathsEnabled
        ignoreRedHatOpenshiftContainerLibraryVulnerabilities
        pipInstalledPythonLibrariesVulnerabilitiesEnabled
        npmInstalledJavascriptLibrariesVulnerabilitiesEnabled
        codeLibraries {
          manifestFilesLifecycleStages
          lockFilesLifecycleStages
          artifactsLifecycleStages
          mavenScopes
          npmScopes
          gradleScopes
        }
        endOfLifeTechnologies { upcomingDetectionEnabled upcomingDetectionDays }
      }

      dss: dataScannerSettings {
        enabled
        bucketConfig       { enabled privateBucketsEnabled }
        virtualDriveConfig { enabled }
        cloudDbConfig      { enabled }
        bigQueryConfig     { enabled }
        dynamoDbConfig     { enabled }
        snowflakeConfigV2  { schemaScanEnabled }
        databricksConfigV2 { schemaScanEnabled }
        diskDbConfig       { enabled }
        diskFileConfig     { enabled }
        serverlessConfig   { enabled }
        vertexAiConfig     { enabled }
        openAiConfig       { enabled azureEnabled }
        shadowDataConfig   { enabled }
        azureStorageAccountConfig {
          privateEndpointGeneralConfig       { enabled }
          privateEndpointWithFirewallConfig  { enabled }
        }
        azureCosmosDbConfig {
          privateEndpointGeneralConfig       { enabled }
          privateEndpointWithFirewallConfig  { enabled }
        }
      }
    }
    """
    res1 = run_gql(api_endpoint, access_token, q1)

    # 2. Q2: Issues & Trends & MTTR & Avg Age
    print("[2/5] Running Q2 (Issues, MTTR, Avg Age, SHI)...")
    q2 = """
    query TamApiDeltaIssues(
      $startDate: DateTime!
      $startDate90d: DateTime!
      $endDate:   DateTime!
    ) {
      ocIssues: issuesV2(first: 1, filterBy: {severity: [CRITICAL], status: [OPEN, IN_PROGRESS], type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION]}) { totalCount }
      ohIssues: issuesV2(first: 1, filterBy: {severity: [HIGH],     status: [OPEN, IN_PROGRESS], type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION]}) { totalCount }
      rcIssues: issuesV2(first: 1, filterBy: {severity: [CRITICAL], status: [RESOLVED], type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION]}) { totalCount }
      rhIssues: issuesV2(first: 1, filterBy: {severity: [HIGH],     status: [RESOLVED], type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION]}) { totalCount }
      rjIssues: issuesV2(first: 1, filterBy: {status: [REJECTED],                      type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION]}) { totalCount }
      otIssues: issuesV2(first: 1, filterBy: {type: [THREAT_DETECTION], status: [OPEN, IN_PROGRESS]}) { totalCount }
      rtIssues: issuesV2(first: 1, filterBy: {type: [THREAT_DETECTION], status: [RESOLVED], resolvedAt: {after: $startDate90d}}) { totalCount }

      shi_open: systemHealthIssues(first: 1, filterBy: { status: [OPEN] }) {
        criticalSeverityCount
        highSeverityCount
        totalCount
      }
      systemHealthIssues(first: 1, filterBy: { status: [RESOLVED] }) {
        criticalSeverityCount
        highSeverityCount
        totalCount
      }

      mttr: issuesTrendV2(
        filterBy: { type: [THREAT_DETECTION] }
        type: MTTR
        startDate: $startDate90d
        endDate: $endDate
      ) { total dataPoints { time totalValue criticalSeverityValue highSeverityValue } }

      avgAge: issuesTrendV2(
        filterBy: {
          severity: [CRITICAL, HIGH]
          type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION]
        }
        type: AVERAGE_ISSUE_AGE
        startDate: $startDate
        endDate: $endDate
        interval: DAY
      ) { dataPoints { time criticalSeverityValue highSeverityValue } }
    }
    """
    res2 = run_gql(api_endpoint, access_token, q2, {"startDate": start_30d, "startDate90d": start_90d, "endDate": end_str})

    # Discover active primary license for billable workload metrics
    print("\n[*] Discovering active tenant license...")
    q_lic = """
    query {
      viewerV2 {
        tenant {
          licenses { id sku status startAt endAt }
        }
      }
    }
    """
    res_lic = run_gql(api_endpoint, access_token, q_lic)
    licenses = (res_lic.get("data", {}).get("viewerV2", {}).get("tenant", {}) or {}).get("licenses", [])
    active_licenses = [l for l in licenses if l.get("status") == "ACTIVE"]
    primary_lic_id = None
    for pref in ["ONE", "ADVANCED", "ENTERPRISE", "ESSENTIAL", "CLOUD_OPS"]:
        for l in active_licenses:
            if l.get("sku") == pref:
                primary_lic_id = l.get("id")
                break
        if primary_lic_id:
            break
    if not primary_lic_id and active_licenses:
        primary_lic_id = active_licenses[0].get("id")
    print(f"    Active primary license ID: {primary_lic_id}")

    # 3. Q3: Users, Projects, Security Score, Cloud Accounts, Connectors, K8s, Outposts, Sensors, Deployments, Cloud Event Rules
    print("[3/5] Running Q3 (Users, Projects, Security Score, Accounts, Connectors, Outposts, Sensors, Events)...")
    q3 = """
    query TamApiDeltaDemocratization(
      $logged30d:  DateTime!
      $scoreStart: DateTime!
      $scoreEnd:   DateTime!
      $cliStart:   DateTime!
    ) {
      uTot: users(first: 1, filterBy: {status: {notEquals: [DELETED]}}) { totalCount }
      uAct: users(first: 1, filterBy: {lastLoginAt: {after: $logged30d}}) { totalCount }
      ssoUsers: users(first: 500) {
        nodes { identityProviderV2 { name } }
      }
      pTot:  projects(first: 1) { totalCount LBICount MBICount HBICount }
      pRoot: projects(first: 1, filterBy: {root: true}) { totalCount }
      champItems: championCenterJourneyItems {
        type
        maturity
        owner { id name email }
      }
      tcs: tenantContactSettings { supportContacts { id } }
      viewerV2 { tenant { industry licenses { id sku status } } }
      secScore: monitoredMetrics(first: 5, filterBy: {type: [SECURITY_SCORE], builtin: true}) {
        nodes {
          id name type
          dataPoints(startDate: $scoreStart, endDate: $scoreEnd, timeInterval: DAY) { time value }
        }
      }
      ssBench: monitoredMetricsBenchmarks {
        securityScore {
          byIndustry                  { percentile50 }
          byWorkloadCount             { percentile50 }
          byIndustryAndWorkloadCount  { percentile50 }
        }
      }
      trOn:  resourceTaggingRules(filterBy: {enabled: true})  { totalCount }
      trOff: resourceTaggingRules(filterBy: {enabled: false}) { totalCount }
      drTotal: applicationServiceDiscoveryRules(first: 1)     { totalCount }
      wfOn:  automationWorkflows(filterBy: {enabled: true})   { totalCount }
      wfOff: automationWorkflows(filterBy: {enabled: false})  { totalCount }

      cliScans: cicdScans(first: 1, filterBy: { createdAt: { after: $cliStart } }) { totalCount }
      k8sClusters: kubernetesClusters(first: 500) {
        totalCount
        nodes {
          name
          kind
          nodeCount
          containerCount
          connectors {
            id
            enabled
          }
          admissionController {
            id
            healthStatus
          }
          kubernetesAuditLogCollector {
            id
            healthStatus
          }
          sensorGroup {
            id
          }
        }
      }
      serverless: graphSearch(first: 1, query: {type: [SERVERLESS], select: true}, projectId: "*", quick: true) { totalCount }
      cloudAccounts(first: 500) { totalCount nodes { cloudProvider name } }
      connectors(first: 500) { totalCount nodes { id name enabled status type { id name } extraConfig } }
      outposts(first: 1) { totalCount }
      sensors(first: 1) { totalCount }
      deployments(first: 500) { totalCount nodes { type status } }
      cloudEvents(
        groupBy: { fields: ["origin"] }
        orderDirection: DESC
        first: 30
        filterBy: { and: [ { timestamp: { inLast: { unit: DurationFilterValueUnitMonths, amount: 1 } } } ] }
      ) {
        nodes {
          ... on CloudEventGroupByResult {
            values
            countV2
            groupPercentage
          }
        }
      }
    }
    """
    res3 = run_gql(api_endpoint, access_token, q3, {
        "logged30d": start_30d,
        "scoreStart": start_90d,
        "scoreEnd": end_str,
        "cliStart": start_30d
    })

    # Execute WorkloadLicenseUsage if primary license is found
    res_lic_usage = None
    if primary_lic_id:
        print("    Running WorkloadLicenseUsage query with active license...")
        q_lic_usage = """
        query WorkloadLicenseUsage($startAt: DateTime!, $endAt: DateTime!, $license: ID!) {
          billableWorkloadTrendV2(
            startDate: $startAt
            endDate: $endAt
            license: $license
          ) {
            ... on CloudBillableWorkloadTrendData {
              averageComputeWorkloadCount
              averageVirtualMachineCount
              averageContainerHostCount
              averageServerlessCount
              averageServerlessContainerCount
              wizOsWorkloadCount
              greenAgentWorkloadDetails { runCount }
              dataPoints {
                id
                timestamp
                ... on CloudBillableWorkloadSampleV2 {
                  computeWorkloadCount
                  virtualMachineCount
                  containerHostCount
                  serverlessCount
                  serverlessContainerCount
                  wizOsWorkloadCount
                }
              }
            }
            ... on SensorBillableWorkloadTrendData {
              averageSensorWorkloadCount
              averageKubernetesSensorCount
              averageVMSensorCount
              dataPoints {
                id
                timestamp
                ... on SensorBillableWorkloadSampleV2 {
                  sensorWorkloadCount
                  kubernetesSensorsCount
                  virtualMachineSensorsCount
                  serverlessContainerSensorsCount
                }
              }
            }
          }
        }
        """
        res_lic_usage = run_gql(api_endpoint, access_token, q_lic_usage, {
            "startAt": start_30d,
            "endAt": end_str,
            "license": primary_lic_id
        })

    # 4. Q4: Technologies & Active Service Accounts & AI Inventory
    print("[4/5] Running Q4-combined (Technologies, Accounts, AI Inventory)...")
    q4 = """
    query TamApiDeltaPiCombined {
      q4a_totals: graphSearch(
        first: 500
        projectId: "*"
        quick: false
        query: {
          select: true
          type: [TECHNOLOGY]
          where: {
            deploymentModel: {EQUALS: ["Cloud service"]}
            name: {DOES_NOT_CONTAIN: ["Wiz"]}
          }
          relationships: [{
            type: [{type: HAS_TECH, reverse: true}]
            with: {
              select: true
              type: [SERVICE_ACCOUNT]
              where: {externalOwners: {IS_SET: true}}
              aggregate: true
              relationships: [{
                type: [{type: CONTAINS, reverse: true}]
                with: {
                  type: [SUBSCRIPTION, CLOUD_ORGANIZATION]
                  where: {name: {DOES_NOT_START_WITH: ["Discovered"]}}
                }
              }]
            }
          }]
        }
      ) {
        nodes { aggregateCount entities { id name type properties } }
      }
      q4b_active: graphSearch(
        first: 500
        projectId: "*"
        quick: false
        query: {
          select: true
          type: [TECHNOLOGY]
          where: {
            deploymentModel: {EQUALS: ["Cloud service"]}
            name: {DOES_NOT_CONTAIN: ["Wiz"]}
          }
          relationships: [{
            type: [{type: HAS_TECH, reverse: true}]
            with: {
              select: true
              type: [SERVICE_ACCOUNT]
              where: {
                externalOwners: {IS_SET: true}
                inactiveInLast90Days: {EQUALS: false}
              }
              aggregate: true
              relationships: [{
                type: [{type: CONTAINS, reverse: true}]
                with: {
                  type: [SUBSCRIPTION, CLOUD_ORGANIZATION]
                  where: {name: {DOES_NOT_START_WITH: ["Discovered"]}}
                }
              }]
            }
          }]
        }
      ) {
        nodes { aggregateCount entities { id name type properties } }
      }
      aiSecFindings: aiSecurityFindingsGroupedByValues(first: 500, groupBy: {fields: [TYPE]}) {
        nodes { type analytics { totalFindingCount } }
        pageInfo { hasNextPage }
      }
      aiMisconfigFindings: configurationFindingsGroupedByValues(first: 500, filterBy: {status: [OPEN], frameworkCategory: ["wct-id-1998"]}, groupBy: {fields: [RESOURCE_TYPE]}) {
        nodes { resourceType analytics { totalFindingCount } }
        pageInfo { hasNextPage }
      }
      aiAgents: cloudResourcesV2(filterBy: {type: {equals: ["AI_AGENT"]}, property: [{propertyName: "status", valueFilter: {stringArrayFilter: {containsAny: ["Active"]}}}]}, first: 0) {
        totalCount
      }
      aiModels: cloudResourcesV2(filterBy: {type: {equals: ["AI_MODEL"]}, property: [{propertyName: "status", valueFilter: {stringArrayFilter: {containsAny: ["Active"]}}}]}, first: 0) {
        totalCount
      }
      aiGuardrails: cloudResourcesV2(filterBy: {type: {equals: ["AI_GUARDRAIL"]}, property: [{propertyName: "status", valueFilter: {stringArrayFilter: {containsAny: ["Active"]}}}]}, first: 0) {
        totalCount
      }
      aiMcpServers: cloudResourcesV2(filterBy: {type: {equals: ["MCP_SERVER"]}}, first: 0) {
        totalCount
      }
      aiPipelines: cloudResourcesV2(filterBy: {type: {equals: ["AI_PIPELINE"]}, property: [{propertyName: "status", valueFilter: {stringArrayFilter: {containsAny: ["Active"]}}}]}, first: 0) {
        totalCount
      }
      aiDatasets: cloudResourcesV2(filterBy: {type: {equals: ["AI_DATASET"]}}, first: 0) {
        totalCount
      }
      aiTechnologies: technologiesV2(first: 0, filterBy: {category: {stackLayer: [MACHINE_LEARNING_AND_AI]}, usedByOrganization: true, familyId: {isSet: false}}) {
        totalCount
      }
      aiCodingAgents: hostedTechnologies(first: 0, filterBy: {isInherited: false, resource: {type: {equals: ["IDE"]}}, technologyV2: {category: {category: ["169", "246"], stackLayer: [MACHINE_LEARNING_AND_AI]}}, codeToCloudPipelineStage: {equals: [CODE]}}) {
        totalCount
      }
      aiCodeRepos: hostedTechnologiesGroupedByValues(
        first: 0
        filterBy: {isInherited: false, resource: {type: {equals: ["REPOSITORY_BRANCH"]}}, technologyV2: {category: {category: ["169", "246"], stackLayer: [MACHINE_LEARNING_AND_AI]}}, codeToCloudPipelineStage: {equals: [CODE]}}
        groupBy: {fields: [CODE_REPOSITORY]}
      ) {
        totalCount
      }
      aiWorkloads: graphSearch(
        query: {
          type: [VIRTUAL_MACHINE, VIRTUAL_MACHINE_IMAGE, CONTAINER, CONTAINER_IMAGE, SERVERLESS]
          select: true
          where: { purposes: { EQUALS: ["AI"] } }
          relationships: [{
            type: [{ type: RUNS }]
            with: {
              type: [AI_AGENT, AI_MODEL, MCP_SERVER]
              select: true
              aggregate: true
            }
          }]
        }
        projectId: "*"
        first: 0
        quick: false
      ) {
        totalCount
      }
    }
    """
    res4 = run_gql(api_endpoint, access_token, q4)

    print("[4.5/5] Running Q4c (Potential Integrations Service Account Timeline Dates)...")
    q4c = """
    query TamApiDeltaPiDates($after: String) {
      graphSearch(
        first: 1000
        projectId: "*"
        quick: false
        after: $after
        query: {
          select: true
          type: [TECHNOLOGY]
          where: {
            deploymentModel: {EQUALS: ["Cloud service"]}
            name: {DOES_NOT_CONTAIN: ["Wiz"]}
          }
          relationships: [{
            type: [{type: HAS_TECH, reverse: true}]
            with: {
              select: true
              type: [SERVICE_ACCOUNT]
              where: {externalOwners: {IS_SET: true}}
              relationships: [{
                type: [{type: CONTAINS, reverse: true}]
                with: {
                  type: [SUBSCRIPTION, CLOUD_ORGANIZATION]
                  where: {name: {DOES_NOT_START_WITH: ["Discovered"]}}
                }
              }]
            }
          }]
        }
      ) {
        nodes { entities { id name type properties } }
        pageInfo { hasNextPage endCursor }
      }
    }
    """
    res4c = run_gql(api_endpoint, access_token, q4c, {"after": None})

    # 5. Q5: Data Scans & Red Agent Modules
    print("[5/5] Running Q5 (Data Scans, Red Agent Modules)...")
    q5 = """
    query TamApiDeltaRedAgentAndDataScans(
      $dsTotalQuery: GraphEntityQueryInput
      $dsFailedQuery: GraphEntityQueryInput
      $dsSkippedQuery: GraphEntityQueryInput
    ) {
      ds_total: graphSearch(query: $dsTotalQuery, projectId: "*", quick: true) { totalCount }
      ds_failed: graphSearch(query: $dsFailedQuery, projectId: "*", quick: true) { totalCount }
      ds_skipped: graphSearch(query: $dsSkippedQuery, projectId: "*", quick: true) { totalCount }

      redAgentSettings {
        scanIntervalDays
        dastAttackerModule { isEnabled }
        webCrawlerModule { isEnabled }
        secretImpactModule { isEnabled }
        saasAttackerModule { isEnabled }
      }
      webCrawlerApiEndpoints: apiEndpoints(filterBy: { isAiGenerated: true }) { totalCount }
      webDastAttackerFindings: attackSurfaceFindings(filterBy: { status: { equals: [OPEN] }, redAgentModule: { equals: [DAST_ATTACKER] } }) { totalCount }
      webDastAttackerIssues: issues(filterBy: { status: [OPEN, IN_PROGRESS], riskEqualsAny: ["wct-id-3959"], type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION] }) { totalCount }
      secretsBlastRadiusFindings: attackSurfaceFindings(filterBy: { status: { equals: [OPEN] }, redAgentModule: { equals: [SECRET_IMPACT] } }) { totalCount }
      saasAttackerFindings: attackSurfaceFindings(filterBy: { status: { equals: [OPEN] }, redAgentModule: { equals: [SAAS_ATTACKER] } }) { totalCount }

      customFrameworksEnabled: securityFrameworks(first: 0, filterBy: { createdBy: USER, enabled: true }) { totalCount }
      customFrameworksDisabled: securityFrameworks(first: 0, filterBy: { createdBy: USER, enabled: false }) { totalCount }
      customFrameworksAll: securityFrameworks(first: 0, filterBy: { createdBy: USER }) { totalCount }
      aiSettings {
        redAgent {
          isEnabled
        }
      }
      aiAgentsList: aiAgents(first: 50) {
        nodes {
          name
          enabled
        }
      }
      integrationDeployments: deployments(first: 100, filterBy: {
        status: [ENABLED],
        subtypeNotEquals: { integration: [AZURE_DEVOPS, WIZ_SYSTEM] },
        type: [INTEGRATION]
      }) {
        nodes {
          id
          name
          lastSeenAt
          object {
            ... on Integration {
              id
              name
              status
              lastTestedAt
            }
          }
        }
      }
      browserExtensionAudit: auditLogEntriesGroupedByValues(
        first: 20
        filterBy: {
          actionV2: ["AiAssistantSendMessage"],
          userType: [USER_ACCOUNT],
          clientType: { notEquals: [UNKNOWN] }
        }
        groupBy: { fields: [CLIENT_TYPE] }
      ) {
        nodes {
          clientType
          analytics {
            totalCount
            performerCount
          }
        }
      }
      mcpAudit: auditLogEntriesGroupedByValues(
        first: 0
        filterBy: { clientType: { equals: [MCP] } }
        groupBy: { fields: [PERFORMER] }
      ) {
        totalCount
      }
    }
    """
    q5_vars = {
      "dsTotalQuery": {
        "type": ["CLOUD_RESOURCE"],
        "relationships": [{
          "type": [{"type": "SCANNED", "reverse": True}],
          "with": {"type": ["SECURITY_TOOL_SCAN"], "select": True, "where": {"name": {"CONTAINS": ["data scan"]}}}
        }],
        "select": True
      },
      "dsFailedQuery": {
        "type": ["CLOUD_RESOURCE"],
        "relationships": [{
          "type": [{"type": "SCANNED", "reverse": True}],
          "with": {"type": ["SECURITY_TOOL_SCAN"], "select": True, "where": {"name": {"CONTAINS": ["data scan"]}, "status": {"EQUALS": ["ScanStatusError"]}}}
        }],
        "select": True
      },
      "dsSkippedQuery": {
        "type": ["CLOUD_RESOURCE"],
        "relationships": [{
          "type": [{"type": "SCANNED", "reverse": True}],
          "with": {"type": ["SECURITY_TOOL_SCAN"], "select": True, "where": {"name": {"CONTAINS": ["data scan"]}, "status": {"EQUALS": ["ScanStatusSkipped"]}}}
        }],
        "select": True
      }
    }
    res5 = run_gql(api_endpoint, access_token, q5, q5_vars)

    print("[*] Running K8s Coverage Ladder & Gaps query (canonical property counts)...")
    q_k8s_cov = """
    query K8sCoverageLadderAndGaps {
      totalClusters: cloudResourcesV2(first: 0, filterBy: { type: { equals: ["KUBERNETES_CLUSTER"] } }) { totalCount }
      kc_wc: cloudResourcesV2(first: 0, filterBy: {
        type: { equals: ["KUBERNETES_CLUSTER"] },
        property: [{ propertyName: "deploymentCoverage_connector_deploymentStatus", valueFilter: { stringArrayFilter: { containsAny: ["Installed"] } } }]
      }) { totalCount }
      kg_nc: cloudResourcesV2(first: 0, filterBy: {
        type: { equals: ["KUBERNETES_CLUSTER"] },
        property: [{ propertyName: "deploymentCoverage_connector_deploymentStatus", valueFilter: { stringArrayFilter: { containsAny: ["NotInstalled"] } } }]
      }) { totalCount }
      kc_ac: cloudResourcesV2(first: 0, filterBy: {
        type: { equals: ["KUBERNETES_CLUSTER"] },
        property: [{ propertyName: "deploymentCoverage_admissionController_deploymentStatus", valueFilter: { stringArrayFilter: { containsAny: ["Installed"] } } }]
      }) { totalCount }
      kc_se: cloudResourcesV2(first: 0, filterBy: {
        type: { equals: ["KUBERNETES_CLUSTER"] },
        property: [{ propertyName: "deploymentCoverage_auditLogCollector_deploymentStatus", valueFilter: { stringArrayFilter: { containsAny: ["Installed"] } } }]
      }) { totalCount }
      kg_na: cloudResourcesV2(first: 0, filterBy: {
        type: { equals: ["KUBERNETES_CLUSTER"] },
        property: [{ propertyName: "deploymentCoverage_auditLogCollector_deploymentStatus", valueFilter: { stringArrayFilter: { containsAny: ["NotInstalled"] } } }]
      }) { totalCount }
      kc_cli: cloudResourcesV2(first: 0, filterBy: {
        type: { equals: ["KUBERNETES_CLUSTER"] },
        property: [{ propertyName: "deploymentCoverage_sensor_deploymentStatus", valueFilter: { stringArrayFilter: { containsAny: ["Installed"] } } }]
      }) { totalCount }
      kg_ns: cloudResourcesV2(first: 0, filterBy: {
        type: { equals: ["KUBERNETES_CLUSTER"] },
        property: [{ propertyName: "deploymentCoverage_sensor_deploymentStatus", valueFilter: { stringArrayFilter: { containsAny: ["NotInstalled"] } } }]
      }) { totalCount }
    }
    """
    res_k8s_cov = run_gql(api_endpoint, access_token, q_k8s_cov)

    print("[*] Running Top Controls by Issue Count query (Slide 11 Critical & High)...")
    q_controls = """
    query TopControlsByIssueCount {
      criticalControls: issuesGroupedByValue(
        groupBy: SOURCE_RULE
        filterBy: {
          severity: [CRITICAL]
          status: [OPEN, IN_PROGRESS]
          type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION]
        }
        first: 20
        orderBy: { field: ISSUE_COUNT, direction: DESC }
      ) {
        nodes {
          id
          issues(first: 1) {
            totalCount
            nodes {
              sourceRules {
                ... on Control {
                  id
                  name
                }
                ... on CloudConfigurationRule {
                  id
                  name
                  control {
                    id
                    name
                  }
                }
              }
            }
          }
        }
      }

      highControls: issuesGroupedByValue(
        groupBy: SOURCE_RULE
        filterBy: {
          severity: [HIGH]
          status: [OPEN, IN_PROGRESS]
          type: [CLOUD_CONFIGURATION, TOXIC_COMBINATION]
        }
        first: 20
        orderBy: { field: ISSUE_COUNT, direction: DESC }
      ) {
        nodes {
          id
          issues(first: 1) {
            totalCount
            nodes {
              sourceRules {
                ... on Control {
                  id
                  name
                }
                ... on CloudConfigurationRule {
                  id
                  name
                  control {
                    id
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    res_controls = run_gql(api_endpoint, access_token, q_controls)

    print("[*] Running Preview & Migration Hub query...")
    q_preview = """
    query GetPreviewAndMigrationHubItems {
      previewAndMigrationHubItems {
        id
        title
        description
        enabled
        type
        private
        billable
        licenseCategories
        docsUrl
        automaticallyEnabledAt
        enabledUpdatedAt
        cta {
          relativeUrl
        }
      }
    }
    """
    res_preview = run_gql(api_endpoint, access_token, q_preview)
    preview_items = res_preview.get("data", {}).get("previewAndMigrationHubItems", [])
    preview_vars, preview_links = transform_preview_hub(preview_items)
    print(f"    Compiled {len(preview_vars)} preview variables across {len(preview_items)} Preview Hub items.")

    print("[*] Running Tracked Roadmap Items query...")
    q_roadmap = """
    query TrackedRoadmapItems($after: String, $first: Int, $filterBy: TrackedRoadmapItemsFilters, $orderBy: TrackedRoadmapItemsOrder) {
      trackedRoadmapItems(
        after: $after
        first: $first
        filterBy: $filterBy
        orderBy: $orderBy
      ) {
        totalCount
        nodes {
          id
          title
          ticketId
          developmentStatus
          plannedReleaseDate {
            year
            quarter
          }
          tracking {
            priority
          }
        }
      }
    }
    """
    res_roadmap = run_gql(api_endpoint, access_token, q_roadmap, {
        "first": 20,
        "orderBy": {
            "field": "PRIORITY",
            "direction": "DESC"
        }
    })
    roadmap_nodes = res_roadmap.get("data", {}).get("trackedRoadmapItems", {}).get("nodes", [])
    roadmap_total = res_roadmap.get("data", {}).get("trackedRoadmapItems", {}).get("totalCount", len(roadmap_nodes))
    preview_vars["ROADMAP_TRACKER"] = format_tracked_roadmap_items(roadmap_nodes, limit=20)
    preview_vars["ROADMAP_TRACKER_TOTAL"] = str(roadmap_total)
    print(f"    Compiled ROADMAP_TRACKER with top {len(roadmap_nodes[:20])} of {roadmap_total} tracked roadmap items.")

    all_responses = [res1, res2, res3, res4, res4c, res5, res_k8s_cov, res_controls]
    if res_lic:
        all_responses.append(res_lic)
    if res_lic_usage:
        all_responses.append(res_lic_usage)
    combined_payload = "\n---\n".join([json.dumps(r) for r in all_responses])

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    customer_name = args.customer
    if not customer_name:
        tenant_info = ((res3.get("data", {}).get("viewerV2", {}) or {}).get("tenant", {}) or {})
        customer_name = tenant_info.get("name") or "Cloud Security Customer"
    target_folder_id = args.folder_id or os.environ.get("GOOGLE_FOLDER_ID") or "11OSM169RkTJIbpj7l4lFiwsrU6lgk5FJ"
    template_id = args.template_id or os.environ.get("QBR_TEMPLATE_ID") or QBR_TEMPLATE_ID

    print("\n[*] Processing API payload & generating variable replacements...")
    reqs, merged = build_replacement_requests(
        customer_name=customer_name,
        today_str=today_str,
        tam_metrics={},
        api_delta_text=combined_payload,
        preview_vars=preview_vars
    )
    print(f"    Generated {len(reqs)} replaceAllText requests across {len(merged)} variables.")

    # Determine output format
    selected_format = args.format
    if not selected_format:
        if args.google_slides:
            selected_format = "slides"
        elif not args.dry_run and sys.stdin.isatty():
            print("\nSelect Presentation Output Format:")
            print("  [1] PowerPoint Presentation (.pptx) - Local file, no Google account needed (Default)")
            print("  [2] Google Slides Presentation - Creates live deck in Google Drive")
            print("  [3] Both (PowerPoint + Google Slides)")
            choice = input("Choice [1/2/3, default: 1]: ").strip()
            if choice == "2":
                selected_format = "slides"
            elif choice == "3":
                selected_format = "both"
            else:
                selected_format = "pptx"
        else:
            selected_format = "pptx"

    # 1. Local PowerPoint (.pptx) Generation
    template_pptx = args.pptx_template or str(SCRIPT_DIR.parent / "templates" / "wiz_health_assessment_template.pptx")
    customer_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', customer_name)
    output_pptx = args.output_pptx or str(Path.cwd() / "output" / f"Wiz_Health_Assessment_{customer_slug}_{today_str}.pptx")

    if selected_format in ("pptx", "both") and not args.dry_run:
        if not os.path.exists(template_pptx):
            print(f"\n[!] PowerPoint template not found at: {template_pptx}")
        else:
            print(f"\n[*] Generating PowerPoint presentation from {template_pptx}...")
            enabled_titles = {it["title"].strip() for it in preview_items if it.get("enabled")}
            pptx_res = process_pptx_template(
                template_path=template_pptx,
                output_path=output_pptx,
                variables=merged,
                enabled_preview_titles=enabled_titles
            )
            print(f"    [✓] PowerPoint presentation generated: {output_pptx} ({pptx_res['file_size']} bytes)")
            print(f"    Applied {pptx_res['replacements_made']} token replacements across all slides.")
            print(f"    Highlighted {pptx_res['highlighted_count']} enabled preview lines.")
            if pptx_res['swept_tokens'] > 0:
                print(f"    Swept {pptx_res['swept_tokens']} unfilled template tokens.")

    # 2. Google Slides Generation
    new_deck_id = None
    new_deck_url = None

    if selected_format in ("slides", "both") and not args.dry_run:
        slides_client = GoogleSlidesClient.from_env()
        if not slides_client:
            print("\n[!] Google Slides credentials not found in .env.")
            print(f"    See docs/GOOGLE_SLIDES_SETUP.md or run: {python_command()} scripts/setup_credentials.py")
        else:
            print(f"\n[*] Copying master template {template_id} to customer folder {target_folder_id}...")
            copy_res = slides_client.copy_template(customer_name, timestamp_str, target_folder_id)
            new_deck_id = copy_res.get("id")
            new_deck_url = copy_res.get("webViewLink") or f"https://docs.google.com/presentation/d/{new_deck_id}/edit"
            print(f"    New Deck ID: {new_deck_id}")
            print(f"    New Deck URL: {new_deck_url}")

            print(f"\n[*] Applying {len(reqs)} batch replacement requests via Slides API...")
            slides_client.batch_update_presentation(new_deck_id, reqs)

            print("\n[*] Highlighting enabled preview items in light green on Slides 16 & 17...")
            def highlight_enabled_previews(slides_client, presentation_id, preview_items):
                SLIDES_API_BASE = "https://slides.googleapis.com/v1"
                enabled_titles = {it["title"].strip() for it in preview_items if it.get("enabled")}
                pres = slides_client._request("GET", f"{SLIDES_API_BASE}/presentations/{presentation_id}")
                
                highlight_reqs = []
                for slide in pres.get("slides", []):
                    for elem in slide.get("pageElements", []):
                        elem_id = elem.get("objectId")
                        if "shape" in elem and "text" in elem["shape"]:
                            full_text = "".join(te.get("textRun", {}).get("content", "") for te in elem["shape"]["text"].get("textElements", []))
                            for line in full_text.split("\n"):
                                line_str = line.strip()
                                if not line_str or not line_str.startswith("•"):
                                    continue
                                clean_title = line_str.lstrip("• ").strip()
                                if clean_title in enabled_titles:
                                    idx = full_text.find(line)
                                    if idx != -1:
                                        highlight_reqs.append({
                                            "updateTextStyle": {
                                                "objectId": elem_id,
                                                "textRange": {
                                                    "type": "FIXED_RANGE",
                                                    "startIndex": idx,
                                                    "endIndex": idx + len(line)
                                                },
                                                "style": {
                                                    "backgroundColor": {
                                                        "opaqueColor": {
                                                            "rgbColor": {
                                                                "red": 0.88,
                                                                "green": 0.96,
                                                                "blue": 0.88
                                                            }
                                                        }
                                                    }
                                                },
                                                "fields": "backgroundColor"
                                            }
                                        })
                if highlight_reqs:
                    slides_client.batch_update_presentation(presentation_id, highlight_reqs)
                return len(highlight_reqs)

            hl_count = highlight_enabled_previews(slides_client, new_deck_id, preview_items)
            print(f"    Highlighted {hl_count} enabled preview lines in light green.")

            print("\n[*] Archiving previous customer decks...")
            arch_count = slides_client.archive_prior_decks(target_folder_id, new_deck_id)
            print(f"    Moved {arch_count} prior deck(s) into archive/ subfolder.")

            print("\n[*] Sweeping remaining unfilled template tokens...")
            sweep_res = slides_client.sweep_remaining_tokens(new_deck_id)
            print(f"    Swept {sweep_res.get('swept_count', 0)} unfilled token(s)")

    if args.dry_run:
        print(f"\n[*] Dry Run Completed for Customer: {customer_name}")
        print(f"    Total Variables Computed: {len(merged)}")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        print(f"    Saved metrics to: {args.output_json}")

    print("\n=======================================================")
    print("           DECK GENERATION SUCCESSFUL                  ")
    if not args.dry_run and os.path.exists(output_pptx):
        print(f" Local PPTX: {output_pptx}")
    if new_deck_url:
        print(f" Google Slides: {new_deck_url}")
    print("=======================================================\n")

    return new_deck_id, new_deck_url, merged

if __name__ == "__main__":
    main()
