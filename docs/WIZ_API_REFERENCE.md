# Wiz GraphQL API Reference Guide

This document provides a comprehensive technical reference for querying and automating the **Wiz GraphQL API**. Use this when building custom integrations, writing scripts, or when an AI agent needs to execute queries outside the MCP toolset.

---

## 1. Endpoint & Authentication

### Endpoint Format
```text
https://api.<DATACENTER>.app.wiz.io/graphql
```
*Common datacenters:* `us1`, `us2`, `us20`, `us100`, `eu1`, `eu2`, `au1`, `ca1`, `gov`

### Authentication Flow (OAuth 2.0 Client Credentials)
Wiz uses OAuth 2.0 with JWT access tokens. Tokens have a default lifetime of **24 hours (86,400 seconds)**.

```bash
# Request an Access Token
curl --silent --request POST \
  --url "https://auth.app.wiz.io/oauth/token" \
  --header "Content-Type: application/x-www-form-urlencoded" \
  --data "grant_type=client_credentials" \
  --data "client_id=${WIZ_CLIENT_ID}" \
  --data "client_secret=${WIZ_CLIENT_SECRET}" \
  --data "audience=wiz-api"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

---

## 2. Core GraphQL Query Recipes

### A. Issues Summary & Tenant Security Score
Get high-level risk overview:

```graphql
query GetTenantOverview {
  securityScore {
    score
  }
  issuesSummary(filterBy: { status: [OPEN, IN_PROGRESS] }) {
    critical
    high
    medium
    low
    informational
    all
  }
}
```

---

### B. Querying Active Security Issues (With Pagination)
Fetch open critical and high issues with resource context:

```graphql
query GetOpenIssues($first: Int!, $after: String, $severity: [IssueSeverity!]) {
  issues(
    first: $first
    after: $after
    filterBy: {
      status: [OPEN, IN_PROGRESS]
      severity: $severity
    }
    orderBy: { direction: DESC, field: CREATED_AT }
  ) {
    totalCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      id
      sourceRule {
        name
        description
      }
      severity
      status
      createdAt
      entitySnapshot {
        id
        name
        type
        cloudProvider
        subscriptionName
      }
    }
  }
}
```

Variables:
```json
{
  "first": 50,
  "after": null,
  "severity": ["CRITICAL", "HIGH"]
}
```

---

### C. Vulnerability Findings & CVE Inspection
Fetch exploitable CVEs on cloud workloads:

```graphql
query GetExploitableVulnerabilities($first: Int!) {
  vulnerabilityFindings(
    first: $first
    filterBy: {
      hasExploit: true
      severity: [CRITICAL, HIGH]
    }
  ) {
    totalCount
    nodes {
      id
      name
      severity
      score
      hasExploit
      fixedVersion
      vulnerableAsset {
        id
        name
        type
      }
      link
    }
  }
}
```

---

### D. Security Graph Queries (`graphSearch`)
The Wiz Security Graph models resources, configurations, identities, and vulnerabilities as nodes and relationships.

Example: **Find all Internet-facing Virtual Machines with High Privileges and Open Critical Issues**:

```graphql
query ToxicCombinations {
  graphSearch(
    query: {
      type: [VIRTUAL_MACHINE]
      relationships: [
        {
          type: [{ type: EXPOSED_TO_INTERNET }]
        },
        {
          type: [{ type: HAS_ATTACHED }]
          with: {
            type: [EFFECTIVE_ROLE]
            where: { isAdmin: { EQUALS: true } }
          }
        },
        {
          type: [{ type: HAS_ISSUE }]
          with: {
            type: [ISSUE]
            where: { severity: { EQUALS: CRITICAL }, status: { EQUALS: OPEN } }
          }
        }
      ]
    }
    first: 20
  ) {
    totalCount
    nodes {
      entities {
        id
        name
        type
        properties
      }
    }
  }
}
```

---

### E. Tenant Licenses & Quotas
Inspect purchased SKUs, start/end dates, and used capacity:

```graphql
query GetLicenses {
  tenantLicenses {
    nodes {
      id
      name
      sku
      status
      startAt
      endAt
      quotaUsage {
        totalAmount
        usedAmount
        type
      }
    }
  }
}
```

---

### F. Automation Rules
List configured automated actions (e.g. ticketing, notifications):

```graphql
query GetAutomationRules {
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

---

## 3. Schema Discovery (Introspection)

To dynamically discover fields, queries, or types available on the target tenant:

### Find Query Fields Matching a Keyword
```graphql
query IntrospectQueries {
  __schema {
    queryType {
      fields {
        name
        description
      }
    }
  }
}
```

### Inspect Type Fields
```graphql
query IntrospectType($typeName: String!) {
  __type(name: $typeName) {
    name
    fields {
      name
      description
      type {
        name
        kind
        ofType {
          name
          kind
        }
      }
    }
  }
}
```

---

## 4. Error Handling & Rate Limiting

### Common HTTP Status Codes
| Code | Meaning | Agent Action |
| :--- | :--- | :--- |
| `200 OK` | Query succeeded (inspect `errors` array in JSON if present). | Process `data` object. |
| `400 Bad Request` | GraphQL syntax error or invalid variable types. | Re-check field names and schema types. |
| `401 Unauthorized` | Access token expired or invalid credentials. | Re-fetch token and retry once. |
| `403 Forbidden` | Service account lacks permission for requested field. | Warn user about permission requirements. |
| `429 Too Many Requests` | Rate limit exceeded. | Exponential backoff (sleep 2s, 4s, 8s). |
| `500 / 502 / 504` | Gateway or backend timeout on heavy graph query. | Reduce `$first` limit or simplify nested fields. |

---

## 5. Write Operations (Mutations) Best Practices

Whenever executing mutations:
1. **Always Verify Target Resource ID**: Ensure you are updating the intended entity.
2. **Require User Approval**: Display the proposed mutation parameters to the user and await confirmation.

Example: **Update Issue Status**:
```graphql
mutation UpdateIssueStatus($id: ID!, $status: IssueStatus!, $comment: String) {
  updateIssue(
    input: {
      id: $id
      status: $status
      resolutionReason: FALSE_POSITIVE
      comment: $comment
    }
  ) {
    issue {
      id
      status
      updatedAt
    }
  }
}
```
