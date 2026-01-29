import logging
from typing import Optional
from .config import ObservabilityConfig
from .traces import setup_tracing
from .metrics import setup_metrics
from .logs import setup_logging, attach_log_handlers
from .capture import ensure_all_logs_captured

logger = logging.getLogger(__name__)

_initialized = False

def setup_observability(
    service_name: Optional[str] = None,
    enable_traces: bool = True,
    enable_metrics: bool = True,
    enable_logs: bool = True,
    instrument_framework: bool = True,
) -> bool:
    global _initialized
    
    if _initialized:
        return True
    
    if service_name:
        ObservabilityConfig.OTEL_SERVICE_NAME = service_name
    
    if not ObservabilityConfig.OTEL_ENABLED:
        logger.info("OpenTelemetry disabled")
        return False
    
    if not ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT not set")
        return False
    
    success = True
    
    if enable_traces:
        success &= setup_tracing()
    
    if enable_metrics:
        success &= setup_metrics()
    
    if enable_logs:
        if setup_logging():
            attach_log_handlers()
            ensure_all_logs_captured()
    
    if instrument_framework:
        _instrument_framework()
    
    _initialized = True
    return success

def _instrument_framework():
    from .integrations import setup_django, setup_fastapi, setup_celery
    
    if setup_django():
        return
    
    if setup_fastapi():
        return
    
    setup_celery()
