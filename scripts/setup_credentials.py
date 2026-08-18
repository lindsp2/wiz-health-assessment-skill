#!/usr/bin/env python3
"""
Wiz & Google Cloud Credentials Setup Wizard
============================================
Interactive setup tool to:
1. Guide you through entering your Wiz Service Account credentials locally.
2. Verify live connectivity to the Wiz GraphQL API.
3. Configure Google Slides / Drive API credentials (optional).
4. Generate a sanitized, local .env file.
"""

import getpass
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from console_compat import enable_unicode_output, python_command

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent

enable_unicode_output()

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
    print("\n🔒 Security Notice: Credentials entered here are saved ONLY to your")
    print("   local .env file on disk and are never shared or sent to any LLM.\n")

    # 1. Datacenter Guidance
    print("--- 1. Wiz Datacenter ---")
    print("To find your Tenant Data Center:")
    print("  Navigate to: https://app.wiz.io/tenant-info/data-center-and-regions")
    print("  Look for the 'Tenant Data Center' result (e.g. us1, us2, us20, us100, eu1, gov).\n")

    dc_input = input("Enter your Wiz Datacenter [default: us1]: ").strip().lower()
    datacenter = dc_input if dc_input else "us1"

    auth_url = "https://auth.wiz.io/oauth/token"
    api_endpoint = f"https://api.{datacenter}.app.wiz.io/graphql"

    # 2. Service Account Guidance
    print("\n--- 2. Wiz Service Account Credentials ---")
    print("To create your Service Account:")
    print("  1. Access: https://app.wiz.io/settings/service-accounts/new")
    print("  2. Input a recognizable name for the Service Account")
    print("  3. Select '</> Custom Integration (GraphQL API)' from the Type dropdown")
    print("  4. Select 'Read all entities (read:all)' as the API scope")
    print("  5. Click on 'Add Service Account'")
    print("  6. Copy the Client ID and Client Secret")
    print("  7. Click 'Finish'\n")

    client_id = input("Enter Wiz Service Account Client ID: ").strip()
    client_secret = getpass.getpass("Enter Wiz Service Account Client Secret (input hidden): ").strip()

    if not client_secret:
        # Fallback to regular input if getpass has issues in certain terminals
        client_secret = input("Enter Wiz Service Account Client Secret: ").strip()

    if not (client_id and client_secret):
        print("[!] Client ID and Client Secret are required.")
        sys.exit(1)

    success, tenant_name = test_wiz_connection(auth_url, client_id, client_secret, api_endpoint)
    if not success:
        print("[!] Connection test failed. Please verify your credentials and datacenter.")
        sys.exit(1)

    # 3. Google Slides Credentials (Optional)
    print("\n--- 3. Google Slides / Drive Setup (Optional) ---")
    print("Note: PowerPoint (.pptx) generation works with ZERO Google setup.")
    print("Only configure Google OAuth if you specifically want live Google Slides decks.")
    setup_google = input("Do you want to configure Google Slides credentials now? [y/N]: ").strip().lower()

    google_client_id = ""
    google_client_secret = ""
    google_refresh_token = ""
    google_folder_id = ""

    if setup_google == "y":
        google_client_id = input("Enter Google Client ID: ").strip()
        google_client_secret = getpass.getpass("Enter Google Client Secret (hidden): ").strip() or input("Enter Google Client Secret: ").strip()
        google_refresh_token = getpass.getpass("Enter Google Refresh Token (hidden): ").strip() or input("Enter Google Refresh Token: ").strip()
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

# Google Slides & Drive (Optional)
GOOGLE_CLIENT_ID={google_client_id}
GOOGLE_CLIENT_SECRET={google_client_secret}
GOOGLE_REFRESH_TOKEN={google_refresh_token}
GOOGLE_FOLDER_ID={google_folder_id}
QBR_TEMPLATE_ID=1ga4sflsBPZS2lsXi6k6fUY1jU5dOrqQ9bQ1JEp3B5GM
"""

    # Write beside the repo rather than into the current directory, so the file
    # lands where every other script looks for it no matter where this was run.
    env_path = REPO_DIR / ".env"
    env_path.write_text(env_content, encoding="utf-8")
    print(f"\n[✓] Successfully saved configuration to {env_path}")
    print("\nYou are ready to generate presentations:")
    print(f"  {python_command()} scripts/generate_deck.py --format pptx --customer \"{tenant_name or 'My Customer'}\"")

if __name__ == "__main__":
    main()
