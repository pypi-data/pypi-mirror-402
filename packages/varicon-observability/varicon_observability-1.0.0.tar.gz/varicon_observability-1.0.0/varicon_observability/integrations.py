import logging
from typing import Optional
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def setup_django():
    try:
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
        
        DjangoInstrumentor().instrument()
        Psycopg2Instrumentor().instrument()
        logger.info("Django instrumentation enabled")
        return True
    except Exception as e:
        logger.warning(f"Django instrumentation failed: {e}")
        return False

def setup_fastapi(app: Optional[FastAPI] = None):
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        
        if app:
            FastAPIInstrumentor().instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        logger.info("FastAPI instrumentation enabled")
        return True
    except Exception as e:
        logger.warning(f"FastAPI instrumentation failed: {e}")
        return False

def setup_celery():
    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        CeleryInstrumentor().instrument()
        logger.info("Celery instrumentation enabled")
        return True
    except Exception as e:
        logger.warning(f"Celery instrumentation failed: {e}")
        return False
