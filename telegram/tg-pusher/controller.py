import asyncio
import time
from aiogram import Bot
from croniter import croniter

from config import BOTS, GROUPS, BACKOFF, MAX_RETRY
from content import build_content
from storage import TaskStore
from worker import WorkerBot
from logger import setup_logger

ctrl_log = setup_logger("controller", "logs/controller.log")
err_log = setup_logger("error", "logs/error.log")

def next_run_from_cron(expr: str, base: int) -> int:
    """Calculate next execution timestamp from cron."""
    return int(croniter(expr, base).get_next())

async def main():
    """Main scheduler loop."""
    store = TaskStore()
    await store.init()

    workers = {
        name: WorkerBot(
            Bot(token=cfg["token"]),
            cfg["min_interval"],
            cfg["jitter"],
        )
        for name, cfg in BOTS.items()
    }

    now = int(time.time())

    # === Initial task creation (run once after DB reset) ===
    for g in GROUPS:
        first_run = next_run_from_cron(g["cron"], now)
        content = build_content(g["address"])

        await store.add_task(
            bot=g["bot"],
            group_id=g["group_id"],
            address=g["address"],
            content=content,
            cron=g["cron"],
            first_run=first_run,
        )

        ctrl_log.info(
            f"[TASK_INIT] group={g['group_id']} "
            f"cron={g['cron']} next={time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_run))}"
        )

    # === Scheduler loop ===
    while True:
        tasks = await store.fetch_due()

        for t in tasks:
            (
                task_id,
                bot_name,
                group_id,
                address,
                content,
                cron,
                retry_count,
                next_run_at,
                last_error,
                updated_at,
            ) = t

            try:
                await workers[bot_name].send(group_id, content)
                ctrl_log.info(f"[SEND_OK] id={task_id}")

                next_run = next_run_from_cron(cron, next_run_at)
                await store.update_next_run(task_id, next_run)

            except Exception as e:
                err_log.error(f"[SEND_FAIL] id={task_id} err={e}")
                retry_count += 1

                if retry_count > MAX_RETRY:
                    err_log.error(f"[TASK_STOPPED] id={task_id}")
                    continue

                delay = BACKOFF[retry_count - 1]
                await store.mark_retry(
                    task_id, retry_count, delay, str(e)
                )

        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
