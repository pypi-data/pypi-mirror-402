'''
Core logging backend for laplace_log.

This module defines the LoggerLHC class, which:
- configures the root logger
- installs file and console handlers
- captures print() output
- exposes an application-level logger

Typical usage:
    from laplace_log import LoggerLHC, log

    LoggerLHC("laplace.opt")
    log.info("Application started")
'''

# libraries
import logging
from pathlib import Path
from datetime import date
import sys


# project
from .utils import (
    LogHelper, StreamToLogger, 
    get_logger_instance, set_logger_instance
)
log = LogHelper()  # helper class to import in order to make logs easely


class LoggerLHC:
    '''Logger class to handle logs for Laplace apps.'''

    def __init__(self, 
                 app_name: str,
                 log_root: Path | str | None = None,
                 file_level: str = "debug",   # which level to save
                 console_level: str = "info"):
        '''
            Args:
                app_name: (str)
                    The name of the application handling the logs.
                
                log_root: (Path | str | None)
                    the folder path where the logs should be saved. (default None)
                    Creates a 'logs' folder inside which a 'yyyy-mm-dd' folder will 
                    contain the 'app_name.log' file.
                
                file_level: (str)
                    The logging level that should be use to save logs in file.
                
                console_level: (str)
                    The logging level that should be use to print the logs in
                    the console. The 'print' are appearing as 'root' logs.
        '''
        if get_logger_instance() is not None:
            return      # already initialized

        self.app_name = app_name

        # making the folders (logs / yyyy-mm-dd)
        self.log_root = Path(log_root or Path.cwd()) / "logs"
        self.date_folder = self.log_root / date.today().isoformat()
        self.date_folder.mkdir(parents=True, exist_ok=True)

        # log file name (replace '.' by '_')
        self.log_file = self.date_folder / f"{app_name.replace(".", "_")}.log"
        
        # making a root logger and setting the level
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)

        # making an app logger
        self.logger = logging.getLogger(f"{app_name}")

        # Set up handlers (file and console) for root
        self.setup_handlers(file_level, console_level)

        # Redirect Python prints to console handler
        self.capture_prints()

        set_logger_instance(self)  # the instance is initialized


    def setup_handlers(self, file_level: str, console_level: str):
        '''Setup file and console handlers with independent levels.'''
        # format (datatime [level] [process name] message)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S")

        # File handler
        fh = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')  # saving the logs in the file
        fh.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))     # set the log level
        fh.setFormatter(fmt)                                                 # set the format
        self.root_logger.addHandler(fh)                                      # give the handler to root

        # Console handler
        ch = logging.StreamHandler(sys.stdout)                               # print logs in the console
        ch.setLevel(getattr(logging, console_level.upper(), logging.INFO))   # set the log level
        ch.setFormatter(fmt)                                                 # set the format
        self.root_logger.addHandler(ch)                                      # give the handler to root


    def capture_prints(self):
        '''Redirect Python prints to console (avoid double logging).'''
        sys.stdout = StreamToLogger(self.root_logger)
        sys.stderr = StreamToLogger(self.root_logger)


    # Shortcut methods (with the app logger)
    def info(self, msg): self.logger.info(msg)
    def debug(self, msg): self.logger.debug(msg)
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg): self.logger.error(msg)
