from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Remove duplicate ai_providers_config entries
    r = conn.execute(text("SELECT id, key, LEFT(value, 80) as val FROM platform_settings WHERE key = 'ai_providers_config'"))
    rows = r.fetchall()
    print(f"Found {len(rows)} ai_providers_config entries:")
    for row in rows:
        print(f"  id={row[0]}: {row[2]}")
    
    # Keep only the one with actual keys, delete the other
    if len(rows) > 1:
        # Find the one with actual data
        keep_id = None
        for row in rows:
            if 'gsk_' in str(row[2]) or '"enabled":true' in str(row[2]):
                keep_id = row[0]
                break
        if keep_id is None:
            keep_id = rows[-1][0]  # keep last one
        
        delete_ids = [row[0] for row in rows if row[0] != keep_id]
        for did in delete_ids:
            conn.execute(text(f"DELETE FROM platform_settings WHERE id = {did}"))
            print(f"  Deleted duplicate id={did}")
        conn.commit()
        print(f"  Kept id={keep_id}")
    else:
        print("  Only one entry, nothing to clean")
