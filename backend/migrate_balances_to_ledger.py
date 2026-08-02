"""
One-shot migration: seed WalletTransaction entries from legacy User.dt_balance / User.token_balance.

After running this script, balances are computed from the ledger.
The legacy columns can then be converted to @property.

Usage:
    python migrate_balances_to_ledger.py [--dry-run]
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models import User


def utcnow():
    return datetime.now(timezone.utc)


def migrate(dry_run: bool = False):
    with Session(engine) as db:
        users_with_balance = (
            db.query(User)
            .filter(
                ((User.dt_balance != None) & (User.dt_balance > 0.0))
                | ((User.token_balance != None) & (User.token_balance > 0))
            )
            .all()
        )

        if not users_with_balance:
            print("No users with legacy balances to migrate.")
            return

        dt_total = 0.0
        token_total = 0
        tx_count = 0
        now = utcnow().isoformat()

        for user in users_with_balance:
            dt = user.dt_balance or 0.0
            tokens = user.token_balance or 0
            meta_dt = json.dumps({"source": "migration", "reason": "Legacy dt_balance seed"})
            meta_token = json.dumps({"source": "migration", "reason": "Legacy token_balance seed"})

            if dt > 0.0:
                if dry_run:
                    print(f"  [DRY RUN] Would create DT_PURCHASED credit: user={user.id} ({user.email}) amount={dt}")
                else:
                    db.execute(text(
                        "INSERT INTO wallet_transactions (user_id, pool, amount, created_at, metadata) "
                        "VALUES (:uid, 'dt_purchased'::walletpool, :amt, :now, cast(:meta as jsonb))"
                    ).bindparams(meta=meta_dt), {"uid": user.id, "amt": int(dt), "now": now})
                    tx_count += 1
                dt_total += dt

            if tokens > 0:
                if dry_run:
                    print(f"  [DRY RUN] Would create PURCHASED credit: user={user.id} ({user.email}) amount={tokens}")
                else:
                    db.execute(text(
                        "INSERT INTO wallet_transactions (user_id, pool, amount, created_at, metadata) "
                        "VALUES (:uid, 'PURCHASED'::walletpool, :amt, :now, cast(:meta as jsonb))"
                    ).bindparams(meta=meta_token), {"uid": user.id, "amt": tokens, "now": now})
                    tx_count += 1
                token_total += tokens

        if not dry_run:
            db.commit()

        print(f"\nMigration {'(DRY RUN) ' if dry_run else ''}summary:")
        print(f"  Users processed: {len(users_with_balance)}")
        print(f"  Transactions created: {tx_count}")
        print(f"  Total DT migrated: {dt_total}")
        print(f"  Total tokens migrated: {token_total}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    print(f"{'[DRY RUN] ' if dry_run else ''}Migrating legacy balances to WalletTransaction ledger...\n")
    migrate(dry_run=dry_run)
