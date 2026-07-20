from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Add all new columns needed for professional course management
    columns = [
        # Visual management
        "cover_url VARCHAR(500)",
        
        # Access control
        "visibility VARCHAR(50) DEFAULT 'public'",  # public, private, school, role
        "enrollment_type VARCHAR(50) DEFAULT 'open'",  # open, manual, assignment
        
        # Pedagogical
        "prerequisites TEXT",
        "learning_objectives TEXT",
        
        # School/teacher assignment (stored as JSON arrays)
        "allowed_schools JSON",
        "allowed_teachers JSON",
        
        # Audit fields
        "created_by_id INTEGER REFERENCES users(id)",
        "updated_by_id INTEGER REFERENCES users(id)",
        "archived_at TIMESTAMP",
        "archived_by_id INTEGER REFERENCES users(id)",
        
        # Additional metadata
        "short_description VARCHAR(500)",
        "slug VARCHAR(255) UNIQUE",
        "meta_title VARCHAR(255)",
        "meta_description TEXT",
        "language VARCHAR(20) DEFAULT 'fr'"
    ]
    
    for col_def in columns:
        col_name = col_def.split()[0]
        try:
            conn.execute(text(f"ALTER TABLE courses ADD COLUMN IF NOT EXISTS {col_def}"))
            print(f"Added: {col_name}")
        except Exception as e:
            print(f"{col_name}: {e}")
    
    conn.commit()
    print("\n✅ All columns added successfully!")