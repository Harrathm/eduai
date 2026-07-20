from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    r = conn.execute(text("SELECT key, LEFT(value, 120) as val FROM platform_settings WHERE key IN ('ai_providers_config', 'openai_api_key', 'ai_generation_cost_lesson')"))
    for row in r:
        print(f"  {row[0]}: {row[1]}")
