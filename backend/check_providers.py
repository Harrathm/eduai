import json
from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    r = conn.execute(text("SELECT id, key, value FROM platform_settings WHERE key = 'ai_providers_config'"))
    for row in r:
        print(f"id={row[0]}, key={row[1]}")
        config = json.loads(row[2])
        for pid, pcfg in config.items():
            enabled = pcfg.get('enabled', False)
            has_key = bool(pcfg.get('key', ''))
            print(f"  {pid}: enabled={enabled}, has_key={has_key}, model={pcfg.get('model','')}")
