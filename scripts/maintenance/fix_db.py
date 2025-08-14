from app.models.database import engine

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE scraping_tasks 
        ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3;
        
        ALTER TABLE scraping_tasks 
        ADD COLUMN IF NOT EXISTS current_retries INTEGER DEFAULT 0;
    """))
    conn.commit()