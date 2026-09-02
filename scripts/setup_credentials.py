#!/usr/bin/env python3
"""
Wiz Credentials Setup Wizard
============================
Interactive setup tool to:
1. Guide you through entering your Wiz Service Account credentials locally.
2. Verify live connectivity to the Wiz GraphQL API.
3. Generate a sanitized, local .env file.

The PDF deck is rendered offline via LibreOffice - no Google account or OAuth is
required, so this wizard does not ask for any Google credentials.
"""

import getpass
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from console_compat import enable_unicode_output, python_command, default_env_write_path

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

    # 1. Customer Name
    print("--- 1. Customer Name ---")
    customer_input = input("Enter Customer Name for reports & presentations [default: My Company]: ").strip()
    customer_name = customer_input if customer_input else "My Company"

    # 2. Datacenter Guidance
    print("\n--- 2. Wiz Datacenter ---")
    print("To find your Tenant Data Center:")
    print("  Navigate to: https://app.wiz.io/tenant-info/data-center-and-regions")
    print("  Look for the 'Tenant Data Center' result (e.g. us1, us2, us20, us100, eu1, gov).\n")

    dc_input = input("Enter your Wiz Datacenter [default: us1]: ").strip().lower()
    datacenter = dc_input if dc_input else "us1"

    auth_url = "https://auth.app.wiz.io/oauth/token"
    api_endpoint = f"https://api.{datacenter}.app.wiz.io/graphql"

    # 3. Service Account Guidance
    print("\n--- 3. Wiz Service Account Credentials ---")
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

    # The PDF deck is rendered offline via LibreOffice, so no Google/OAuth config is
    # written. Only if the user has ALREADY set up the advanced --format slides path
    # (Google creds present in an existing .env) do we preserve those lines verbatim.
    # In plugin mode the repo dir is Claude-managed; write the .env where the user
    # owns it (their project dir / cwd). In clone mode this is the repo root.
    env_path = default_env_write_path(REPO_DIR)
    existing_vars = {}
    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing_vars[k.strip()] = v.strip().strip("\"'")

    # Write .env file
    env_content = f"""# ==============================================================================
# Wiz Tenant Health Assessment - Local Environment Configuration
# Generated via scripts/setup_credentials.py
# ==============================================================================

# Customer
CUSTOMER_NAME={customer_name}

# Wiz API
WIZ_AUTH_URL={auth_url}
WIZ_DATACENTER={datacenter}
WIZ_API_ENDPOINT={api_endpoint}
WIZ_CLIENT_ID={client_id}
WIZ_CLIENT_SECRET={client_secret}
"""

    # Preserve pre-existing Google credentials only if the user already had them
    # (advanced --format slides users). We never create empty Google placeholders.
    google_keys = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN",
                   "GOOGLE_FOLDER_ID", "QBR_TEMPLATE_ID"]
    google_present = {k: existing_vars[k] for k in google_keys if existing_vars.get(k)}
    if google_present:
        env_content += "\n# Advanced (optional): Google Slides output (--format slides) - preserved from prior .env\n"
        for k in google_keys:
            if k in google_present:
                env_content += f"{k}={google_present[k]}\n"

    env_path.write_text(env_content, encoding="utf-8")
    print(f"\n[✓] Successfully saved configuration to {env_path}")
    print("\nYou are ready to run your Health Assessment:")
    print(f"  {python_command()} scripts/generate_deck.py --format csv --customer \"{customer_name}\"")
    print("  (add --format pdf for the offline LibreOffice-rendered executive deck)")

if __name__ == "__main__":
    main()
