import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# ============================================================================
# Setup Logging Directory
# ============================================================================
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


# ============================================================================
# Custom Formatters
# ============================================================================

class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for file logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Build log data with key fields
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add structured fields if present
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "response_time_ms"):
            log_data["response_time_ms"] = round(record.response_time_ms, 2)
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        if hasattr(record, "username"):
            log_data["username"] = record.username
        if hasattr(record, "sql_query"):
            log_data["sql_query"] = record.sql_query
        if hasattr(record, "sql_params"):
            log_data["sql_params"] = record.sql_params
        
        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output"""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        
        # Format HTTP request logs
        if hasattr(record, "method") and hasattr(record, "path"):
            status = getattr(record, "status_code", "?")
            response_time = getattr(record, "response_time_ms", "?")
            client_ip = getattr(record, "client_ip", "unknown")
            return f"[{timestamp}] {client_ip} - {record.method} {record.path} | Status: {status} | Time: {response_time}ms"
        
        # Format SQL logs
        if hasattr(record, "sql_query"):
            return f"[{timestamp}] SQL: {record.sql_query}"
        
        # Default format
        return f"[{timestamp}] {record.levelname}: {record.getMessage()}"


# ============================================================================
# Logger Setup
# ============================================================================

def setup_logging(name: str = "xclipboard") -> logging.Logger:
    """Setup dual logging: console (human-readable) + file (JSON)"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(console_handler)
    
    # File handler (JSON, daily rotation)
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB per file
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger


# Initialize logger
logger = setup_logging()

# Disable uvicorn's verbose access logging
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.INFO)


# ============================================================================
# Logging Helper Functions
# ============================================================================

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    client_ip: str,
    status_code: int,
    response_time_ms: float,
    username: Optional[str] = None
):
    """Log HTTP request/response"""
    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Request processed",
        args=(),
        exc_info=None,
    )
    record.method = method
    record.path = path
    record.client_ip = client_ip
    record.status_code = status_code
    record.response_time_ms = response_time_ms
    if username:
        record.username = username
    
    logger.handle(record)


def log_database_query(
    logger: logging.Logger,
    query: str,
    params: Optional[tuple] = None
):
    """Log database query"""
    record = logging.LogRecord(
        name=logger.name,
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg="Database query",
        args=(),
        exc_info=None,
    )
    record.sql_query = query
    record.sql_params = params
    
    logger.handle(record)
