from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Add all missing course_purchases columns
    columns = [
        'currency VARCHAR(10) DEFAULT "DT"',
        'school_id INTEGER REFERENCES schools(id)'
    ]
    
    for col_def in columns:
        col_name = col_def.split()[0]
        try:
            conn.execute(text(f'ALTER TABLE course_purchases ADD COLUMN IF NOT EXISTS {col_def}'))
            print(f'Added {col_name}')
        except Exception as e:
            print(f'{col_name}: {e}')
    
    conn.commit()
    print('All columns added')