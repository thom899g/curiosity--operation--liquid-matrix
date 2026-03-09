"""
Unified logging system for Operation Liquid Matrix v2.0
Structured logging with Firebase integration for critical events
"""
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import json
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class StructuredLogger:
    """Structured logger with Firebase integration"""
    
    def __init__(self, name: str, firestore_client=None):
        self.name = name
        self.firestore = firestore_client
        self.logger = logging.getLogger(name)
        
        # Configure console handler
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Set level from config
        from config import config
        self.logger.setLevel(getattr(logging, config.log_level))
    
    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self._log(LogLevel.DEBUG, message, metadata)
    
    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self._log(LogLevel.INFO, message, metadata)
    
    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self._log(LogLevel.WARNING, message, metadata)
        self._firebase_log("WARNING", message, metadata)
    
    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self._log(LogLevel.ERROR, message, metadata)
        self._firebase_log("ERROR", message, metadata)
    
    def critical(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self._log(LogLevel.CRITICAL, message, metadata)
        self._firebase_log("CRITICAL", message, metadata)
        self._trigger_telegram_alert(f"🚨 CRITICAL: {message}")
    
    def _log(self, level: LogLevel, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Internal logging method"""
        log_method = getattr(self.logger, level.value.lower())
        
        if metadata:
            structured_message = f"{message} | Metadata: {json.dumps(metadata)}"
            log_method(structured_message)
        else:
            log_method(message)
    
    def _firebase_log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log critical events to Firebase for monitoring dashboard"""
        if not self.firestore:
            return
        
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "component": self.name,
                "level": level,
                "message": message,
                "metadata": metadata or {},
                "resolved": False
            }
            
            # Add to Firestore
            doc_ref = self.firestore.collection("system_logs").document()
            doc_ref.set(log_entry)
            
        except Exception as e:
            # Fallback to console if Firebase fails
            self.logger.error(f"Failed to log to Firebase: {str(e)}")
    
    def _trigger_telegram_alert(self, message: str):
        """Send critical alerts via Telegram"""
        try:
            from utils.telegram import send_telegram_message
            send_telegram_message(message)
        except ImportError:
            self.logger.warning("Telegram module not available for alert")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {str(e)}")

# Global logger instances
def get_logger(name: str, firestore_client=None) -> StructuredLogger:
    """Factory function for getting logger instances"""
    return StructuredLogger(name, firestore_client)