"""FastAPI main application file"""
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist, IntegrityError

from scheduler_service import close_dramatiq, close_tortoise, setup_dramatiq, get_scheduler
from scheduler_service.api import setup_routes
from scheduler_service.config import Config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management"""
    # Execute on startup
    await setup_dbs(app)

    # Start scheduler
    scheduler = get_scheduler()
    scheduler.start()

    # Dramatiq will be set up by the app fixture in tests or via external config in production
    yield

    # Shutdown scheduler
    if scheduler.running:
        scheduler.shutdown()

    # Execute on shutdown
    await close_dbs()


def create_app(config: Any = None) -> FastAPI:
    """Create FastAPI application"""
    # Get default config (Config.to_dict() automatically loads TOML config)
    default_config = Config.to_dict()

    # If config is provided, update default config with it
    if config:
        # If config is a class, get its dict form
        if hasattr(config, 'to_dict'):
            config_dict = config.to_dict()
        elif isinstance(config, dict):
            config_dict = config
        else:
            # Try to convert it to dict
            config_dict = dict(config.__dict__)

        # Update default config
        default_config.update(config_dict)

    # Use new lifespan event handler
    app = FastAPI(
        title="Scheduler Service API",
        description="RESTful API for Task Scheduler Service",
        version="0.3.0",
        lifespan=lifespan  # Set lifespan management
    )

    # Store config to app instance
    app.config = default_config

    # Register routes
    setup_routes(app)

    # Register exception handlers
    @app.exception_handler(DoesNotExist)
    async def does_not_exist_exception_handler(request: Request, exc: DoesNotExist):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_exception_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": [
                {"loc": [], "msg": str(exc), "type": "IntegrityError"}]},
        )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        # Production environment should set specific domains
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


async def setup_dbs(app: FastAPI):
    """Initialize all database connections"""

    # Get database URL, supports multiple config keys
    db_url = app.config.get('POSTGRES_URL') or app.config.get(
        'PG_URL') or app.config.get('DB_URL')
    if not db_url:
        raise ValueError(
            "PostgreSQL database URL not configured, please set POSTGRES_URL, PG_URL or DB_URL")

    # PostgreSQL - Tortoise ORM (Use official implementation)
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["scheduler_service.models"]},
    )

    # Initialize Dramatiq
    setup_dramatiq(app.config)


async def close_dbs():
    """Close all database connections"""
    # Close Tortoise connection
    await close_tortoise()
    # Close Dramatiq connection
    close_dramatiq()
