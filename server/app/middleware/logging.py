"""
Logging Middleware

Provides structured logging for requests, responses, and errors.
"""

import logging
import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured JSON logging.
    
    Logs requests, responses, and errors with structured data including:
    - user_id
    - request_id
    - timestamp
    - method, path, status_code
    - response_time
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request and log structured data."""
        start_time = time.time()
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # Get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        # Log request
        logger.info(
            "Request received",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "response_time_ms": round(process_time * 1000, 2),
                }
            )
            
            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "response_time_ms": round(process_time * 1000, 2),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
            
            raise


def setup_logging():
    """Configure structured logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Use JSON formatter in production
    # In development, use standard formatter for readability
    import os
    if os.getenv("PRODUCTION", "false").lower() == "true":
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                
                # Add extra fields
                if hasattr(record, "request_id"):
                    log_data["request_id"] = record.request_id
                if hasattr(record, "user_id"):
                    log_data["user_id"] = record.user_id
                if hasattr(record, "method"):
                    log_data["method"] = record.method
                if hasattr(record, "path"):
                    log_data["path"] = record.path
                if hasattr(record, "status_code"):
                    log_data["status_code"] = record.status_code
                if hasattr(record, "response_time_ms"):
                    log_data["response_time_ms"] = record.response_time_ms
                
                return json.dumps(log_data)
        
        # Apply JSON formatter
        for handler in logging.root.handlers:
            handler.setFormatter(JSONFormatter())

