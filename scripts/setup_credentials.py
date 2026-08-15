#!/usr/bin/env python3
"""
Wiz & Google Cloud Credentials Setup Wizard
============================================
Interactive setup tool to:
1. Guide you through entering your Wiz Service Account credentials.
2. Verify live connectivity to the Wiz GraphQL API.
3. Configure Google Slides / Drive API credentials (optional).
4. Generate a sanitized, local .env file.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

def test_wiz_connection(auth_url, client_id, client_secret, api_endpoint):
    print("\n[*] Testing connection to Wiz GraphQL API...")
    auth_data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": "wiz-api"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(auth_url, data=auth_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            token = json.loads(resp.read()).get("access_token")
    except Exception as e:
        print(f"[!] Authentication failed: {e}")
        return False, None

    test_query = """
    query TestConnection {
      viewerV2 {
        tenant {
          id
          name
        }
      }
    }
    """
    try:
        req = urllib.request.Request(
            api_endpoint,
            data=json.dumps({"query": test_query}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read())
            tenant = ((res.get("data", {}).get("viewerV2", {}) or {}).get("tenant", {}) or {})
            tenant_name = tenant.get("name")
            tenant_id = tenant.get("id")
            if tenant_name:
                print(f"[✓] Connected successfully to tenant: {tenant_name} ({tenant_id})")
                return True, tenant_name
    except Exception as e:
        print(f"[!] Query failed: {e}")
        return False, None

    return False, None

def main():
    print("=======================================================")
    print("     WIZ CREDENTIALS & ENVIRONMENT SETUP WIZARD        ")
    print("=======================================================")

    print("\nThis wizard will configure your local .env file.")
    print("Prerequisites: A Wiz Service Account with read:all scope.")
    print("Guide: See docs/WIZ_SERVICE_ACCOUNT_SETUP.md for instructions.\n")

    # 1. Wiz Datacenter
    dc_input = input("Enter your Wiz Datacenter [default: us1] (e.g. us1, us2, us20, us100, eu1, gov): ").strip()
    datacenter = dc_input if dc_input else "us1"

    auth_url = "https://auth.wiz.io/oauth/token"
    api_endpoint = f"https://api.{datacenter}.app.wiz.io/graphql"

    # 2. Wiz Credentials
    client_id = input("Enter Wiz Service Account Client ID: ").strip()
    client_secret = input("Enter Wiz Service Account Client Secret: ").strip()

    if not (client_id and client_secret):
        print("[!] Client ID and Client Secret are required.")
        sys.exit(1)

    success, tenant_name = test_wiz_connection(auth_url, client_id, client_secret, api_endpoint)
    if not success:
        print("[!] Please verify your credentials, datacenter, and network access.")
        sys.exit(1)

    # 3. Google Slides Credentials (Optional)
    print("\n--- Google Slides / Drive Setup (Optional) ---")
    print("To generate live Google Slides presentations, configure Google Cloud OAuth.")
    print("Guide: See docs/GOOGLE_SLIDES_SETUP.md for instructions.")
    setup_google = input("Do you want to configure Google Slides credentials now? [y/N]: ").strip().lower()

    google_client_id = ""
    google_client_secret = ""
    google_refresh_token = ""
    google_folder_id = ""

    if setup_google == "y":
        google_client_id = input("Enter Google Client ID: ").strip()
        google_client_secret = input("Enter Google Client Secret: ").strip()
        google_refresh_token = input("Enter Google Refresh Token: ").strip()
        google_folder_id = input("Enter Target Google Drive Folder ID (optional): ").strip()

    # 4. Write .env file
    env_content = f"""# ==============================================================================
# Wiz Tenant Health Assessment - Local Environment Configuration
# Generated via scripts/setup_credentials.py
# ==============================================================================

# Wiz API
WIZ_AUTH_URL={auth_url}
WIZ_DATACENTER={datacenter}
WIZ_API_ENDPOINT={api_endpoint}
WIZ_CLIENT_ID={client_id}
WIZ_CLIENT_SECRET={client_secret}

# Google Slides & Drive
GOOGLE_CLIENT_ID={google_client_id}
GOOGLE_CLIENT_SECRET={google_client_secret}
GOOGLE_REFRESH_TOKEN={google_refresh_token}
GOOGLE_FOLDER_ID={google_folder_id}
QBR_TEMPLATE_ID=1ga4sflsBPZS2lsXi6k6fUY1jU5dOrqQ9bQ1JEp3B5GM
"""

    env_path = Path.cwd() / ".env"
    env_path.write_text(env_content, encoding="utf-8")
    print(f"\n[✓] Successfully saved configuration to {env_path}")
    print("\nYou are ready to run:")
    print("  python3 scripts/generate_deck.py --customer \"" + (tenant_name or "My Customer") + "\"")

if __name__ == "__main__":
    main()
