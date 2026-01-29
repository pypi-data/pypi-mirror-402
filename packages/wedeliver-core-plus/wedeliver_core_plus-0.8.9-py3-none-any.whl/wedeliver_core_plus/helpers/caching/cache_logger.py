"""
Cache Logger - Centralized logging for cache system.

Respects CACHE_DEBUG environment variable and Flask app.config.
Only logs cache debug messages when CACHE_DEBUG=True.

Usage:
    from wedeliver_core_plus.helpers.caching.cache_logger import (
        cache_debug, cache_info, cache_warning, cache_error
    )
    
    # Debug logs (only shown when CACHE_DEBUG=True)
    cache_debug("Cache hit for /api/customers")
    
    # Info logs (always shown)
    cache_info("Cache system initialized")
    
    # Warning logs (always shown)
    cache_warning("Redis connection failed")
    
    # Error logs (always shown)
    cache_error("Cache invalidation failed")

Environment Variables:
    CACHE_DEBUG: Enable/disable cache debug logs (default: False)
    DEBUG: Fallback if CACHE_DEBUG not set (default: False)

Examples:
    # Production (no debug logs)
    CACHE_DEBUG=false
    
    # Development (all debug logs)
    CACHE_DEBUG=true
    
    # Granular control
    DEBUG=false          # Disable general debug logs
    CACHE_DEBUG=true     # Enable only cache debug logs
"""

import os
import logging


class CacheLogger:
    """
    Centralized logger for cache system.
    
    Automatically respects CACHE_DEBUG flag from environment or Flask config.
    Provides different log levels: DEBUG, INFO, WARNING, ERROR.
    """
    
    _logger = None
    _cache_debug_enabled = None
    
    @classmethod
    def _get_logger(cls):
        """Get or create logger instance."""
        if cls._logger is None:
            cls._logger = logging.getLogger('cache')
        return cls._logger
    
    @classmethod
    def _is_cache_debug_enabled(cls):
        """
        Check if CACHE_DEBUG mode is enabled.
        
        Priority:
        1. Flask app.config.get("CACHE_DEBUG")
        2. Environment variable CACHE_DEBUG
        3. Flask app.config.get("DEBUG") (fallback)
        4. Environment variable DEBUG (fallback)
        5. Default: False
        """
        # Return cached value if already determined
        if cls._cache_debug_enabled is not None:
            return cls._cache_debug_enabled
        
        try:
            # Try to get from Flask config first
            from flask import current_app

            # Check CACHE_DEBUG flag (highest priority)
            cache_debug = current_app.config.get("CACHE_DEBUG")
            if cache_debug is not None:
                cls._cache_debug_enabled = cache_debug
                return cls._cache_debug_enabled

            # Fallback to DEBUG flag
            debug = current_app.config.get("DEBUG", False)
            cls._cache_debug_enabled = debug
            return cls._cache_debug_enabled

        except (RuntimeError, ModuleNotFoundError, ImportError):
            # No Flask context or Flask not installed, check environment variables
            
            # Check CACHE_DEBUG env var (highest priority)
            cache_debug_env = os.getenv("CACHE_DEBUG")
            if cache_debug_env is not None:
                cls._cache_debug_enabled = cache_debug_env.lower() in ("true", "1", "yes")
                return cls._cache_debug_enabled
            
            # Fallback to DEBUG env var
            debug_env = os.getenv("DEBUG", "False")
            cls._cache_debug_enabled = debug_env.lower() in ("true", "1", "yes")
            return cls._cache_debug_enabled
    
    @classmethod
    def reset_cache(cls):
        """Reset cached debug flag (useful for testing)."""
        cls._cache_debug_enabled = None
    
    @classmethod
    def debug(cls, message):
        """
        Log DEBUG level message (only if CACHE_DEBUG=True).
        
        Args:
            message: Log message (without [Cache] prefix)
        """
        if cls._is_cache_debug_enabled():
            try:
                from flask import current_app
                current_app.logger.debug(f"[Cache] {message}")
            except (RuntimeError, ModuleNotFoundError, ImportError):
                # Fallback to print if no Flask context or Flask not installed
                print(f"[Cache DEBUG] {message}")
    
    @classmethod
    def info(cls, message):
        """
        Log INFO level message (always shown).

        Args:
            message: Log message (without [Cache] prefix)
        """
        try:
            from flask import current_app
            current_app.logger.info(f"[Cache] {message}")
        except (RuntimeError, ModuleNotFoundError, ImportError):
            print(f"[Cache INFO] {message}")

    @classmethod
    def warning(cls, message):
        """
        Log WARNING level message (always shown).

        Args:
            message: Log message (without [Cache] prefix)
        """
        try:
            from flask import current_app
            current_app.logger.warning(f"[Cache] {message}")
        except (RuntimeError, ModuleNotFoundError, ImportError):
            print(f"[Cache WARNING] {message}")

    @classmethod
    def error(cls, message):
        """
        Log ERROR level message (always shown).

        Args:
            message: Log message (without [Cache] prefix)
        """
        try:
            from flask import current_app
            current_app.logger.error(f"[Cache] {message}")
        except (RuntimeError, ModuleNotFoundError, ImportError):
            print(f"[Cache ERROR] {message}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def cache_debug(message):
    """
    Log cache debug message (only if CACHE_DEBUG=True).
    
    Args:
        message: Log message without [Cache] prefix
    
    Example:
        cache_debug("Cache hit for /api/customers")
        # Output (if CACHE_DEBUG=True): [Cache] Cache hit for /api/customers
    """
    CacheLogger.debug(message)


def cache_info(message):
    """
    Log cache info message (always shown).
    
    Args:
        message: Log message without [Cache] prefix
    
    Example:
        cache_info("Cache system initialized")
        # Output: [Cache] Cache system initialized
    """
    CacheLogger.info(message)


def cache_warning(message):
    """
    Log cache warning message (always shown).
    
    Args:
        message: Log message without [Cache] prefix
    
    Example:
        cache_warning("Redis connection failed")
        # Output: [Cache] Redis connection failed
    """
    CacheLogger.warning(message)


def cache_error(message):
    """
    Log cache error message (always shown).
    
    Args:
        message: Log message without [Cache] prefix
    
    Example:
        cache_error("Cache invalidation failed")
        # Output: [Cache] Cache invalidation failed
    """
    CacheLogger.error(message)

