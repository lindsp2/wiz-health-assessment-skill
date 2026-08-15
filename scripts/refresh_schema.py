#!/usr/bin/env python3
"""
Wiz Schema Refresh & Introspection Tool
Fetches and saves the full GraphQL introspection schema for offline analysis.
"""

import argparse
import json
import sys
from pathlib import Path
from wiz_client import WizClient

INTROSPECTION_QUERY = """
query FullIntrospection {
  __schema {
    queryType { name }
    mutationType { name }
    types {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          name
          description
          type {
            kind
            name
            ofType { kind name }
          }
        }
        type {
          kind
          name
          ofType { kind name }
        }
      }
    }
  }
}
"""

def main():
    parser = argparse.ArgumentParser(description="Download Wiz GraphQL Schema Introspection")
    parser.add_argument("-o", "--output", default="wiz-schema-introspection.json", help="Output JSON path")
    parser.add_argument("--env-file", help="Path to .env file")
    args = parser.parse_args()

    client = WizClient(env_file=args.env_file)
    print(f"Connecting to Wiz API ({client.api_endpoint}) and fetching introspection...")
    
    try:
        data = client.execute_query(INTROSPECTION_QUERY)
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Successfully saved introspection schema to {out_path.resolve()}")
    except Exception as e:
        sys.stderr.write(f"Failed to fetch schema: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
