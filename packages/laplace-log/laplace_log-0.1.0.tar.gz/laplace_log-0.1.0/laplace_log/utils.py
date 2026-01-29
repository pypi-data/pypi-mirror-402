'''
Internal utilities for laplace_log.

This module contains:
- the singleton logger instance
- helper classes for simplified logging calls
- stream redirection utilities for print() capture

This module is not intended to be used directly by applications.
'''
# libraries
import sys


# singleton instance (app logger)
_logger_instance = None

def set_logger_instance(logger):
    '''set the app logger'''
    global _logger_instance
    _logger_instance = logger

def get_logger_instance():
    '''get the app logger'''
    return _logger_instance


def log_func(msg, level="info"):
    '''Log function used to make logs in app logger.'''
    global _logger_instance
    if _logger_instance is None:
        raise RuntimeError("Logger not initialized! Call LoggerLHC(app_name, ...) first.")
    
    level = level.lower()
    if level == "debug":
        _logger_instance.debug(msg)
    elif level == "warning":
        _logger_instance.warning(msg)
    elif level == "error":
        _logger_instance.error(msg)
    else:
        _logger_instance.info(msg)


class LogHelper:
    '''Helper class giving a shortcut to app logger.'''
    def info(self, msg): log_func(msg, level="info")
    def debug(self, msg): log_func(msg, level="debug")
    def warning(self, msg): log_func(msg, level="warning")
    def error(self, msg): log_func(msg, level="error")


class StreamToLogger:
    '''Helper class redirecting the Python stream (prints) to the 'logger' gave in argument.'''
    
    def __init__(self, logger, stream=None):
        self.logger = logger
        self.stream = stream or sys.__stdout__  # original stdout/stderr
    
    def write(self, message):
        message = message.rstrip()
        if not message:
            return
        
        # Write to the original console
        if self.stream:
            self.stream.write(message + "\n")
            self.stream.flush()
        
        # add the print the logger logs
        self.logger.info(message)
    
    def flush(self):
        if self.stream:
            self.stream.flush()
