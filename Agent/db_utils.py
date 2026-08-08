
import psycopg

from Agent.service import get_db_uri


def clear_postgres_data() -> None:

    """Delete all checkpoint table contents, keeping the table structure with empty rows."""
    
    with psycopg.connect(get_db_uri(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                TRUNCATE TABLE
                    checkpoints,
                    checkpoint_blobs,
                    checkpoint_writes
                RESTART IDENTITY CASCADE;
                """
            )

    print("PostgreSQL data cleared successfully.")


if __name__ == "__main__":
    clear_postgres_data()
