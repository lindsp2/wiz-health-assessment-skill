# Wiz Service Account & Datacenter Setup Guide

This guide walks you through finding your tenant datacenter and creating a dedicated, read-only Wiz Service Account to authenticate with the Wiz GraphQL API.

---

## 🔒 Security Notice
* **Never share or paste your Client Secret in chat conversations or public repositories.**
* Credentials should be stored strictly in your local `.env` file on disk (which is gitignored).

---

## 1. How to Find Your Wiz Datacenter

1. In your browser, navigate to: [https://app.wiz.io/tenant-info/data-center-and-regions](https://app.wiz.io/tenant-info/data-center-and-regions)
2. Locate the **Tenant Data Center** result (e.g. `us1`, `us2`, `us20`, `us100`, `eu1`, `gov`).

---

## 2. How to Generate the Wiz Service Account

1. In the Wiz Portal, access the Service Account creation page: [https://app.wiz.io/settings/service-accounts/new](https://app.wiz.io/settings/service-accounts/new)
2. Input a recognizable name for the Service Account (e.g. `Health-Assessment-Skill`).
3. Select `</> Custom Integration (GraphQL API)` from the **Type** dropdown.
4. Select `Read all entities (read:all)` as the **API scope**.
5. Click on **Add Service Account**.
6. Take note of the **Client ID** and **Client Secret** (these will be used in your local `.env` file).
7. Click **Finish**.

---

## 3. Configure Your Local `.env` File

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Wiz Authentication OAuth Endpoint (default: https://auth.app.wiz.io/oauth/token)
WIZ_AUTH_URL=https://auth.app.wiz.io/oauth/token

# Wiz Data Center Identifier (e.g. us1, us2, us20, us100, eu1, gov)
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
