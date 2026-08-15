# Wiz Service Account Setup Guide

This guide walks you through creating a dedicated, read-only Wiz Service Account to authenticate with the Wiz GraphQL API.

---

## 1. Prerequisites
* **Wiz Portal Access**: You need an account in your organization's Wiz Portal with permissions to manage Service Accounts (typically **Global Admin** or **Settings Admin**).

---

## 2. Step-by-Step Creation

1. **Log in to the Wiz Portal**: Navigate to your tenant URL (e.g., `https://app.wiz.io` or `https://gov.wiz.io`).
2. **Open Settings**: Click the **Settings (Gear Icon)** in the left navigation sidebar.
3. **Navigate to Service Accounts**: Under the **Access Management** section, select **Service Accounts**.
4. **Create New Service Account**:
   * Click **+ Add Service Account** in the top right corner.
   * **Name**: Enter a descriptive name (e.g. `Health-Assessment-Auditor` or `Executive-Deck-Builder`).
   * **Account Type**: Select **Service Account (OAuth 2.0 / API)**.
5. **Assign Scopes / Permissions**:
   * For health assessments and deck generation, assign the **`read:all`** permission (or **Global Viewer** / **Read Only** role).
   * *Note*: Write/mutation permissions are not required.
6. **Generate Credentials**:
   * Click **Create**.
   * **Important**: Copy the **Client ID** and **Client Secret** immediately. The client secret will not be shown again.

---

## 3. Identify Your Data Center & API Endpoint

Wiz hosts tenants across several regional data centers. Identify your datacenter code from your browser URL:

| Data Center | Region / Cloud | GraphQL API Endpoint |
|---|---|---|
| `us1` | US Commercial (AWS us-east-1) | `https://api.us1.app.wiz.io/graphql` |
| `us2` | US Commercial (Azure East US) | `https://api.us2.app.wiz.io/graphql` |
| `us20` | US Commercial (GCP us-central1) | `https://api.us20.app.wiz.io/graphql` |
| `us100` | US Commercial | `https://api.us100.app.wiz.io/graphql` |
| `eu1` | Europe (AWS eu-central-1) | `https://api.eu1.app.wiz.io/graphql` |
| `gov` | US GovCloud / FedRAMP | `https://api.gov.wiz.io/graphql` |

---

## 4. Configure Your `.env` File

Add your credentials to `.env`:

```bash
WIZ_AUTH_URL=https://auth.wiz.io/oauth/token
WIZ_DATACENTER=us1
WIZ_API_ENDPOINT=https://api.us1.app.wiz.io/graphql
WIZ_CLIENT_ID=your_client_id_here
WIZ_CLIENT_SECRET=your_client_secret_here
```

Test your credentials using the built-in setup wizard:
```bash
python3 scripts/setup_credentials.py
```
