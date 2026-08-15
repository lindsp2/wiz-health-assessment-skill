# Wiz Model Context Protocol (MCP) Installation & Setup Guide

This guide provides step-by-step instructions for connecting the **Wiz MCP Server** (`https://mcp.app.wiz.io`) to any MCP-compatible AI agent or developer tool, including Claude Desktop, Claude Code, Cursor, VS Code, ChatGPT, and Antigravity.

---

## Table of Contents
1. [Overview & Architecture](#1-overview--architecture)
2. [Prerequisites in the Wiz Portal](#2-prerequisites-in-the-wiz-portal)
3. [Configuration by Platform](#3-configuration-by-platform)
   - [Claude Desktop](#a-claude-desktop)
   - [Claude Code (CLI)](#b-claude-code-cli)
   - [Cursor IDE / Windsurf](#c-cursor-ide--windsurf)
   - [VS Code (Cline / Roo-Code / Continue)](#d-vs-code-cline--roo-code--continue)
   - [ChatGPT Custom Actions / OpenAI Assistants](#e-chatgpt-custom-actions--openai-assistants)
   - [Google Antigravity & Jetski](#f-google-antigravity--jetski)
4. [Using an MCP Stdio-to-SSE Bridge (Optional)](#4-using-an-mcp-stdio-to-sse-bridge-optional)
5. [Verification & Testing](#5-verification--testing)
6. [Troubleshooting & FAQs](#6-troubleshooting--faqs)

---

## 1. Overview & Architecture

The **Wiz MCP Server** provides over 130 pre-built tools that allow AI assistants to securely query cloud security posture, vulnerabilities, inventory, identity entitlements, threat events, and system settings directly from Wiz.

- **Server Endpoint:** `https://mcp.app.wiz.io`
- **Transport:** Server-Sent Events (SSE) / Streamable HTTP
- **Authentication:** Service Account Headers (`Wiz-Client-Id`, `Wiz-Client-Secret`, `Wiz-DataCenter`) or OAuth 2.0.

---

## 2. Prerequisites in the Wiz Portal

Before connecting your client, create a Service Account in your Wiz tenant:

1. Log in to your **Wiz Portal** (`https://app.wiz.io` or regional URL).
2. Go to **Settings (gear icon) > Service Accounts**.
3. Click **+ Add Service Account**.
4. Configure the Service Account:
   - **Name:** `AI-Agent-MCP-Integration` (or descriptive name)
   - **Access / Role:** Select `Global Read-Only` or `read:all` (or custom granular permissions).
   - **Allowed API Scopes:** Ensure GraphQL API access is enabled.
5. Click **Create** and immediately copy and store the generated credentials:
   - **Client ID** (e.g., `zzlohuyel...`)
   - **Client Secret** (e.g., `jXC8GFeAX...`)
6. Identify your **Data Center** code from your browser URL:
   - `https://app.wiz.io` $\rightarrow$ `us1`
   - `https://us20.app.wiz.io` $\rightarrow$ `us20`
   - `https://us100.app.wiz.io` $\rightarrow$ `us100`
   - `https://eu1.app.wiz.io` $\rightarrow$ `eu1`
   - `https://gov.wiz.io` $\rightarrow$ `gov`

---

## 3. Configuration by Platform

### A. Claude Desktop

Edit your Claude Desktop configuration file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Add the `wiz-mcp` server entry:

```json
{
  "mcpServers": {
    "wiz-mcp": {
      "url": "https://mcp.app.wiz.io",
      "headers": {
        "Wiz-Client-Id": "YOUR_WIZ_CLIENT_ID",
        "Wiz-Client-Secret": "YOUR_WIZ_CLIENT_SECRET",
        "Wiz-DataCenter": "YOUR_DATACENTER_CODE"
      }
    }
  }
}
```

Restart Claude Desktop. The hammer icon in Claude Desktop will display the Wiz MCP tool library.

---

### B. Claude Code (CLI)

Run the following command from your terminal:

```bash
claude mcp add wiz-mcp https://mcp.app.wiz.io   --header "Wiz-Client-Id: YOUR_WIZ_CLIENT_ID"   --header "Wiz-Client-Secret: YOUR_WIZ_CLIENT_SECRET"   --header "Wiz-DataCenter: YOUR_DATACENTER_CODE"
```

Verify connection:
```bash
claude mcp list
```

---

### C. Cursor IDE / Windsurf

1. Open Cursor **Settings** (`Cmd+,` or `Ctrl+,`).
2. Navigate to **Features > MCP Servers** (or **Tools > MCP**).
3. Click **+ Add New MCP Server**.
4. Configure the server fields:
   - **Name:** `wiz-mcp`
   - **Type:** `sse`
   - **Server URL:** `https://mcp.app.wiz.io`
   - **Headers:**
     - `Wiz-Client-Id`: `YOUR_WIZ_CLIENT_ID`
     - `Wiz-Client-Secret`: `YOUR_WIZ_CLIENT_SECRET`
     - `Wiz-DataCenter`: `YOUR_DATACENTER_CODE`
5. Click **Save** and verify the green status indicator.

---

### D. VS Code (Cline / Roo-Code / Continue)

In your extension's MCP settings file (e.g. `cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "wiz-mcp": {
      "url": "https://mcp.app.wiz.io",
      "transport": "sse",
      "headers": {
        "Wiz-Client-Id": "YOUR_WIZ_CLIENT_ID",
        "Wiz-Client-Secret": "YOUR_WIZ_CLIENT_SECRET",
        "Wiz-DataCenter": "YOUR_DATACENTER_CODE"
      }
    }
  }
}
```

---

### E. ChatGPT Custom Actions / OpenAI Assistants

For tools requiring an OpenAPI specification or direct REST/GraphQL integration:
1. In your Custom GPT editor, click **Create new action**.
2. Configure authentication using **Custom Header** or **OAuth 2.0**:
   - Header 1: `Wiz-Client-Id`
   - Header 2: `Wiz-Client-Secret`
   - Header 3: `Wiz-DataCenter`
3. Alternatively, connect via an MCP-to-OpenAPI gateway bridge or host a serverless proxy against `https://api.<datacenter>.app.wiz.io/graphql`.

---

### F. Google Antigravity & Jetski

Add the server to your `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "wiz-mcp": {
      "serverUrl": "https://mcp.app.wiz.io",
      "url": "https://mcp.app.wiz.io",
      "headers": {
        "Wiz-Client-Id": "YOUR_WIZ_CLIENT_ID",
        "Wiz-Client-Secret": "YOUR_WIZ_CLIENT_SECRET",
        "Wiz-DataCenter": "YOUR_DATACENTER_CODE"
      }
    }
  }
}
```

---

## 4. Using an MCP Stdio-to-SSE Bridge (Optional)

If your client only supports local `stdio` processes rather than direct SSE HTTP URLs, you can run the bridge via `mcp-remote` / `npx`:

```json
{
  "mcpServers": {
    "wiz-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.app.wiz.io",
        "--header", "Wiz-Client-Id: YOUR_WIZ_CLIENT_ID",
        "--header", "Wiz-Client-Secret: YOUR_WIZ_CLIENT_SECRET",
        "--header", "Wiz-DataCenter: YOUR_DATACENTER_CODE"
      ]
    }
  }
}
```

---

## 5. Verification & Testing

Once installed, prompt your AI agent to run a simple read-only sanity check:

> *"Can you check our Wiz tenant security score and summarize the top 5 open critical issues?"*

Expected behavior:
1. The agent calls `get_security_score` $\rightarrow$ returns overall score.
2. The agent calls `list_issues` with `{ "filterBy": { "severity": ["CRITICAL"], "status": ["OPEN"] }, "limit": 5 }`.
3. The agent formats the output into a clear, actionable summary.

---

## 6. Troubleshooting & FAQs

### Error: `401 Unauthorized`
- **Cause:** Invalid Client ID or Secret, or the Service Account was revoked.
- **Fix:** Re-generate the Service Account secret in the Wiz Portal and update your configuration.

### Error: `403 Forbidden` / `Missing Permissions`
- **Cause:** The Service Account lacks the required role or scope for the tool being called.
- **Fix:** Ensure the Service Account has `Global Read-Only` or specific read permissions for the target domain in Wiz Portal.

### Error: `Invalid DataCenter` / `Tenant Not Found`
- **Cause:** The `Wiz-DataCenter` header does not match your tenant's actual hosting region.
- **Fix:** Check the domain in your browser when logged into Wiz (e.g. `app.wiz.io` $\rightarrow$ `us1`, `us20.app.wiz.io` $\rightarrow$ `us20`).

### Error: SSE Connection Timeout
- **Cause:** Corporate proxy or firewall blocking streaming HTTP/SSE connections.
- **Fix:** Ensure outbound HTTPS traffic to `https://mcp.app.wiz.io` on port 443 is allowed.
