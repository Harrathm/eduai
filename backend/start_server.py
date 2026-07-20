import uvicorn
import sys

try:
    from app.main import app
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='error')
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)