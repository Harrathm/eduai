from app.db import get_db
from app.ai.provider_client import get_enabled_provider, generate_chat

db = next(get_db())
pid, conf = get_enabled_provider(db)
print(f"Provider: {pid}")
if conf:
    print(f"Model: {conf.get('model')}")
    print(f"Has key: {bool(conf.get('key'))}")

try:
    result = generate_chat(db, [{"role": "user", "content": "Say 'ok' only."}], max_tokens=10)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
