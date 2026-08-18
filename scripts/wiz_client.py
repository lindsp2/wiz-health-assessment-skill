#!/usr/bin/env python3
"""
Wiz GraphQL Client CLI
A self-contained, zero-dependency Python utility for authenticating, querying,
paginating, and searching the Wiz GraphQL API.
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from console_compat import enable_unicode_output

enable_unicode_output()


class WizClient:
    def __init__(self, auth_url=None, api_endpoint=None, client_id=None, client_secret=None, env_file=None):
        if env_file:
            self._load_env_file(env_file)
        
        self.auth_url = auth_url or os.environ.get("WIZ_AUTH_URL", "https://auth.app.wiz.io/oauth/token")
        self.client_id = client_id or os.environ.get("WIZ_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("WIZ_CLIENT_SECRET")
        datacenter = os.environ.get("WIZ_DATACENTER", "us100")
        
        default_endpoint = f"https://api.{datacenter}.app.wiz.io/graphql"
        self.api_endpoint = api_endpoint or os.environ.get("WIZ_API_ENDPOINT") or os.environ.get("WIZ_API_URL", default_endpoint)

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Missing Wiz credentials. Please set WIZ_CLIENT_ID and WIZ_CLIENT_SECRET "
                "environment variables or provide a valid .env file."
            )

        self.cache_dir = Path.home() / ".cache" / "wiz"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        id_hash = hashlib.sha256(self.client_id.encode()).hexdigest()[:12]
        self.token_cache_file = self.cache_dir / f"token_{id_hash}.json"

    def _load_env_file(self, filepath):
        p = Path(filepath)
        if not p.is_file():
            return
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("\"'")
                if k not in os.environ:
                    os.environ[k] = v

    def get_token(self, force_refresh=False):
        if not force_refresh and self.token_cache_file.is_file():
            try:
                with open(self.token_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 5-minute safety buffer before expiry
                    if data.get("expires_at", 0) > time.time() + 300:
                        return data["access_token"]
            except Exception:
                pass

        payload = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": "wiz-api"
        }).encode("utf-8")

        req = urllib.request.Request(
            self.auth_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "WizClient/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                token = res_data["access_token"]
                expires_in = res_data.get("expires_in", 86400)
                cache_payload = {
                    "access_token": token,
                    "expires_at": time.time() + expires_in
                }
                with open(self.token_cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_payload, f)
                return token
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Authentication failed ({e.code}): {err_body}")

    def execute_query(self, query_str, variables=None, retry_auth=True, max_retries=3):
        variables = variables or {}
        token = self.get_token()

        for attempt in range(max_retries):
            body = json.dumps({"query": query_str, "variables": variables}).encode("utf-8")
            req = urllib.request.Request(
                self.api_endpoint,
                data=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "User-Agent": "WizClient/1.0"
                }
            )

            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                if e.code == 401 and retry_auth:
                    token = self.get_token(force_refresh=True)
                    retry_auth = False
                    continue
                elif e.code == 429:
                    sleep_sec = 2 ** (attempt + 1)
                    time.sleep(sleep_sec)
                    continue
                else:
                    raise RuntimeError(f"GraphQL request failed ({e.code}): {err_body}")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)

        raise RuntimeError("GraphQL request exceeded maximum retries.")

    def search_schema(self, keyword):
        query = """
        query IntrospectAllQueries {
          __schema {
            queryType {
              fields {
                name
                description
              }
            }
          }
        }
        """
        result = self.execute_query(query)
        fields = result.get("data", {}).get("__schema", {}).get("queryType", {}).get("fields", [])
        matches = []
        kw = keyword.lower()
        for f in fields:
            name = f.get("name", "")
            desc = f.get("description") or ""
            if kw in name.lower() or kw in desc.lower():
                matches.append({"name": name, "description": desc.strip()})
        return matches


def main():
    parser = argparse.ArgumentParser(description="Wiz GraphQL API CLI Client")
    parser.add_argument("-q", "--query", help="GraphQL query string")
    parser.add_argument("-f", "--file", help="Path to .graphql query file")
    parser.add_argument("-v", "--variables", help="JSON string of query variables")
    parser.add_argument("--env-file", help="Path to .env file containing credentials")
    parser.add_argument("--search-schema", help="Search schema queries for a keyword")
    parser.add_argument("--raw", action="store_true", help="Print raw unformatted JSON")
    args = parser.parse_args()

    try:
        client = WizClient(env_file=args.env_file)
    except Exception as e:
        sys.stderr.write(f"Initialization Error: {e}\n")
        sys.exit(1)

    if args.search_schema:
        print(f"Searching schema for '{args.search_schema}'...")
        matches = client.search_schema(args.search_schema)
        print(f"Found {len(matches)} matching queries:")
        for m in matches:
            print(f"  - {m['name']}: {m['description'][:120]}")
        sys.exit(0)

    query_str = args.query
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            query_str = f.read()

    if not query_str:
        if not sys.stdin.isatty():
            query_str = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)

    vars_dict = {}
    if args.variables:
        try:
            vars_dict = json.loads(args.variables)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Invalid variables JSON: {e}\n")
            sys.exit(1)

    try:
        result = client.execute_query(query_str, vars_dict)
        if args.raw:
            print(json.dumps(result))
        else:
            print(json.dumps(result, indent=2))
    except Exception as e:
        sys.stderr.write(f"Execution Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
