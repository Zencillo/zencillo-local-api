"""Explicit laboratory entry point. Excluded from the station wheel."""
from contextlib import asynccontextmanager

from app.main import create_registered_app, registered_operations
from tools.payment_lab.operations import payment_operations


def create_lab_app(settings, *, connect, attempts):
    @asynccontextmanager
    async def lifespan(_app):
        with attempts.service_lock():
            attempts.recover()
            yield

    operations = registered_operations(settings)
    operations.update(payment_operations(connect, attempts))
    return create_registered_app(settings, operations, lifespan=lifespan)
