import os
import asyncio
import sentry_sdk

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aptrade.core.worker import DataStore
from typing import Optional

# from aptrade.schedule import crons, get_cron_router
from aptrade.api.main import api_router
from aptrade.core.config import settings
from fastapi.routing import APIRoute


import logging

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    print(route.tags, route.name)
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


API_ENABLED = os.getenv("API_ENABLED", "true").lower() in ("1", "true", "yes")

app = FastAPI(
    title="APTrade API",
    docs_url="/docs" if API_ENABLED else None,
    redoc_url="/redoc" if API_ENABLED else None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

DATASTORE = DataStore()
_bg_task: Optional[asyncio.Task] = None


# @app.on_event("startup")
# async def _startup_crons():
#     logger.info("startup: initializing crons")
#     # call init_app if available
#     if hasattr(crons, "init_app"):
#         maybe = crons.init_app(app)
#         if asyncio.iscoroutine(maybe):
#             await maybe

#     # try to start the scheduler if a start method exists
#     for name in ("start", "start_all", "run"):
#         start_fn = getattr(crons, name, None)
#         if callable(start_fn):
#             res = start_fn()
#             if asyncio.iscoroutine(res):
#                 await res
#             logger.info(f"started crons using {name}()")
#             break
#     else:
#         logger.info("no start() method on crons; assuming init_app activated tasks")


# @app.on_event("shutdown")
# async def _shutdown_crons():
#     logger.info("shutdown: stopping crons")
#     for stop_name in ("shutdown", "stop", "stop_all", "close"):
#         stop_fn = getattr(crons, stop_name, None)
#         if callable(stop_fn):
#             res = stop_fn()
#             if asyncio.iscoroutine(res):
#                 await res
#             logger.info(f"stopped crons using {stop_name}()")
#             break


# @app.get("/latest")
# async def latest():
#     data = await DATASTORE.get_latest()
#     if data is None:
#         return {"status": "no-data"}
#     return data


if API_ENABLED:
    # optional: enable CORS only when API is active
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.API_V1_STR)
else:
    # register a simple health route even when API disabled (optional)
    @app.get("/_internal/health")
    def health():
        return {"api_enabled": False}
