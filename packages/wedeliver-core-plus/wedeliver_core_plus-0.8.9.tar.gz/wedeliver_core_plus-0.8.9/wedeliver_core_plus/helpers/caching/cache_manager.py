"""
CacheManager - Centralized cache operations manager.

Handles cache retrieval, storage, and validation for route handlers.
Uses thread pools for non-blocking async operations.

Supports both gevent Pool and ThreadPoolExecutor based on configuration.
"""

import os
import copy
from concurrent.futures import ThreadPoolExecutor
from flask import current_app
from flask_babel import force_locale
from wedeliver_core_plus.helpers.caching.cache_logger import (
    cache_debug, cache_info, cache_warning, cache_error
)


class CacheManager:
    """
    Manages cache operations for route handlers.

    Features:
    - Async cache writes using thread pool (non-blocking)
    - Cache validation in background
    - Cross-service metadata handling
    - Gevent-compatible pool operations
    """

    # Global pool for async cache writes
    # Reused across all requests for better resource management
    # Initialized lazily with config-based pool size
    # Supports both gevent Pool and ThreadPoolExecutor
    _write_pool = None
    _write_pool_initialized = False

    @classmethod
    def _get_write_pool(cls):
        """
        Get or create the write pool with gevent support.

        Uses gevent Pool or ThreadPoolExecutor based on CACHE_USE_GEVENT_POOL config.
        This ensures compatibility with gunicorn + gevent workers.
        """
        if not cls._write_pool_initialized:
            try:
                pool_size = current_app.config.get('CACHE_WRITE_POOL_SIZE', 10)
            except:
                pool_size = int(os.getenv('CACHE_WRITE_POOL_SIZE', '10'))

            # Import pool type detection function
            from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import _should_use_gevent_pool

            # Determine pool type based on configuration
            if _should_use_gevent_pool():
                from gevent.pool import Pool as GeventPool
                cls._write_pool = GeventPool(size=pool_size)
                cls._write_pool_initialized = True
                cache_debug(f"Initialized gevent write pool with {pool_size} greenlets")
            else:
                cls._write_pool = ThreadPoolExecutor(
                    max_workers=pool_size,
                    thread_name_prefix="cache-write"
                )
                cls._write_pool_initialized = True
                cache_debug(f"Initialized ThreadPoolExecutor write pool with {pool_size} workers")

        return cls._write_pool

    @classmethod
    def _submit_to_pool(cls, pool, func, *args):
        """
        Submit a function to a pool (gevent Pool or ThreadPoolExecutor).

        Handles the API difference between gevent Pool (spawn) and ThreadPoolExecutor (submit).

        Args:
            pool: gevent Pool or ThreadPoolExecutor
            func: Function to execute
            *args: Arguments to pass to the function
        """
        if hasattr(pool, 'spawn'):
            # gevent Pool
            pool.spawn(func, *args)
        else:
            # ThreadPoolExecutor
            pool.submit(func, *args)
    
    def __init__(self, cache_rule, path, request_data):
        """
        Initialize CacheManager.

        Args:
            cache_rule: Cache rule class (not instance)
            path: API endpoint path (may contain Flask placeholders like <string:step_name>)
            request_data: Request parameters (validated_data)
        """
        self.cache_rule = cache_rule

        # Compile path by replacing Flask placeholders with actual values
        self.path = self._compile_path(path, request_data)

        self.request_data = request_data
        self.cache_instance = None
        self.cache_key = None

    def _compile_path(self, path_template, request_data):
        """
        Replace Flask path placeholders with actual values from request_data.

        This ensures cache keys use actual URLs instead of route templates,
        preventing cache collisions between different path parameter values.

        Examples:
            "/api/product/<int:product_id>" + {"product_id": 123}
            → "/api/product/123"

            "/api/uber/<string:step_name>" + {"step_name": "vehicle_info"}
            → "/api/uber/vehicle_info"

            "/config/api/v1/lov/<group_type>/<value_type>" + {"group_type": "city", "value_type": "active"}
            → "/config/api/v1/lov/city/active"

        Args:
            path_template: Route path with Flask placeholders
            request_data: Dictionary containing path parameter values

        Returns:
            Compiled path with actual values
        """
        import re

        # Pattern to match Flask path parameters: <type:name> or <name>
        # Supports: <int:id>, <string:name>, <float:price>, <path:filepath>, <uuid:id>, <name>
        pattern = r'<(?:(?:int|float|string|path|uuid):)?(\w+)>'

        def replace_placeholder(match):
            param_name = match.group(1)
            # Get value from request_data, fallback to placeholder if not found
            value = request_data.get(param_name)
            if value is not None:
                return str(value)
            # If parameter not found, keep the placeholder (shouldn't happen in normal flow)
            cache_warning(f"Path parameter '{param_name}' not found in request_data, keeping placeholder")
            return match.group(0)

        compiled_path = re.sub(pattern, replace_placeholder, path_template)

        # Log if path was compiled (contains placeholders)
        if compiled_path != path_template:
            cache_debug(f"Compiled path: {path_template} → {compiled_path}")

        return compiled_path
        
    def initialize(self):
        """
        Initialize cache instance and generate cache key.

        Returns:
            bool: True if cache is configured and initialized, False otherwise
        """
        if not self.cache_rule:
            return False

        # Check if cache is enabled - skip initialization if disabled
        from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import is_cache_enabled
        if not is_cache_enabled():
            return False

        try:
            # Initialize the cache rule instance
            self.cache_instance = self.cache_rule(self.path)

            # Check if cache instance was successfully created
            if self.cache_instance is None or self.cache_instance.cache is None:
                return False

            # Generate cache key
            self.cache_key = self.cache_instance.make_key(self.request_data)

            return True
        except Exception as e:
            cache_warning(f"Initialization failed: {e}")
            return False
    
    def get_cached_response(self):
        """
        Retrieve cached response if available.
        
        Returns:
            Cached response data with is_cached flag, or None if cache miss
        """
        if not self.cache_instance or not self.cache_key:
            return None
            
        try:
            cached_data = self.cache_instance.get(self.cache_key)
            if cached_data is None:
                cache_debug(f"MISS for {self.path}")
                return None
                
            cache_debug(f"HIT for {self.path}")
            
            # Handle cache validation if enabled (async, non-blocking)
            self._validate_cache_async(cached_data)
            
            # Return response with is_cached flag
            return self._prepare_cached_response(cached_data)
            
        except Exception as e:
            cache_warning(f"Error retrieving cache: {e}")
            return None
    
    def store_response_async(self, output):
        """
        Store response in cache asynchronously (non-blocking).

        Uses gevent Pool or ThreadPoolExecutor to prevent blocking the response.

        Args:
            output: Serialized response data to cache
        """
        if not self.cache_instance or not self.cache_key or output is None:
            return

        # Check if async writes are enabled
        try:
            async_writes = current_app.config.get('CACHE_ASYNC_WRITES', True)
        except:
            async_writes = True

        if async_writes:
            # Submit to pool (returns immediately, non-blocking)
            write_pool = self._get_write_pool()
            self._submit_to_pool(write_pool, self._store_cache, self.cache_key, output)
            cache_debug(f"Queued async cache write for {self.path}")
        else:
            # Synchronous write (blocking)
            self._store_cache(self.cache_key, output)
            cache_debug(f"Sync cache write for {self.path}")
    
    def _store_cache(self, cache_key, data):
        """
        Internal method to store cache (runs in background thread).
        
        Args:
            cache_key: Cache key
            data: Data to cache
        """
        try:
            self.cache_instance.set(cache_key, data)
            cache_debug(f"✓ Async stored: {cache_key}")
        except Exception as e:
            cache_warning(f"✗ Async store failed for {cache_key}: {e}")
    
    def _prepare_cached_response(self, cached_data):
        """
        Prepare cached response with is_cached flag.
        
        Args:
            cached_data: Raw cached data
            
        Returns:
            Response data with is_cached flag added
        """
        # Make a deep copy to prevent validation thread from seeing the flag
        response_data = copy.deepcopy(cached_data)
        
        # Add is_cached flag
        if isinstance(response_data, dict):
            response_data["is_cached"] = True
        elif isinstance(response_data, list):
            # Add flag to each dict element in list
            for item in response_data:
                if isinstance(item, dict):
                    item["is_cached"] = True
        
        return response_data
    
    def _validate_cache_async(self, cached_data):
        """
        Validate cached data asynchronously in background.

        Uses BaseCacheRule's invalidation pool (gevent Pool or ThreadPoolExecutor)
        for gevent-compatible async execution.

        Strategy: Fetch fresh data and compare in BACKGROUND (with app context).

        Args:
            cached_data: Cached data to validate
        """
        try:
            validation_mode = current_app.config.get('CACHE_VALIDATION_MODE', 'off')

            if validation_mode == 'off':
                return

            if not self.cache_instance._should_validate(validation_mode):
                return

            # Capture config values and app instance in main thread
            metrics_enabled = current_app.config.get('CACHE_VALIDATION_METRICS_ENABLED', True)
            app = current_app._get_current_object()

            # ============================================================
            # FETCH FRESH DATA + COMPARE IN BACKGROUND POOL
            # ============================================================
            def _async_validate():
                """
                Background validation function.

                Runs with app context and test_request_context to allow database queries
                and business logic execution with proper request context.

                Uses test_request_context with Accept-Language header so that
                find_user_language() in auth.py can read the header correctly,
                matching the behavior of the original request.
                """

                with app.app_context():
                    # Use test_request_context with Accept-Language header
                    # This provides a fake request context so request.headers works
                    # and find_user_language() returns the correct language
                    with app.test_request_context(headers={'Accept-Language': self._user_language}):
                        # Also set g.user for any code that reads from g.user directly
                        from flask import g
                        g.user = {'language': self._user_language}

                        with force_locale(self._user_language):
                            try:
                                self.cache_instance._validate_cache_data(
                                    cache_key=self.cache_key,
                                    cached_data=cached_data,
                                    route_handler_func=self._route_handler_func,
                                    validated_data=self.request_data,
                                    schema=self._schema,
                                    many=self._many,
                                    metrics_enabled=metrics_enabled,
                                    app=app  # Pass app instance for context
                                )
                            except Exception as e:
                                cache_warning(f"Background validation error: {e}")

            # Use BaseCacheRule's invalidation pool (gevent-compatible)
            from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule
            validation_pool = BaseCacheRule._get_invalidation_pool()
            self._submit_to_pool(validation_pool, _async_validate)
            cache_debug(f"Queued async validation for {self.path}")

        except Exception as e:
            cache_warning(f"Error setting up cache validation: {e}")
    
    def set_validation_context(self, route_handler_func, schema, many, user_language):
        """
        Set context needed for cache validation.
        
        Args:
            route_handler_func: The route handler function
            schema: Marshmallow schema for serialization
            many: Boolean flag for list serialization
        """
        self._route_handler_func = route_handler_func
        self._schema = schema
        self._many = many
        self._user_language = user_language or 'ar'
    


