import psycopg

from docguard.config import settings


def main():
    try:
        conn = psycopg.connect(settings.database_url)
        print("Database connection: OK")
        row = conn.execute("SELECT count(*) FROM documents").fetchone()
        count = row[0] if row else 0
        print(f"Documents: {count}")
    except Exception as e:
        print(f"Database connection: FAILED ({e})")


if __name__ == "__main__":
    main()
