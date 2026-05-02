import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from logging import Logger
from logger import log_request


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests with timing and status"""
    
    def __init__(self, app, logger: Logger):
        super().__init__(app)
        self.logger = logger
    
    async def dispatch(self, request: Request, call_next):
        """Log incoming request and outgoing response"""
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Call the next middleware/endpoint
        response = await call_next(request)
        
        # Calculate response time in milliseconds
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log the request
        log_request(
            self.logger,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            status_code=response.status_code,
            response_time_ms=response_time_ms
        )
        
        return response
