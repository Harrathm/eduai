import json
from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    r = conn.execute(text("SELECT id, value FROM platform_settings WHERE key = 'ai_providers_config'"))
    row = r.fetchone()
    if row:
        config = json.loads(row[1])
        if config.get("groq", {}).get("model") == "llama-3.3-70b":
            config["groq"]["model"] = "llama-3.3-70b-versatile"
            conn.execute(text("UPDATE platform_settings SET value = :val WHERE id = :id"),
                        {"val": json.dumps(config), "id": row[0]})
            conn.commit()
            print("Updated Groq model to llama-3.3-70b-versatile")
        else:
            print(f"Current Groq model: {config.get('groq', {}).get('model')}")
