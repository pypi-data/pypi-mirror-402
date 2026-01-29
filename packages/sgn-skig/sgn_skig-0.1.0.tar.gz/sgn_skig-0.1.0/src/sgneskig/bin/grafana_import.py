#!/usr/bin/env python
"""Import a Grafana dashboard from a JSON file.

Imports a dashboard JSON file to Grafana, optionally overwriting existing.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request


def main() -> None:
    """Import dashboard to Grafana."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "dashboard_file",
        help="Path to dashboard JSON file",
    )
    parser.add_argument(
        "--grafana-url",
        default="http://localhost:3000",
        help="Grafana URL (default: http://localhost:3000)",
    )
    parser.add_argument(
        "--grafana-auth",
        default="admin:sgnl",
        help="Grafana auth as user:password (default: admin:sgnl)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=True,
        help="Overwrite existing dashboard (default: True)",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_false",
        dest="overwrite",
        help="Don't overwrite existing dashboard",
    )
    parser.add_argument(
        "--folder-id",
        type=int,
        default=0,
        help="Folder ID to import into (default: 0 = General)",
    )

    args = parser.parse_args()

    # Load dashboard JSON
    try:
        with open(args.dashboard_file) as f:
            dashboard = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.dashboard_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.dashboard_file}: {e}", file=sys.stderr)
        sys.exit(1)

    # Build import payload
    payload_dict = {
        "dashboard": dashboard,
        "overwrite": args.overwrite,
        "folderId": args.folder_id,
    }
    payload = json.dumps(payload_dict).encode()

    # Make request
    url = f"{args.grafana_url}/api/dashboards/db"

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")

    auth_bytes = args.grafana_auth.encode()
    auth_b64 = base64.b64encode(auth_bytes).decode()
    req.add_header("Authorization", f"Basic {auth_b64}")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            dashboard_url = result.get("url", "")
            if dashboard_url:
                print(f"Imported: {args.grafana_url}{dashboard_url}")
            else:
                print(f"Imported: {result.get('slug', 'dashboard')}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            result = json.loads(body)
            message = result.get("message", body)
        except json.JSONDecodeError:
            message = body
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
