#!/usr/bin/env python3
"""
TrackPoint functionality module.
"""

import os
import json
import time
import datetime
import threading
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional
from opentelemetry import trace

# Import the necessary functions from userInfo
# We'll need to handle this carefully since we're splitting the module
from .userInfo import get_username, AppendUserInfo, get_default_observer_config


class TrackPointManager:
    """Manages track point logging with file rotation using RotatingFileHandler."""
    
    def __init__(self, module_name: str = "unknown", trackpoint_dir: str = None, max_file_size: int = None, max_files: int = None):
        """
        Initialize TrackPointManager.
        
        Args:
            trackpoint_dir: Directory to store trackpoint files
            max_file_size: Maximum size of each trackpoint file in bytes
            max_files: Maximum number of trackpoint files to maintain
        """
        config = get_default_observer_config()
        self.trackpoint_dir = trackpoint_dir or config.TRACKPOINT
        self.max_file_size = max_file_size or config.DEFAULT_MAX_FILE_SIZE
        self.max_files = max_files or config.DEFAULT_MAX_FILES
        self.module_name = module_name
        self.file_name = f"trackpoint_{module_name}_{get_username()}.trackpoint"
        
        # Ensure the directory exists
        Path(self.trackpoint_dir).mkdir(parents=True, exist_ok=True)
        
        # Thread lock for thread safety
        self._lock = threading.Lock()
        
        # Store logger instances by module name
        self._logger = None
        
    def _get_logger(self) -> logging.Logger:
        """Get or create a logger for a specific module."""
        with self._lock:
            if not self._logger:
                # Create logger for this module
                logger = logging.getLogger(f'trackpoint.logger.{self.module_name}')
                logger.setLevel(logging.INFO)
                # Prevent duplicate handlers
                if not logger.handlers:
                    file_path = os.path.join(self.trackpoint_dir, self.file_name)
                    # Create rotating file handler
                    handler = RotatingFileHandler(
                        file_path,
                        maxBytes=self.max_file_size,
                        backupCount=self.max_files - 1  # backupCount is the number of backup files to keep
                    )
                    
                    # Create formatter
                    formatter = logging.Formatter('%(message)s')  # Simple format for JSON
                    handler.setFormatter(formatter)
                    
                    logger.addHandler(handler)
                    logger.propagate = False  # Don't propagate to parent loggers
                
                self._logger = logger
            
            return self._logger
    
    def log_event(self, event_name: str, properties: Dict[str, str] = None, trace_id: str = "") -> None:
        """
        Log an event with its properties to trackpoint files.
        
        Args:
            module_name: Name of the module generating the event
            event_name: Name of the event being tracked
            properties: Dictionary of properties associated with the event
            trace_id: Trace ID to associate with the event
        """
        # Get the appropriate logger for this module
        logger = self._logger or self._get_logger()
        
        # Get current timestamp with milliseconds in ISO format
        # Get the current time in UTC
        utc_now = datetime.datetime.utcnow()
        
        # Convert to local time (assuming Beijing timezone with +0800 offset)
        # For simplicity, we'll use a fixed offset of +0800
        local_time = utc_now + datetime.timedelta(hours=8)
        
        # Format as ISO 8601 with milliseconds and timezone offset
        timestamp_ms = int((time.time() - int(time.time())) * 1000)
        formatted_time = local_time.strftime("%Y-%m-%dT%H:%M:%S") + f".{timestamp_ms:03d}+0800"
        
        # Prepare the event data
        event_data = {
            "time": formatted_time,
            "eventName": event_name,
            "module": self.module_name,
        }
        if not trace_id:
            span = trace.get_current_span()
            if span and span.get_span_context().trace_id != 0:
                trace_id = format(span.get_span_context().trace_id, '032x')
        
        # Add trace ID if provided
        if trace_id:
            event_data["traceId"] = trace_id
        # Add user info to the top level of event data
        # Since we can't directly import the function here, we'll create a minimal version
        user_properties = {}
        # We'll manually copy the logic from AppendUserInfo here
        # This is a simplified version - a full implementation would require more integration
        AppendUserInfo(user_properties)  # This should work if called in correct context
        # Filter out empty user properties and add them to the main event data
        non_empty_user_props = {k: v for k, v in user_properties.items() if v}
        event_data.update(non_empty_user_props)
        
        # Add custom properties in a nested 'properties' field
        if properties:
            event_data["properties"] = properties
        
        # Convert to JSON string
        json_line = json.dumps(event_data, separators=(',', ':')) + "\n"
        # 写到文件
        self._write_to_file(logger, json_line.strip())
    
    def _write_to_file(self, logger, json_line):
        """Write JSON line to file asynchronously."""
        logger.info(json_line)


# Global instance for trackpoint management
_trackpoint_manager = None


def init_trackpoint_manager(module_name: str, trackpoint_dir: str = None, max_file_size: int = None, max_files: int = None) -> TrackPointManager:
    """
    Initialize the trackpoint manager.
    
    Args:
        trackpoint_dir: Directory to store trackpoint files
        max_file_size: Maximum size of each trackpoint file in bytes
        max_files: Maximum number of trackpoint files to maintain
    
    Returns:
        TrackPointManager instance
    """
    global _trackpoint_manager
    if _trackpoint_manager is None:
        _trackpoint_manager = TrackPointManager(module_name, trackpoint_dir, max_file_size, max_files)
    return _trackpoint_manager


def track_event(event_name: str, properties: Dict[str, str] = None, trace_id: str = "") -> Optional[str]:
    """
    Log an event with its properties to trackpoint files.
    
    Args:
        event_name: Name of the event being tracked
        properties: Dictionary of properties associated with the event
        trace_id: Trace ID to associate with the event
    """
    # Initialize manager if not already done
    if _trackpoint_manager is None:
        err = 'Warning: TrackPointManager not initialized. Call init_trackpoint_manager() first.'
        print(err)
        return err
    
    _trackpoint_manager.log_event(event_name, properties, trace_id)



def track_flush() -> None:
    """Flush the trackpoint logger handlers."""
    if _trackpoint_manager:
        _trackpoint_manager.flush()


def track_shutdown() -> None:
    """Shutdown the trackpoint manager."""
    if _trackpoint_manager:
        _trackpoint_manager.shutdown()