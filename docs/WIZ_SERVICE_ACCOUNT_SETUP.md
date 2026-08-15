# Wiz Service Account & Datacenter Setup Guide

This guide walks you through finding your tenant datacenter and creating a dedicated, read-only Wiz Service Account to authenticate with the Wiz GraphQL API.

---

## 🔒 Security Notice
* **Never share or paste your Client Secret in chat conversations or public repositories.**
* Credentials should be stored strictly in your local `.env` file (which is gitignored).

---

## 1. How to Identify Your Wiz Datacenter

Wiz hosts tenants across several regional cloud data centers. You need your datacenter identifier to construct the correct GraphQL API endpoint.

### Method 1: Check your Browser Address Bar
Log in to your Wiz Portal and look at the URL in your address bar:

| If your Wiz URL is... | Your Datacenter is... | GraphQL API Endpoint |
|---|---|---|
| `https://app.wiz.io` or `https://us1.app.wiz.io` | `us1` (US Commercial - AWS) | `https://api.us1.app.wiz.io/graphql` |
| `https://us2.app.wiz.io` | `us2` (US Commercial - Azure) | `https://api.us2.app.wiz.io/graphql` |
| `https://us20.app.wiz.io` | `us20` (US Commercial - GCP) | `https://api.us20.app.wiz.io/graphql` |
| `https://us100.app.wiz.io` | `us100` (US Commercial) | `https://api.us100.app.wiz.io/graphql` |
| `https://eu1.app.wiz.io` | `eu1` (Europe - AWS) | `https://api.eu1.app.wiz.io/graphql` |
| `https://gov.wiz.io` | `gov` (US GovCloud / FedRAMP) | `https://api.gov.wiz.io/graphql` |

### Method 2: Check Tenant Details in Portal
1. In the Wiz Portal, click **Settings (Gear Icon)** in the left sidebar.
2. Click **General > Tenant Details**.
3. View the **Region / Datacenter** field.

---

## 2. How to Generate a Wiz Service Account

1. **Open Settings**: Log in to the Wiz Portal and click the **Settings (Gear Icon)** in the left navigation sidebar.
2. **Navigate to Service Accounts**: Under the **Access Management** section, select **Service Accounts**.
3. **Create New Service Account**:
   * Click the blue **+ Add Service Account** button in the top right corner.
   * **Name**: Enter a descriptive name (e.g. `Health-Assessment-Skill`).
   * **Account Type**: Select **Service Account (OAuth 2.0 / API)**.
4. **Assign Scopes / Permissions**:
   * Under Roles / Permissions, assign the **Global: Security Read Only** role (or `read:all` scope).
   * *Note*: No write or mutation permissions are required.
5. **Generate Credentials**:
   * Click **Create**.
   * **Important**: Copy the **Client ID** and **Client Secret** immediately. Wiz will not display the client secret again.

---

## 3. Configure Your Local `.env` File

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Wiz Authentication OAuth Endpoint
WIZ_AUTH_URL=https://auth.wiz.io/oauth/token

# Wiz Data Center / Region Identifier (e.g. us1, us2, us20, us100, eu1, gov)
WIZ_DATACENTER=us1

# Direct Wiz GraphQL API Endpoint
WIZ_API_ENDPOINT=https://api.us1.app.wiz.io/graphql

# Wiz Service Account Credentials
WIZ_CLIENT_ID=your_client_id_here
WIZ_CLIENT_SECRET=your_client_secret_here
```

---

## 4. Test Connectivity Locally

Run the setup wizard in your terminal:
```bash
python3 scripts/setup_credentials.py
```
This will perform a live read query to confirm your credentials are valid and display the connected tenant name.
