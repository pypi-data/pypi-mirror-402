"""
Logging utility for Klink SDK
"""
import logging
from typing import Any, Dict


class Logger:
    """Simple logger for SDK operations"""
    
    def __init__(self, debug: bool = False):
        self.debug_enabled = debug
        self.logger = logging.getLogger("klinkfinance_sdk")
        
        if debug and not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
    
    def info(self, message: str, context: Dict[str, Any] = None):
        """Log info message"""
        if self.debug_enabled:
            if context:
                self.logger.info(f"{message} - {context}")
            else:
                self.logger.info(message)
    
    def error(self, message: str, context: Dict[str, Any] = None):
        """Log error message"""
        if self.debug_enabled:
            if context:
                self.logger.error(f"{message} - {context}")
            else:
                self.logger.error(message)
    
    def debug(self, message: str, context: Dict[str, Any] = None):
        """Log debug message"""
        if self.debug_enabled:
            if context:
                self.logger.debug(f"{message} - {context}")
            else:
                self.logger.debug(message)
