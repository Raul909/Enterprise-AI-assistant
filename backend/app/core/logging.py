"""
Structured logging configuration using structlog.
Provides JSON logging for production and human-readable output for development.
"""

import logging
import sys
from datetime import datetime, timezone

import structlog
from structlog.types import Processor

from core.config import settings


def add_timestamp(
    logger: logging.Logger, method_name: str, event_dict: dict
) -> dict:
    """Add ISO timestamp to log entries."""
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: dict
) -> dict:
    """Add application context to log entries."""
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["environment"] = settings.environment
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Common processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_timestamp,
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json":
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class AuditLogger:
    """
    Specialized logger for audit trail entries.
    Records tool executions, user actions, and security events.
    """
    
    def __init__(self):
        self._logger = get_logger("audit")
    
    def log_tool_execution(
        self,
        user_id: int,
        tool_name: str,
        query: str,
        result: dict | None = None,
        execution_time_ms: float = 0,
        success: bool = True,
        error: str | None = None
    ) -> None:
        """Log a tool execution for audit purposes."""
        self._logger.info(
            "tool_execution",
            user_id=user_id,
            tool_name=tool_name,
            query=query[:500],  # Truncate long queries
            execution_time_ms=execution_time_ms,
            success=success,
            error=error,
            result_size=len(str(result)) if result else 0
        )
    
    def log_auth_event(
        self,
        event_type: str,
        user_email: str | None = None,
        user_id: int | None = None,
        success: bool = True,
        ip_address: str | None = None,
        reason: str | None = None
    ) -> None:
        """Log authentication events."""
        self._logger.info(
            "auth_event",
            event_type=event_type,
            user_email=user_email,
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            reason=reason
        )
    
    def log_permission_denied(
        self,
        user_id: int,
        resource: str,
        action: str,
        reason: str
    ) -> None:
        """Log permission denied events."""
        self._logger.warning(
            "permission_denied",
            user_id=user_id,
            resource=resource,
            action=action,
            reason=reason
        )


# Global audit logger instance
audit_logger = AuditLogger()
