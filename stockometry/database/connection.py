import psycopg2
from psycopg2 import sql
from contextlib import contextmanager
from ..config import settings

def get_db_connection_string(dbname=None):
    """Constructs a connection string."""
    db = dbname or settings.db_name
    return f"dbname='{db}' user='{settings.db_user}' host='{settings.db_host}' password='{settings.db_password}' port='{settings.db_port}'"

@contextmanager
def get_db_connection(dbname=None):
    """Provides a transactional database connection."""
    conn = None
    try:
        conn = psycopg2.connect(get_db_connection_string(dbname=dbname))
        yield conn
    except Exception as e:
        print(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def init_db(dbname=None):
    """Initializes the database and creates tables if they don't exist."""
    target_db = dbname or settings.db_name
    print(f"Initializing database '{target_db}'...")
    try:
        # Connect to the default 'postgres' database to check if our target DB exists
        with get_db_connection(dbname='postgres') as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [target_db])
                if not cursor.fetchone():
                    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
                    print(f"Database '{target_db}' created.")

        # Connect to our target database to create tables
        with get_db_connection(dbname=target_db) as conn:
            with conn.cursor() as cursor:
                # Create articles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id SERIAL PRIMARY KEY,
                        source_id VARCHAR(255),
                        source_name VARCHAR(255),
                        author VARCHAR(255),
                        title TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        description TEXT,
                        content TEXT,
                        published_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create stock_data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stock_data (
                        id SERIAL PRIMARY KEY,
                        ticker VARCHAR(10) NOT NULL,
                        date DATE NOT NULL,
                        open NUMERIC(12, 4),
                        high NUMERIC(12, 4),
                        low NUMERIC(12, 4),
                        close NUMERIC(12, 4),
                        volume BIGINT,
                        UNIQUE(ticker, date)
                    );
                """)
                
                # Create daily_reports table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_reports (
                        id SERIAL PRIMARY KEY, 
                        report_date DATE UNIQUE NOT NULL, 
                        executive_summary TEXT NOT NULL,
                        run_source VARCHAR(20) DEFAULT 'SCHEDULED',
                        generated_at_utc TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Check if executive_summary column exists, if not add it
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'daily_reports' AND column_name = 'executive_summary';
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE daily_reports ADD COLUMN executive_summary TEXT;")
                    print("Added executive_summary column to daily_reports table")
                
                # Check if run_source column exists, if not add it
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'daily_reports' AND column_name = 'run_source';
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE daily_reports ADD COLUMN run_source VARCHAR(20) DEFAULT 'SCHEDULED';")
                    print("Added run_source column to daily_reports table")
                
                # Check if generated_at_utc column exists, if not add it
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'daily_reports' AND column_name = 'generated_at_utc';
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE daily_reports ADD COLUMN generated_at_utc TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
                    print("Added generated_at_utc column to daily_reports table")
                
                # Create report_signals table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS report_signals (
                        id SERIAL PRIMARY KEY, 
                        report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE, 
                        signal_type VARCHAR(50) NOT NULL, 
                        sector VARCHAR(255), 
                        direction VARCHAR(50), 
                        details TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Check if created_at column exists in report_signals, if not add it
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'report_signals' AND column_name = 'created_at';
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE report_signals ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
                    print("Added created_at column to report_signals table")
                
                # Create signal_sources table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS signal_sources (
                        id SERIAL PRIMARY KEY, 
                        signal_id INTEGER REFERENCES report_signals(id) ON DELETE CASCADE, 
                        title TEXT NOT NULL, 
                        url TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(signal_id, url)
                    );
                """)
                
                # Check if created_at column exists in signal_sources, if not add it
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'signal_sources' AND column_name = 'created_at';
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE signal_sources ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
                    print("Added created_at column to signal_sources table")
                
                # Create predicted_stocks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS predicted_stocks (
                        id SERIAL PRIMARY KEY,
                        signal_id INTEGER REFERENCES report_signals(id) ON DELETE CASCADE,
                        symbol VARCHAR(20) NOT NULL,
                        reason TEXT NOT NULL,
                        url TEXT,
                        score DECIMAL(5,4),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Check if created_at column exists in predicted_stocks, if not add it
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'predicted_stocks' AND column_name = 'created_at';
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE predicted_stocks ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
                    print("Added created_at column to predicted_stocks table")
                
            conn.commit()
        print("Database tables checked/created successfully.")
    except psycopg2.OperationalError as e:
        print(f"Could not connect to PostgreSQL. Is the server running and are your credentials in the configuration correct? Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")
        exit(1)

if __name__ == '__main__':
    init_db()
