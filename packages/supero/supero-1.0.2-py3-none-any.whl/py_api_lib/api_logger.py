"""
Simple App Logger - Minimal Singleton Implementation
Initialize once with app_name, use everywhere with get_logger()
"""
import logging
import logging.handlers
import os
import json
import threading
import inspect
from datetime import datetime


class AppLogger:
    """
    Simple singleton logger for the entire application.
    
    Initialize once at app startup, use everywhere else.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    # Built-in LogRecord attributes that should not be overwritten
    _RESERVED_ATTRS = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
        'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
        'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
        'processName', 'process', 'message', 'asctime'
    }
    
    def __init__(self, app_name: str):
        """
        Initialize the logger (called only once)
        
        Args:
            app_name: Name of your application
        """
        if AppLogger._initialized:
            return
            
        with AppLogger._lock:
            if AppLogger._initialized:
                return
            
            self.app_name = app_name
            self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
            self.log_format = os.getenv('LOG_FORMAT', 'human').lower()
            
            # Setup the logger
            self._setup_logger()
            AppLogger._initialized = True
    
    def _setup_logger(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler (stdout/stderr for containers)
        console_handler = logging.StreamHandler()
        
        if self.log_format == 'json':
            # JSON format for container environments
            formatter = JSONFormatter(self.app_name)
        else:
            # Clean bracket format for readability
            formatter = logging.Formatter(
                '[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]: %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Optional file logging if LOG_DIR is set
        log_dir = os.getenv('LOG_DIR')
        if log_dir:
            self._setup_file_logging(formatter, log_dir)
        
        # Log initialization
        self.logger.info(f"AppLogger initialized for {self.app_name}")
    
    def _setup_file_logging(self, formatter, log_dir):
        """Setup optional file logging"""
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{self.app_name}.log")
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=50 * 1024 * 1024,  # 50MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            self.logger.info(f"File logging enabled: {log_file}")
        except Exception as e:
            self.logger.warning(f"Could not setup file logging: {e}")
    
    def _find_caller(self):
        """
        Find the actual caller (not the wrapper method) for more useful logging.
        Returns (filename, lineno, funcName) of the real caller.
        """
        try:
            # Get the current call stack
            frame = inspect.currentframe()
            
            # Walk up the stack to find the first frame outside of api_logger.py
            while frame:
                frame = frame.f_back
                if frame is None:
                    break
                    
                filename = frame.f_code.co_filename
                # Skip frames from this logging module
                if not filename.endswith('api_logger.py'):
                    return (
                        os.path.basename(filename),  # Just the filename, not full path
                        frame.f_lineno,
                        frame.f_code.co_name
                    )
            
            # Fallback if we can't find a good caller
            return ('unknown.py', 0, 'unknown')
            
        except Exception:
            return ('unknown.py', 0, 'unknown')
    
    def _log_with_caller_info(self, level, message, **extra):
        """
        Log a message with the real caller's file/line info instead of wrapper info.
        """
        try:
            sanitized_extra = self._sanitize_extra(extra)
            
            # Find the real caller
            filename, lineno, funcname = self._find_caller()
            
            # Create a custom log record with the real caller's info
            record = self.logger.makeRecord(
                name=self.logger.name,
                level=level,
                fn=filename,  # This will show as the filename
                lno=lineno,   # This will show as the line number
                msg=message,
                args=(),
                exc_info=None,
                extra=sanitized_extra,
                func=funcname
            )
            
            # Handle the record through the logger's handlers
            self.logger.handle(record)
            
        except Exception:
            # Fallback to basic logging without caller info
            try:
                sanitized_extra = self._sanitize_extra(extra)
                getattr(self.logger, logging.getLevelName(level).lower())(message, extra=sanitized_extra)
            except Exception:
                # Final fallback: print to stdout
                level_name = logging.getLevelName(level)
                print(f"[FALLBACK][{level_name}]: {message}")

    def _sanitize_extra(self, extra):
        """
        Remove keys that conflict with built-in LogRecord attributes
        to prevent 'Attempt to overwrite' errors
        """
        if not extra:
            return {}
        
        # Filter out reserved attributes
        sanitized = {}
        for key, value in extra.items():
            if key not in self._RESERVED_ATTRS:
                sanitized[key] = value
            # Silently skip reserved attributes instead of logging warnings
            # to avoid recursive logging issues
        
        return sanitized
    
    @classmethod
    def initialize(cls, app_name: str):
        """
        Initialize the singleton logger (call this once at app startup)
        
        Args:
            app_name: Name of your application
        
        Returns:
            AppLogger: The singleton instance
        """
        if cls._instance is None:
            cls._instance = AppLogger(app_name)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton logger instance
        
        Returns:
            AppLogger: The singleton instance
        
        Raises:
            RuntimeError: If logger hasn't been initialized yet
        """
        if cls._instance is None:
            raise RuntimeError("Logger not initialized. Call AppLogger.initialize(app_name) first.")
        return cls._instance
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if logger has been initialized"""
        return cls._instance is not None
    
    # Simple logging methods with sanitized extra parameters and real caller info
    def debug(self, message: str, **extra):
        """Log debug message with real caller info"""
        self._log_with_caller_info(logging.DEBUG, message, **extra)
    
    def info(self, message: str, **extra):
        """Log info message with real caller info"""
        self._log_with_caller_info(logging.INFO, message, **extra)
    
    def warning(self, message: str, **extra):
        """Log warning message with real caller info"""
        self._log_with_caller_info(logging.WARNING, message, **extra)
    
    def error(self, message: str, **extra):
        """Log error message with real caller info"""
        self._log_with_caller_info(logging.ERROR, message, **extra)
    
    def critical(self, message: str, **extra):
        """Log critical message with real caller info"""
        self._log_with_caller_info(logging.CRITICAL, message, **extra)
    
    def exception(self, message: str, **extra):
        """Log exception with traceback and real caller info"""
        try:
            sanitized_extra = self._sanitize_extra(extra)
            
            # Find the real caller
            filename, lineno, funcname = self._find_caller()
            
            # For exceptions, we want to preserve the exc_info
            record = self.logger.makeRecord(
                name=self.logger.name,
                level=logging.ERROR,
                fn=filename,
                lno=lineno,
                msg=message,
                args=(),
                exc_info=True,  # This captures the current exception
                extra=sanitized_extra,
                func=funcname
            )
            
            self.logger.handle(record)
            
        except Exception:
            # Fallback to basic exception logging
            try:
                self.logger.exception(message)
            except Exception:
                print(f"[FALLBACK][EXCEPTION]: {message}")


class JSONFormatter(logging.Formatter):
    """Simple JSON formatter for structured logging"""
    
    def __init__(self, app_name: str):
        super().__init__()
        self.app_name = app_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        try:
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'app': self.app_name,
                'level': record.levelname,
                'file': record.filename,
                'line': record.lineno,
                'message': record.getMessage()
            }
            
            # Add extra fields if present - but safely
            if hasattr(record, 'extra') and record.extra:
                # Only add non-conflicting extra fields
                for key, value in record.extra.items():
                    if key not in log_data:  # Avoid overwriting existing keys
                        log_data[f"extra_{key}"] = value  # Prefix with "extra_" for safety
            
            # Add exception info if present
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_data, default=str)
        except Exception:
            # Fallback to simple format if JSON formatting fails
            return f"LOG_FORMAT_ERROR: {record.getMessage()}"


# ============================================================================
# SIMPLE API FUNCTIONS
# ============================================================================

def initialize_logger(app_name: str):
    """
    Initialize the application logger (call once at startup)
    
    Args:
        app_name: Name of your application
    
    Returns:
        AppLogger: The singleton logger instance
    
    Example:
        # In main.py
        from .api_logger import initialize_logger
        logger = initialize_logger('ui-server')
    """
    return AppLogger.initialize(app_name)


def get_logger():
    """
    Get the logger instance (use anywhere in your app)
    
    Returns:
        AppLogger: The singleton logger instance
    
    Example:
        # In any module
        from .api_logger import get_logger
        logger = get_logger()
        logger.info("Hello world")
    """
    return AppLogger.get_instance()

def is_logger_ready() -> bool:
    """
    Check if logger is initialized and ready to use
    
    Returns:
        bool: True if logger is ready
    """
    return AppLogger.is_initialized()
