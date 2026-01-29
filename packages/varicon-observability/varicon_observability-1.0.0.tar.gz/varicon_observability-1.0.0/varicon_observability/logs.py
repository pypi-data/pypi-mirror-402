import logging
from opentelemetry._logs import set_logger_provider, get_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from .config import ObservabilityConfig
from .filters import NoisyLoggerFilter

logger = logging.getLogger(__name__)

_logger_provider = None

def setup_logging() -> bool:
    global _logger_provider
    
    if not ObservabilityConfig.OTEL_ENABLED or not ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT:
        return False
    
    try:
        resource = Resource.create({
            "service.name": ObservabilityConfig.OTEL_SERVICE_NAME,
            "service.version": ObservabilityConfig.OTEL_SERVICE_VERSION,
            "deployment.environment": ObservabilityConfig.OTEL_DEPLOYMENT_ENVIRONMENT,
        })
        
        existing = get_logger_provider()
        if existing and hasattr(existing, "add_log_record_processor"):
            _logger_provider = existing
            return True
        
        _logger_provider = LoggerProvider(resource=resource)
        
        if ObservabilityConfig.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        else:
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        
        headers = ObservabilityConfig.parse_headers()
        exporter = OTLPLogExporter(
            endpoint=ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers=headers if headers else None,
        )
        
        _logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        set_logger_provider(_logger_provider)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup logging: {e}", exc_info=True)
        return False

def attach_log_handlers():
    if not _logger_provider:
        return
    
    root_logger = logging.getLogger()
    if any(isinstance(h, LoggingHandler) for h in root_logger.handlers):
        return
    
    handler = LoggingHandler(logger_provider=_logger_provider)
    handler.addFilter(NoisyLoggerFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    
    framework_loggers = [
        "django",
        "django.request",
        "django.db.backends",
        "fastapi",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "celery",
        "celery.task",
        "celery.worker",
        "integration-logger",
        "application",
    ]
    
    for name in framework_loggers:
        try:
            lg = logging.getLogger(name)
            if not any(isinstance(h, LoggingHandler) for h in lg.handlers):
                h = LoggingHandler(logger_provider=_logger_provider)
                h.addFilter(NoisyLoggerFilter())
                lg.addHandler(h)
            lg.propagate = True
        except Exception:
            pass
    
    manager = logging.Logger.manager
    for logger_name in list(manager.loggerDict.keys()):
        try:
            lg = manager.loggerDict[logger_name]
            if isinstance(lg, logging.Logger):
                lg.propagate = True
        except Exception:
            pass
