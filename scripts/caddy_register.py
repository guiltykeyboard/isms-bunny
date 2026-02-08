#!/usr/bin/env python3
"""
Minimal helper to register a tenant hostname with Caddy's JSON API.
Usage:
  CADDY_API=http://caddy:2019 python scripts/caddy_register.py tenant.example.com http://app:8000
This is intentionally small; production setups should add auth/tokens and idempotent checks.
"""
import os
import sys

import requests

API = os.environ.get("CADDY_API", "http://localhost:2019")


def main():
    if len(sys.argv) < 3:
        print("usage: caddy_register.py <host> <upstream>")
        sys.exit(1)
    host, upstream = sys.argv[1], sys.argv[2]
    route = {
        "@id": f"route-{host}",
        "match": [{"host": [host]}],
        "handle": [
            {
                "handler": "reverse_proxy",
                "upstreams": [
                    {
                        "dial": upstream.replace("http://", "").replace("https://", ""),
                    }
                ],
            }
        ],
    }
    response = requests.post(
        f"{API}/config/apps/http/servers/srv0/routes",
        json=[route],
        timeout=10,
    )
    response.raise_for_status()
    print(f"Registered {host} -> {upstream} (status {response.status_code})")


if __name__ == "__main__":
    main()
