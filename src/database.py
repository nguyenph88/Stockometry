import psycopg2
from psycopg2 import sql
from contextlib import contextmanager
from src.config import settings

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

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    print("Initializing database...")
    try:
        # Connect to the default 'postgres' database to check if our DB exists
        with get_db_connection(dbname='postgres') as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [settings.db_name])
                if not cursor.fetchone():
                    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.db_name)))
                    print(f"Database '{settings.db_name}' created.")

        # Connect to our application database to create tables
        with get_db_connection() as conn:
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
            conn.commit()
        print("Database tables checked/created successfully.")
    except psycopg2.OperationalError as e:
        print(f"Could not connect to PostgreSQL. Is the server running and are your credentials in .env correct? Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")
        exit(1)

if __name__ == '__main__':
    init_db()
