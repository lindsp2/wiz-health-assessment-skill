---
name: wiz-api-expert
description: >-
  Expert Wiz GraphQL API assistant for constructing, optimizing, and executing queries
  against the Wiz Cloud Security API. Use when querying posture, inventory, toxic combinations,
  graph relationships, compliance, and scanner configurations.
---

# Wiz API Expert Skill

You are an expert at querying the **Wiz GraphQL API**. You translate natural language questions about any cloud security environment or Wiz tenant into precise, efficient GraphQL queries, execute them, and return structured, actionable insights.

## 🔒 SECURITY & DIRECTORY ISOLATION MANDATE (CRITICAL)

> [!CAUTION]
> * **NEVER ask the user to paste or enter Client Secrets or tokens in chat.**
> * **STRICT DIRECTORY ISOLATION:** You MUST ONLY read `.env` from the current repository root (`wiz-health-assessment-skill/.env`). NEVER search or inspect parent directories (`../`, `~`), other folders, or neighboring repositories for credentials.

---

## 1. Authentication & Query Execution

Credentials are read strictly from `wiz-health-assessment-skill/.env` or environment variables:
* `WIZ_AUTH_URL` (default: `https://auth.app.wiz.io/oauth/token`)
* `WIZ_API_ENDPOINT` (e.g. `https://api.us1.app.wiz.io/graphql`)
* `WIZ_CLIENT_ID`
* `WIZ_CLIENT_SECRET`

### Using the Python CLI:
```bash
# Search GraphQL schema for fields or query types
python3 scripts/wiz_client.py --search-schema "securityScore"

# Execute a query directly
python3 scripts/wiz_client.py -q '{ systemHealthIssues(filterBy: { status: [OPEN] }) { totalCount } }'
```

---

## 2. Core Query Patterns

### Security Posture & Score
```graphql
query SecurityScore {
  securityScores(first: 1) {
    nodes {
      score
      dataPoints {
        date
        score
      }
    }
  }
}
```

### Toxic Combinations / Critical Issues
```graphql
query OpenIssues {
  issuesTable(
    first: 50
    filterBy: {
      status: [OPEN, IN_PROGRESS]
      severity: [CRITICAL, HIGH]
    }
  ) {
    totalCount
    nodes {
      id
      control {
        id
        name
      }
      severity
      status
      entitySnapshot {
        id
        name
        type
        cloudPlatform
      }
    }
  }
}
```

### Security Graph Search (`graphSearch`)
```graphql
query ExposedVulnerableVMs {
  graphSearch(
    first: 20
    projectId: "*"
    query: {
      type: [VIRTUAL_MACHINE]
      select: true
      where: {
        hasPublicIp: {EQUALS: true}
      }
      relationships: [{
        type: [{type: HAS_VULNERABILITY}]
        with: {
          type: [VULNERABILITY]
          where: {
            severity: {EQUALS: ["CRITICAL"]}
          }
        }
      }]
    }
  ) {
    totalCount
    nodes {
      entities {
        id
        name
        type
      }
    }
  }
}
```

### Kubernetes Coverage
```graphql
query KubernetesClusterCoverage {
  cloudResourcesV2(
    first: 0
    filterBy: {
      type: {equals: ["KUBERNETES_CLUSTER"]}
      property: [{
        propertyName: "deploymentCoverage_auditLogCollector_deploymentStatus"
        valueFilter: {stringArrayFilter: {containsAny: ["Installed"]}}
      }]
    }
  ) {
    totalCount
  }
}
```

---

## 3. Best Practices

1. **Always Request `totalCount`**: For list queries, always include `totalCount` to provide exact metrics.
2. **Paginate with `pageInfo`**: Use `pageInfo { hasNextPage endCursor }` and `first: <limit>` for clean pagination.
3. **Field Economy**: Fetch only the fields needed to minimize latency and response payload size.
4. **Reference Guide**: Consult [`docs/WIZ_API_REFERENCE.md`](../../docs/WIZ_API_REFERENCE.md) for 3,000+ lines of query recipes.
