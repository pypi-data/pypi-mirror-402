# from fastapi_crons import Crons, get_cron_router as _get_cron_router
# from fastapi_crons.state import SQLiteStateBackend
# import logging
# from aptrade.scanner import GapScanner

# logger = logging.getLogger(__name__)
# state = SQLiteStateBackend(db_path="jobs.db")
# crons = Crons(state_backend=state)

# gap_scanner = GapScanner()


# def log_job_start(job_name: str, context: dict):
#     print(f"🚀 Starting job: {job_name}")
#     print(f"📅 Scheduled: {context['scheduled_time']}")


# crons.add_before_run_hook(log_job_start)


# async def notify_success(job_name: str, context: dict):
#     duration = context["duration"]
#     print(f"✅ {job_name} completed in {duration:.2f}s")

#     # Send notification
#     print(f"Job {job_name} succeeded")


# crons.add_after_run_hook(notify_success)


# async def handle_error(job_name: str, context: dict):
#     error = context["error"]
#     print(f"❌ {job_name} failed: {error}")

#     # Send alert
#     print(f"Job {job_name} failed: {error}")


# crons.add_on_error_hook(handle_error)


# @crons.cron("*/1 * * * *", name="every_minute_test")
# async def every_minute_test():
#     logger.info("cron every_minute_test running")
#     print("🔁 every_minute_test fired")
#     try:
#         gap_scanner.refresh()
#     except Exception as e:
#         print("gap_scanner.refresh() raised:", e)
#     return "ok"


# @crons.cron("*/1 * * * *", name="cleanup")
# async def cleanup_task():
#     # Runs every 5 minutes
#     print("🧹 Cleaning up temporary files...")
#     return "Cleanup completed"


# @crons.cron("0 0 * * *", name="daily_report")
# def generate_daily_report():
#     # Runs at midnight every day
#     print("📊 Generating daily report...")
#     return "Report generated"


# def get_cron_router():
#     # return a router bound to our `crons` instance
#     return _get_cron_router()
