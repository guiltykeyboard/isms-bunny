#!/usr/bin/env python
"""
Migrate tenant objects between S3-compatible buckets.

Usage (compact JSON):
  python scripts/s3_migrate.py --tenant-id <uuid> \
    --source '{"bucket":"old","region":"us-east-1","endpoint":"https://s3.wasabisys.com",...}' \
    --dest   '{"bucket":"new","region":"us-east-1","endpoint":"https://s3.wasabisys.com",...}' \
    --prefix tenants/<tenant-id>

The script copies objects under the given prefix from source to destination and
can be used for MSP-shared -> BYO, BYO -> MSP, or between BYO buckets.
"""
import argparse
import json
from typing import Any, Dict

import boto3
from botocore.client import Config


def build_client(cfg: Dict[str, Any]):
    session = boto3.session.Session(
        aws_access_key_id=cfg.get("access_key"),
        aws_secret_access_key=cfg.get("secret_key"),
        region_name=cfg.get("region"),
    )
    return session.client(
        "s3",
        endpoint_url=cfg.get("endpoint"),
        config=Config(signature_version="s3v4"),
    )


def migrate(
    prefix: str,
    source_cfg: Dict[str, Any],
    dest_cfg: Dict[str, Any],
    dry_run: bool = False,
):
    src = build_client(source_cfg)
    dst = build_client(dest_cfg)
    continuation = None
    copied = 0
    while True:
        kwargs = {"Bucket": source_cfg["bucket"], "Prefix": prefix}
        if continuation:
            kwargs["ContinuationToken"] = continuation
        resp = src.list_objects_v2(**kwargs)
        contents = resp.get("Contents", [])
        for obj in contents:
            key = obj["Key"]
            if dry_run:
                print(f"[DRY-RUN] copy {key}")
            else:
                copy_source = {"Bucket": source_cfg["bucket"], "Key": key}
                dst.copy(copy_source, dest_cfg["bucket"], key)
                print(f"copied {key}")
            copied += 1
        if not resp.get("IsTruncated"):
            break
        continuation = resp.get("NextContinuationToken")
    print(f"Done. {copied} objects {'would be ' if dry_run else ''}copied.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-id", required=False, help="Tenant UUID (for logging)")
    parser.add_argument("--prefix", required=True, help="Prefix to migrate (e.g., tenants/<id>)")
    parser.add_argument("--source", required=True, help="JSON for source S3 config")
    parser.add_argument("--dest", required=True, help="JSON for destination S3 config")
    parser.add_argument("--dry-run", action="store_true", help="List actions without copying")
    args = parser.parse_args()

    source_cfg = json.loads(args.source)
    dest_cfg = json.loads(args.dest)
    migrate(args.prefix, source_cfg, dest_cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
