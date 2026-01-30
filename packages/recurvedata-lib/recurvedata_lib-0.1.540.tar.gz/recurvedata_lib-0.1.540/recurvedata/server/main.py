from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse

from recurvedata.config import REDIS_CACHE_URL
from recurvedata.core.tracing import Tracing
from recurvedata.server.connector.api import router as connector_router
from recurvedata.server.data_service.api import router as data_service_router
from recurvedata.server.dbt.api import router as dbt_router
from recurvedata.server.executor.api import router as executor_router
from recurvedata.server.schedulers.api import router as schedulers_router
from recurvedata.server.stream.flink.api import router as flink_router
from recurvedata.utils.cache import redis_cache
from recurvedata.utils.log import init_logging, setup_loguru

__all__ = ["create_app"]


def create_app() -> FastAPI:
    init_logging()
    setup_loguru()

    if not Tracing.is_instantiated():
        from recurvedata.utils.tracing import create_dp_tracer

        create_dp_tracer("recurve-lib-server")

    app = FastAPI(title="Recurve Lib Server", default_response_class=ORJSONResponse)
    redis_cache.configure(namespace="recurve-lib-server", redis_url=REDIS_CACHE_URL)
    public_router = APIRouter(prefix="/api")
    public_router.include_router(dbt_router, prefix="/dbt")
    public_router.include_router(connector_router, prefix="/connector")
    public_router.include_router(data_service_router, prefix="/data-service")
    public_router.include_router(executor_router, prefix="/executor")
    public_router.include_router(schedulers_router, prefix="/schedulers")
    public_router.include_router(flink_router, prefix="/stream/flink")
    app.include_router(public_router)
    return app
