#!/usr/bin/env python
"""Create an InfluxDB datasource in Grafana.

Creates a datasource configuration in Grafana pointing to an InfluxDB database.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request


def main() -> None:
    """Create InfluxDB datasource in Grafana."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
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
        "--influxdb-url",
        default="http://influxdb:8086",
        help="InfluxDB URL as seen from Grafana (default: http://influxdb:8086)",
    )
    parser.add_argument(
        "--database",
        default="sgneskig_metrics",
        help="InfluxDB database name (default: sgneskig_metrics)",
    )
    parser.add_argument(
        "--name",
        help="Datasource name in Grafana (default: same as --database)",
    )

    args = parser.parse_args()

    datasource_name = args.name or args.database

    # Build datasource config
    datasource = {
        "name": datasource_name,
        "type": "influxdb",
        "access": "proxy",
        "url": args.influxdb_url,
        "database": args.database,
        "basicAuth": False,
        "jsonData": {"httpMode": "POST"},
    }

    # Make request
    url = f"{args.grafana_url}/api/datasources"
    payload = json.dumps(datasource).encode()

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")

    auth_bytes = args.grafana_auth.encode()
    auth_b64 = base64.b64encode(auth_bytes).decode()
    req.add_header("Authorization", f"Basic {auth_b64}")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"Created datasource: {result.get('name', datasource_name)}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            result = json.loads(body)
            message = result.get("message", body)
        except json.JSONDecodeError:
            message = body

        if "already exists" in message.lower():
            print(f"Datasource '{datasource_name}' already exists")
        else:
            print(f"Error: {message}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
