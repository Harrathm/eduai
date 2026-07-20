from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Add all missing lesson columns
    columns = [
        'content_url VARCHAR(500)',
        'content_text TEXT',
        'lesson_order INTEGER DEFAULT 0',
        'duration_minutes INTEGER DEFAULT 0',
        'ai_generated BOOLEAN DEFAULT FALSE',
        'tokens_used INTEGER DEFAULT 0',
        'is_free BOOLEAN DEFAULT FALSE',
        'is_preview BOOLEAN DEFAULT FALSE'
    ]
    
    for col_def in columns:
        col_name = col_def.split()[0]
        try:
            conn.execute(text(f'ALTER TABLE lessons ADD COLUMN IF NOT EXISTS {col_def}'))
            print(f'Added {col_name}')
        except Exception as e:
            print(f'{col_name}: {e}')
    
    conn.commit()
    print('All columns added')