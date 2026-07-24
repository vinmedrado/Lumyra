from __future__ import annotations

import argparse
import logging
import socket
import time
import traceback

from services.job_service import lock_next_job, mark_retry, update_job
from services.logging_service import configure_logging
from workers.tasks import TASKS

logger = logging.getLogger("worker")


def execute_once(worker_id: str | None = None) -> dict:
    worker_id = worker_id or socket.gethostname()
    job = lock_next_job(worker_id)
    if not job:
        return {"status": "idle"}
    task = TASKS.get(job["type"])
    if not task:
        update_job(job["id"], status="failed", error_message=f"Task desconhecida: {job['type']}")
        return {"status": "failed", "job_id": job["id"]}
    try:
        result = task(job)
        update_job(job["id"], status="success", progress=100, result_json=result)
        return {"status": "success", "job_id": job["id"], "result": result}
    except Exception as exc:
        mark_retry(job, f"{exc}\n{traceback.format_exc()}")
        logger.exception("job_failed", extra={"job_id": job["id"], "job_type": job["type"]})
        return {"status": "retry_or_failed", "job_id": job["id"]}


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--sleep", type=int, default=10)
    args = parser.parse_args()
    while True:
        execute_once()
        if args.once:
            break
        time.sleep(args.sleep)


if __name__ == "__main__":
    main()
