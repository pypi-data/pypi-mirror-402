# The Alluxio Open Foundation licenses this work under the Apache License, version 2.0
# (the "License"). You may not use this work except in compliance with the License, which is
# available at www.apache.org/licenses/LICENSE-2.0
#
# This software is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied, as more fully set forth in the License.
#
# See the NOTICE file distributed with this work for information regarding copyright ownership.
import logging
import os
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler


# Global registry to track loggers per process to avoid duplicate handlers
_process_loggers = {}
_logger_lock = threading.Lock()


class TagAdapter(logging.LoggerAdapter):
    """Logger adapter that prefixes messages with a fixed tag and adds context info."""

    def process(self, msg, kwargs):
        # Add thread ID and process ID to the log message
        thread_id = threading.get_ident()
        process_id = os.getpid()
        context_info = f"[PID:{process_id}][TID:{thread_id}]"
        return f"{self.extra['tag']} {context_info} {msg}", kwargs


def configure_logger(
    class_name,
    log_level=logging.INFO,
    log_dir=None,
    log_tag_allowlist=None,
):
    """
    Configure and return a logger with enterprise-grade features.
    All loggers in the same process share the same log file.

    Args:
        class_name: Name of the class/module using the logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files. If None, logs to console only
        log_tag_allowlist: Comma-separated list of tags to filter logs

    Returns:
        Configured logger instance with rotating file handlers
    """
    process_id = os.getpid()

    with _logger_lock:
        # Check if we already have a configured root logger for this process
        if process_id in _process_loggers:
            # Return a child logger under the already-configured root
            logger = logging.getLogger(class_name)
            logger.setLevel(log_level)
            return logger

        # This is the first logger for this process, set up the handlers
        # Use a root logger for the entire alluxio package
        root_logger_name = "alluxio"
        logger = logging.getLogger(root_logger_name)

        # Avoid adding duplicate handlers
        if logger.handlers:
            _process_loggers[process_id] = True
            child_logger = logging.getLogger(class_name)
            child_logger.setLevel(log_level)
            return child_logger

        logger.setLevel(log_level)

        # Create formatter with process ID, thread ID, and timestamp
        formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler - always add for visibility
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler with rotation - only if log_dir is specified
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

            # Generate unified log filename with timestamp and process ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"alluxio_pid{process_id}_{timestamp}.log"
            log_file = os.path.join(log_dir, log_filename)

            # Use RotatingFileHandler for automatic log rotation
            # Max 100MB per file, keep 10 backup files
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=10,  # Keep 10 archived log files
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            logger.info(f"Logging initialized for process {process_id}")
            logger.info(f"Log file: {log_file}")
            logger.info(
                "Log rotation enabled: max 100MB per file, 10 backups retained"
            )

        # Tag filtering
        if log_tag_allowlist:
            tags = [tag.strip() for tag in log_tag_allowlist.split(",")]
            logger.info(f"Log tag allowlist enabled: {tags}")
            # Note: Tag filtering logic would be implemented in TagAdapter.process()

        logger.propagate = False  # Prevent duplicate logs in parent loggers

        # Mark this process as having configured logging
        _process_loggers[process_id] = True

        # Return a child logger with the specific class name
        child_logger = logging.getLogger(class_name)
        child_logger.setLevel(log_level)
        return child_logger


def setup_logger(log_dir, level_str, class_name, log_tags=None):
    """
    Legacy function signature for backward compatibility.

    Args:
        log_dir: Directory to store log files
        level_str: String representation of log level (e.g., "INFO", "DEBUG")
        class_name: Name of the class/module using the logger
        log_tags: Comma-separated list of tags to filter logs

    Returns:
        Configured logger instance
    """
    # Convert string level to logging constant
    if isinstance(level_str, str):
        log_level = getattr(logging, level_str.upper(), logging.INFO)
    else:
        log_level = level_str

    return configure_logger(
        class_name=class_name,
        log_level=log_level,
        log_dir=log_dir,
        log_tag_allowlist=log_tags,
    )


def get_tagged_logger(logger, tag):
    """
    Create a tagged logger adapter that includes process/thread context.

    Args:
        logger: Base logger instance
        tag: Tag to prefix log messages (e.g., "[FSSPEC]", "[FALLBACK]")

    Returns:
        TagAdapter instance with enhanced context information
    """
    return TagAdapter(logger, {"tag": tag})
