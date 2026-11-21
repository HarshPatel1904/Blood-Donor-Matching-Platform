import argparse
import json
import sqlite3
import sys
from decimal import Decimal
from pathlib import Path

import boto3

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import Config

TABLES = [
    "users",
    "donors",
    "hospitals",
    "blood_requests",
    "donor_responses",
    "notifications",
    "audit_logs",
]


def _convert_row_for_dynamo(row: dict) -> dict:
    """Converts SQLite row dict floats to Decimal for DynamoDB put_item."""
    return json.loads(json.dumps(row), parse_float=Decimal)


def migrate_sqlite_to_dynamodb(dry_run: bool = False) -> dict:
    db_path = Path(Config.SQLITE_DB_PATH)
    if not db_path.is_file():
        raise FileNotFoundError(f"SQLite database not found at: {db_path}")

    dynamodb = (
        None
        if dry_run
        else boto3.resource("dynamodb", region_name=Config.AWS_REGION)
    )
    prefix = Config.DYNAMODB_TABLE_PREFIX
    counts = {}

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        for table_name in TABLES:
            rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table_name}").fetchall()]
            dynamo_table_name = f"{prefix}{table_name}"
            table_ref = None if dry_run else dynamodb.Table(dynamo_table_name)

            migrated = 0
            for row in rows:
                item = _convert_row_for_dynamo(row)
                if not dry_run:
                    table_ref.put_item(Item=item)
                migrated += 1

            counts[dynamo_table_name] = migrated
            mode_label = "[DRY-RUN]" if dry_run else "[MIGRATED]"
            print(f"{mode_label} {dynamo_table_name}: {migrated} record(s)")
    finally:
        conn.close()

    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Idempotently migrate Stage 1 SQLite tables to Stage 2 DynamoDB."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate SQLite reads and Decimal conversions without writing to AWS.",
    )
    args = parser.parse_args()
    migrate_sqlite_to_dynamodb(dry_run=args.dry_run)
