from .setup import setup_observability
from .config import ObservabilityConfig
from .integrations import setup_django, setup_fastapi, setup_celery

__version__ = "1.0.0"
__all__ = [
    "setup_observability",
    "ObservabilityConfig",
    "setup_django",
    "setup_fastapi",
    "setup_celery",
]
