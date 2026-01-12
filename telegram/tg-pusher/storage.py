import time
import aiosqlite

class TaskStore:
    """SQLite task storage with cron support."""

    def __init__(self, db_path: str = "state.db"):
        self.db_path = db_path

    async def init(self):
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
            CREATE TABLE IF NOT EXISTS send_tasks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              bot_name TEXT NOT NULL,
              group_id INTEGER NOT NULL,
              address TEXT NOT NULL,
              content TEXT NOT NULL,
              cron TEXT NOT NULL,
              retry_count INTEGER DEFAULT 0,
              next_run_at INTEGER NOT NULL,
              last_error TEXT,
              updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_next_run
            ON send_tasks(next_run_at);
            """)
            await db.commit()

    async def add_task(
        self,
        bot: str,
        group_id: int,
        address: str,
        content: str,
        cron: str,
        first_run: int,
    ):
        """Insert initial task (run once at startup)."""
        now = int(time.time())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
            INSERT INTO send_tasks
            (bot_name, group_id, address, content, cron,
             retry_count, next_run_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """, (bot, group_id, address, content, cron, first_run, now))
            await db.commit()

    async def fetch_due(self, limit: int = 5):
        """Fetch tasks whose next_run_at is due."""
        now = int(time.time())
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("""
            SELECT * FROM send_tasks
            WHERE next_run_at <= ?
            ORDER BY next_run_at
            LIMIT ?
            """, (now, limit))
            return await cur.fetchall()

    async def update_next_run(self, task_id: int, next_run: int):
        """Update next cron execution time."""
        now = int(time.time())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
            UPDATE send_tasks
            SET next_run_at = ?,
                retry_count = 0,
                last_error = NULL,
                updated_at = ?
            WHERE id = ?
            """, (next_run, now, task_id))
            await db.commit()

    async def mark_retry(
        self, task_id: int, retry: int, delay: int, error: str
    ):
        """Schedule retry with backoff."""
        now = int(time.time())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
            UPDATE send_tasks
            SET retry_count = ?,
                next_run_at = ?,
                last_error = ?,
                updated_at = ?
            WHERE id = ?
            """, (retry, now + delay, error, now, task_id))
            await db.commit()
