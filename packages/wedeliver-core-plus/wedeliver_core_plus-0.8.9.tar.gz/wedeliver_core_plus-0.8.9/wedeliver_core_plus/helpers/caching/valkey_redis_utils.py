import json
import hashlib
import os
from datetime import timedelta, datetime
from concurrent.futures import ThreadPoolExecutor
from redis import Redis, exceptions as redis_exceptions
from sqlalchemy import event, inspect
from flask import current_app
from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import (
    evaluate_invalidation_conditions,
    format_value_for_cache_key,
    build_cache_key_pattern,
    invalidate_cache_by_pattern
)
from wedeliver_core_plus.helpers.caching.cache_logger import (
    cache_debug, cache_info, cache_warning, cache_error
)


class BaseCacheRule:
    """
    Base caching rule with filter-based invalidation.

    Features:
    - Uses singleton Redis (Valkey) client
    - Service isolation via SERVICE_NAME prefix
    - Filter-based invalidation with operators (=, !=, in, >, <)
    - AND/OR filter logic
    - Path-based or granular invalidation
    - Function caching with automatic invalidation
    - Cross-service invalidation support

    Cache key format:
        {service_name}/path:key1=val1:key2=val2:hash

        Example:
            thrivve-service/core/api/v1/mobile/home/messages:customer_id=123:app_version=app_version:hash

    scoped_cache_keys format:
        Defines the structure of cache keys and their sources.

        {
            "customer_id": "api_params",  # From API request parameters
            "app_version": "__static_value__('app_version')",  # Static value
            "contract_ids": "__function_call__(get_contract_ids, [customer_id])"  # Function call
        }

        Sources:
            - "api_params": Get value from API request parameters
            - "__static_value__('value')": Use static value
            - "__function_call__(func, [params])": Execute function and cache result

    model_invalidation_conditions format:
        Defines when and how to invalidate cache based on model changes.

        All models are registered via Pub/Sub. Each worker decides if it should
        register based on ModelDiscovery (if model exists in this service).

        {
            "ModelName": {
                "events": ["after_update", "after_insert"],  # SQLAlchemy events
                "filters": [(field, operator, scoped_key), ...],  # AND logic
                "or_filters": [(field, operator, scoped_key), ...],  # OR logic
                "invalidate_scope": "*"  # "*" = invalidate all (path-based), None = granular
            }
        }

        Operators:
            - "=": Equal
            - "!=": Not equal
            - "in": In list/array
            - ">": Greater than
            - "<": Less than

        Examples:
            # Simple equality filter
            "Customer": {
                "events": ["after_update"],
                "filters": [("id", "=", "customer_id")]
            }

            # Multiple AND filters
            "ListOfValues": {
                "events": ["after_update"],
                "filters": [
                    ("group_type", "=", "app_version"),
                    ("status", "=", "active")
                ],
                "invalidate_scope": "*"  # Invalidate all when conditions met
            }

            # OR filters
            "Transaction": {
                "events": ["after_update"],
                "or_filters": [
                    ("status", "=", "completed"),
                    ("status", "=", "pending")
                ],
                "filters": [("customer_id", "=", "customer_id")]
            }

            # IN operator with function call
            "ContractInstallment": {
                "events": ["after_update"],
                "filters": [("contract_id", "in", "contract_ids")]
            }

    Function caching:
        - Functions defined in scoped_cache_keys are executed during cache creation
        - Results cached separately: {service_name}:function_cache:{func}:{params}
        - Automatically invalidated when main cache is invalidated
        - Functions must be defined in the cache rule class

        Example:
            scoped_cache_keys = {
                "contract_ids": "__function_call__(get_contract_ids, [customer_id])"
            }

            def get_contract_ids(self, customer_id):
                # Query contracts for customer
                return [101, 102, 103]

            Cache key: thrivve-service:function_cache:get_contract_ids:customer_id=123
            Cached value: [101, 102, 103]
    """

    # DEPRECATED - Old registry (will be removed)
    _listeners_registered = set()
    _cache_rule_registry = {}

    # Singleton instances
    _redis_client = None  # Singleton Redis connection
    _service_name = None  # Service name prefix for cache keys
    _validation_metrics = None  # Singleton metrics instance for cache validation
    _model_discovery = None  # Singleton ModelDiscovery instance

    # Global thread pool for async cache invalidation
    # Reused across all cache rules for better resource management
    # Initialized lazily with config-based pool size
    _invalidation_pool = None
    _invalidation_pool_initialized = False

    # Global thread pool for async registration
    # Handles publishing registration events to Pub/Sub
    _registration_pool = None
    _registration_pool_initialized = False

    # Cache configuration
    ttl = timedelta(minutes=5)
    scoped_cache_keys = {}  # Defines cache key structure and sources
    model_invalidation_conditions = {}  # Defines invalidation filters and conditions
    include_language_in_cache_key = True  # Include language in cache key hash by default

    def __init__(self, path: str = None):
        self.path = path

        # Check if cache is enabled FIRST - skip all initialization if disabled
        from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import is_cache_enabled
        if not is_cache_enabled():
            self.cache = None
            return  # Skip all initialization for zero overhead

        # Initialize service name from Flask config (once per class)
        if BaseCacheRule._service_name is None:
            BaseCacheRule._service_name = current_app.config.get("SERVICE_NAME", "default-service")

        # Initialize ModelDiscovery singleton (once per class)
        if BaseCacheRule._model_discovery is None:
            try:
                from wedeliver_core_plus.helpers.model_discovery import ModelDiscovery
                BaseCacheRule._model_discovery = ModelDiscovery()
            except Exception as e:
                cache_warning(f"ModelDiscovery initialization failed: {e}")
                BaseCacheRule._model_discovery = None

        # Use shared Redis connection (singleton)
        if BaseCacheRule._redis_client is None:
            BaseCacheRule._redis_client = self._create_redis_client()

        self.cache = BaseCacheRule._redis_client

        # Only register invalidation events if cache is available
        if self.cache is not None:
            self._register_all_invalidation_events()

    # ---------------- Redis Singleton Setup ----------------

    def _create_redis_client(self):
        """Create a shared Redis/Valkey client safely, reading config from Flask."""
        app = current_app

        # Check if Redis is enabled via CACHE_ENABLE flag
        enable_redis = app.config.get("CACHE_ENABLE", False)

        if not enable_redis:
            cache_info("Redis is disabled via ENABLE_REDIS flag")
            return None

        host = app.config.get("CACHE_VALKEY_HOST", "valkey-redis")
        port = app.config.get("CACHE_VALKEY_PORT", 6379)
        ssl = app.config.get("CACHE_VALKEY_SSL", False)

        try:
            client = Redis(
                host=host,
                port=port,
                ssl=ssl,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            client.ping()
            cache_info(f"Connected to {host}:{port}")
            return client
        except redis_exceptions.ConnectionError as e:
            # Gracefully handle connection failures in ALL environments
            cache_warning(f"Connection failed: {e}")
            return None

    # ---------------- Language Support ----------------

    def _should_include_language(self):
        """
        Check if language should be included in cache key hash.

        Returns:
            bool: True if language should be included (default), False otherwise
        """
        return getattr(self, 'include_language_in_cache_key', True)

    def _get_current_language(self):
        """
        Get current user language from Auth.

        Returns:
            str: Language code ('ar' or 'en'), or None if not available
        """
        try:
            from wedeliver_core_plus.helpers.auth import Auth
            language = Auth.get_user_language()
            return language if language in ['ar', 'en'] else 'ar'
        except Exception as e:
            cache_warning(f"Failed to get user language: {e}")
            return 'ar'  # Default to Arabic

    def _enrich_params_with_language(self, params: dict) -> dict:
        """
        Enrich params with language for hash calculation ONLY.

        This ensures different languages produce different MD5 hashes,
        even if all other params are identical.

        Language is NOT added to cache key tags, so invalidation patterns
        remain simple and invalidate all languages together.

        Args:
            params: Original request parameters

        Returns:
            dict: Params with language added (if enabled)
        """
        if not self._should_include_language():
            return params

        enriched = params.copy() if params else {}
        language = self._get_current_language()

        if language:
            # Add to params for hash calculation
            # Use special key to avoid conflicts with actual params
            enriched['__cache_language__'] = language

        return enriched

    # ---------------- Core cache ops ----------------

    def make_key(self, params: dict) -> str:
        """
        Create cache key using scoped_cache_keys configuration.

        Format: {service_name}/path:key1=val1:key2=val2:hash

        Language is automatically included in hash calculation (not in tags) unless
        include_language_in_cache_key=False. This ensures different languages get
        different cache entries, but invalidation patterns remain simple and invalidate
        all languages together.

        Args:
            params: Dictionary of API parameters

        Returns:
            Cache key string with service prefix and scoped tags

        Example:
            scoped_cache_keys = {
                "customer_id": "api_params",
                "app_version": "__static_value__('app_version')",
                "contract_ids": "__function_call__(get_contract_ids, [customer_id])"
            }
            params = {"customer_id": 123}

            → thrivve-service/path:customer_id=123:app_version=app_version:contract_ids=[101,102]:hash_abc123
            (hash_abc123 includes language in calculation)
        """
        import re

        # Enrich params with language for hash calculation (not for tags)
        enriched_params = self._enrich_params_with_language(params)

        raw = json.dumps(enriched_params or {}, sort_keys=True)
        digest = hashlib.md5(raw.encode()).hexdigest()

        # Build tags from scoped_cache_keys
        if self.scoped_cache_keys:
            tags = []

            for key, source in self.scoped_cache_keys.items():
                value = None

                # Handle api_params
                if source == "api_params":
                    if key in params:
                        value = params[key]

                # Handle static values
                elif isinstance(source, str) and source.startswith("__static_value__"):
                    match = re.match(r"__static_value__\(['\"](.+?)['\"]\)", source)
                    if match:
                        value = match.group(1)

                # Handle function calls
                elif isinstance(source, str) and "__function_call__" in source:
                    # Execute function and get result
                    match = re.match(r"__function_call__\((\w+),\s*\[([^\]]+)\]\)", source)
                    if match:
                        func_name = match.group(1)
                        param_specs = [p.strip() for p in match.group(2).split(",")]

                        # Parse param specs to separate param names from :scoped_key markers
                        # Format: "customer_id:scoped_key" or just "customer_id"
                        func_params = {}
                        scoped_params = []

                        for param_spec in param_specs:
                            if ":scoped_key" in param_spec:
                                param_name = param_spec.replace(":scoped_key", "").strip()
                                scoped_params.append(param_name)
                            else:
                                param_name = param_spec

                            # Extract param value from API params
                            if param_name in params:
                                func_params[param_name] = params[param_name]

                        # Get function from cache rule class
                        if hasattr(self, func_name):
                            func = getattr(self, func_name)

                            try:
                                # Build function cache key (only with scoped params)
                                scoped_func_params = {k: v for k, v in func_params.items() if k in scoped_params}

                                # Build the function cache key
                                param_parts = []
                                for k, v in sorted(scoped_func_params.items()):
                                    formatted_value = format_value_for_cache_key(v)
                                    param_parts.append(f"{k}={formatted_value}")
                                param_str = ":".join(param_parts) if param_parts else "no_params"
                                func_cache_key = f"{self._service_name}:function_cache:{func_name}:{param_str}"

                                # Check if function result is already cached
                                cached_result = self._get_cached_function_result(func_cache_key)

                                if cached_result is not None:
                                    # Use cached result (no function execution!)
                                    value = cached_result
                                    cache_debug(f"Using cached function result for {func_name}({scoped_func_params})")
                                else:
                                    # Execute function only if not cached
                                    result = func(**func_params)
                                    value = result

                                    # Cache the result
                                    self._cache_function_result(func_name, scoped_func_params, result)
                                    cache_debug(f"Executed and cached function {func_name}({scoped_func_params})")

                            except Exception as e:
                                cache_warning(f"Error executing function {func_name}: {e}")

                # Add to tags if value was resolved
                if value is not None:
                    formatted_value = format_value_for_cache_key(value)
                    tags.append(f"{key}={formatted_value}")

            if tags:
                tag_str = ":".join(tags)
                return f"{self._service_name}:{self.path}:{tag_str}:{digest}"

        return f"{self._service_name}:{self.path}:{digest}"

    def get(self, key: str):
        if not self.cache:
            return None
        try:
            data = self.cache.get(key)
            return json.loads(data) if data else None
        except redis_exceptions.RedisError as e:
            self._warn(f"get() failed: {e}")
            return None

    def set(self, key: str, data: dict):
        """
        Store cache data.

        Note: Function calls in scoped_cache_keys are executed during make_key(),
        so function caching happens automatically during key generation.

        Args:
            key: Cache key
            data: Response data to cache
            api_params: API parameters (not used, kept for backward compatibility)
        """
        if not self.cache:
            return
        try:
            # Store main cache data
            self.cache.setex(key, int(self.ttl.total_seconds()), json.dumps(data))
        except redis_exceptions.RedisError as e:
            self._warn(f"set() failed: {e}")

    def invalidate_by_path(self):
        """Invalidate all cache entries for this path (path-based invalidation)."""
        if not self.cache or not self.path:
            return
        try:
            pattern = f"{self._service_name}:{self.path}:*"
            deleted = invalidate_cache_by_pattern(self.cache, pattern)
            if deleted > 0:
                cache_debug(f"Invalidated {deleted} keys for {self.path}")
        except redis_exceptions.RedisError as e:
            self._warn(f"invalidate_by_path() failed: {e}")

    def invalidate_by_params(self, params: dict):
        """
        Invalidate cache entries matching specific parameters (granular invalidation).

        Uses pattern matching with scoped_cache_keys to find and delete matching keys.
        Also invalidates function cache entries for the same parameters.

        Args:
            params: Dictionary of parameters to match (e.g., {"customer_id": 123})

        Example:
            scoped_cache_keys = {"customer_id": "api_params", "app_version": "__static_value__('app_version')"}
            params = {"customer_id": 123}
            Pattern: {service_name}/path:customer_id=123:*
            Matches: {service_name}/path:customer_id=123:app_version=app_version:hash
        """
        if not self.cache or not self.path:
            return

        if not params:
            cache_warning("invalidate_by_params called with empty params, falling back to path invalidation")
            self.invalidate_by_path()
            return

        try:
            # Build pattern with metadata tags from params
            tags = []

            for key in self.scoped_cache_keys.keys():
                if key in params:
                    value = format_value_for_cache_key(params[key])
                    tags.append(f"{key}={value}")

            if not tags:
                cache_warning("No valid scoped keys found in params, falling back to path invalidation")
                self.invalidate_by_path()
                return

            # Create pattern: {service_name}/path:field1=value1:*
            tag_str = ":".join(tags)
            pattern = f"{self._service_name}:{self.path}:{tag_str}:*"

            deleted = invalidate_cache_by_pattern(self.cache, pattern)
            if deleted > 0:
                cache_debug(f"Invalidated {deleted} key(s) matching pattern: {pattern}")

            # Also invalidate function cache for these params
            self._invalidate_function_cache(params)

        except redis_exceptions.RedisError as e:
            self._warn(f"invalidate_by_params() failed: {e}")

    # ---------------- SQLAlchemy event setup ----------------

    def _register_all_invalidation_events(self):
        """
        Publish registration events for ALL models via Pub/Sub (async).

        All models (regardless of service) are published to Pub/Sub.
        Each worker decides if it should register based on ModelDiscovery.

        This method submits registration to a pool for async processing.
        """
        # Get registration pool
        pool = self._get_registration_pool()

        # Submit registration to pool (async, non-blocking)
        if hasattr(pool, 'spawn'):
            # gevent Pool
            pool.spawn(self._publish_all_registrations)
        else:
            # ThreadPoolExecutor
            pool.submit(self._publish_all_registrations)

    def _publish_all_registrations(self):
        """
        Publish bulk registration event for all models to Pub/Sub (runs in background thread).

        This publishes ALL models in a single bulk message without checking if they exist locally.
        All workers will receive the message and decide if they should register based on ModelDiscovery.

        Uses environment variable for SERVICE_NAME to avoid app context issues in background threads.
        """
        from wedeliver_core_plus.helpers.caching.valkey_pubsub import ValkeyRegistrationPublisher

        # Get service name from environment (no app context needed in background thread)
        service_name = os.environ.get("SERVICE_NAME", "default-service")

        publisher = ValkeyRegistrationPublisher.get_instance()

        try:
            # Publish all models in one bulk message (more efficient than one-by-one)
            publisher.publish_bulk(
                models=self.model_invalidation_conditions,
                path=self.path,
                scoped_cache_keys=self.scoped_cache_keys,
                service_name=service_name
            )
            cache_debug(f"[Cache] Published bulk registration for {len(self.model_invalidation_conditions)} models on {self.path}")
        except Exception as e:
            cache_error(f"Failed to publish bulk registration: {e}")

    # ---------------- Async Invalidation Methods ----------------

    @classmethod
    def _get_invalidation_pool(cls):
        """
        Get or create the invalidation pool with config-based size.

        Uses gevent Pool or ThreadPoolExecutor based on CACHE_USE_GEVENT_POOL config.
        """
        if not cls._invalidation_pool_initialized:
            try:
                pool_size = current_app.config.get('CACHE_INVALIDATION_POOL_SIZE', 20)
            except:
                pool_size = int(os.getenv('CACHE_INVALIDATION_POOL_SIZE', '20'))

            # Import pool type detection function
            from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import _should_use_gevent_pool

            # Determine pool type based on configuration
            if _should_use_gevent_pool():
                from gevent.pool import Pool as GeventPool
                cls._invalidation_pool = GeventPool(size=pool_size)
                cls._invalidation_pool_initialized = True
                cache_debug(f"Initialized gevent invalidation pool with {pool_size} greenlets")
            else:
                # Use ThreadPoolExecutor
                cls._invalidation_pool = ThreadPoolExecutor(
                    max_workers=pool_size,
                    thread_name_prefix="cache-invalidate"
                )
                cls._invalidation_pool_initialized = True
                cache_debug(f"Initialized ThreadPoolExecutor invalidation pool with {pool_size} workers")

        return cls._invalidation_pool

    @classmethod
    def _get_registration_pool(cls):
        """
        Get or create the registration pool for async Pub/Sub publishing.

        Uses gevent Pool or ThreadPoolExecutor based on CACHE_USE_GEVENT_POOL config.
        """
        if not cls._registration_pool_initialized:
            try:
                pool_size = current_app.config.get('CACHE_REGISTRATION_POOL_SIZE', 5)
            except:
                pool_size = int(os.getenv('CACHE_REGISTRATION_POOL_SIZE', '5'))

            # Import pool type detection function
            from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import _should_use_gevent_pool

            # Determine pool type based on configuration
            if _should_use_gevent_pool():
                from gevent.pool import Pool as GeventPool
                cls._registration_pool = GeventPool(size=pool_size)
                cls._registration_pool_initialized = True
                cache_debug(f"Initialized gevent registration pool with {pool_size} greenlets")
            else:
                # Use ThreadPoolExecutor
                cls._registration_pool = ThreadPoolExecutor(
                    max_workers=pool_size,
                    thread_name_prefix="cache-register"
                )
                cls._registration_pool_initialized = True
                cache_debug(f"Initialized ThreadPoolExecutor registration pool with {pool_size} workers")

        return cls._registration_pool

    def _invalidate_async(self, keys):
        """
        Invalidate cache keys asynchronously using Redis pipeline.
        Non-blocking operation - runs in background pool.

        Args:
            keys: List of cache keys to delete
        """
        if not keys:
            return

        # Submit to pool (returns immediately, non-blocking)
        invalidation_pool = self._get_invalidation_pool()

        # Use spawn() for gevent Pool, submit() for ThreadPoolExecutor
        if hasattr(invalidation_pool, 'spawn'):
            # gevent Pool
            invalidation_pool.spawn(self._batch_delete_keys, keys)
        else:
            # ThreadPoolExecutor
            invalidation_pool.submit(self._batch_delete_keys, keys)
        cache_debug(f"Queued async invalidation of {len(keys)} keys")

    def _batch_delete_keys(self, keys):
        """
        Delete multiple keys efficiently using Redis pipeline.

        Uses Redis pipeline to batch delete operations for better performance.
        Can be called synchronously or asynchronously via thread pool.

        Args:
            keys: List of cache keys to delete
        """
        if not keys or not self.cache:
            return

        try:
            # Use Redis pipeline for batch operations
            pipeline = self.cache.pipeline()

            for key in keys:
                pipeline.delete(key)

            # Execute all deletes in one round trip
            results = pipeline.execute()

            # Count successful deletions
            deleted_count = sum(1 for r in results if r > 0)

            cache_debug(f"✓ Batch deleted {deleted_count}/{len(keys)} keys")

            # Log individual keys if needed (for debugging)
            if deleted_count < len(keys):
                for i, (key, result) in enumerate(zip(keys, results)):
                    if result == 0:
                        cache_debug(f"Key not found: {key}")

        except redis_exceptions.RedisError as e:
            cache_error(f"✗ Batch delete failed: {e}")
        except Exception as e:
            cache_error(f"✗ Unexpected error during batch delete: {e}")

    # ---------------- Helpers ----------------

    def _warn(self, msg: str):
        cache_warning(f"{msg}")

    def _get_cached_function_result(self, func_cache_key):
        """
        Retrieve cached function result from Redis.

        Args:
            func_cache_key: Function cache key

        Returns:
            Cached result if found, None otherwise

        Example:
            func_cache_key = "thrivve-service:function_cache:get_contract_ids:customer_id=123"
            → Returns [101, 102, 103] if cached, None otherwise
        """
        if not self.cache:
            return None

        try:
            cached_data = self.cache.get(func_cache_key)
            if cached_data:
                result = json.loads(cached_data)
                cache_debug(f"Retrieved cached function result: {func_cache_key}")
                return result
            return None
        except Exception as e:
            cache_warning(f"Error retrieving cached function result: {e}")
            return None

    def _cache_function_result(self, func_name, func_params, result):
        """
        Cache function result separately for invalidation tracking.

        Cache key format: {service_name}:function_cache:{func_name}:{param1}={value1}

        Args:
            func_name: Name of the function
            func_params: Dict of parameters used to call the function
            result: Function result to cache

        Example:
            func_name = "get_contract_ids"
            func_params = {"customer_id": 123}
            result = [101, 102, 103]

            Cache key: thrivve-service:function_cache:get_contract_ids:customer_id=123
            Cached value: [101, 102, 103]
        """
        if not self.cache:
            return

        try:
            # Build function cache key
            param_parts = []
            for key, value in sorted(func_params.items()):
                formatted_value = format_value_for_cache_key(value)
                param_parts.append(f"{key}={formatted_value}")

            param_str = ":".join(param_parts) if param_parts else "no_params"
            cache_key = f"{self._service_name}:function_cache:{func_name}:{param_str}"

            # Cache the result with same TTL as main cache
            self.cache.setex(cache_key, int(self.ttl.total_seconds()), json.dumps(result))
            cache_debug(f"Cached function result: {cache_key} = {result}")
        except Exception as e:
            cache_warning(f"Error caching function result: {e}")

    # ---------------- Function Call Support ----------------

    def _build_function_cache_key(self, func_name: str, params: dict):
        """
        Build cache key for function result.

        Format: {service_name}:function_cache:{func_name}:{param1}={value1}:{param2}={value2}

        Args:
            func_name: Function name (e.g., "get_contract_ids")
            params: Function parameters (e.g., {"customer_id": 123})

        Returns:
            str: Function cache key
        """
        tags = []
        for param_name, value in sorted(params.items()):
            formatted_value = format_value_for_cache_key(value)
            tags.append(f"{param_name}={formatted_value}")

        tag_str = ":".join(tags)
        return f"{self._service_name}:function_cache:{func_name}:{tag_str}"

    @classmethod
    def get_function_cache_result(cls, func_name: str, params: dict):
        """
        Retrieve cached function result.

        Args:
            func_name: Function name (e.g., "get_contract_ids")
            params: Function parameters (e.g., {"customer_id": 123})

        Returns:
            Cached function result or None if not found
        """
        if not cls._redis_client:
            return None

        # Build function cache key (need service name)
        tags = []
        for param_name, value in sorted(params.items()):
            formatted_value = format_value_for_cache_key(value)
            tags.append(f"{param_name}={formatted_value}")

        tag_str = ":".join(tags)
        func_cache_key = f"{cls._service_name}:function_cache:{func_name}:{tag_str}"

        try:
            data = cls._redis_client.get(func_cache_key)
            return json.loads(data) if data else None
        except redis_exceptions.RedisError as e:
            cache_warning(f"Failed to get function cache: {e}")
            return None

    def _invalidate_function_cache(self, api_params: dict):
        """
        Invalidate function cache entries for given api_params.

        Scans scoped_cache_keys for function calls and invalidates their cache.
        Only includes params marked with :scoped_key in the cache key.

        Args:
            api_params: API parameters (e.g., {"customer_id": 123})
        """
        import re

        if not self.cache:
            return

        for key, source in self.scoped_cache_keys.items():
            if not isinstance(source, str) or "__function_call__" not in source:
                continue

            # Parse function call
            match = re.match(r"__function_call__\((\w+),\s*\[([^\]]+)\]\)", source)
            if not match:
                continue

            func_name = match.group(1)
            param_specs = [p.strip() for p in match.group(2).split(",")]

            # Extract only scoped params from api_params
            func_params = {}
            for param_spec in param_specs:
                if ":scoped_key" in param_spec:
                    param_name = param_spec.replace(":scoped_key", "").strip()
                    if param_name in api_params:
                        func_params[param_name] = api_params[param_name]

            if func_params:
                # Build and delete function cache key (only with scoped params)
                func_cache_key = self._build_function_cache_key(func_name, func_params)
                try:
                    deleted = self.cache.delete(func_cache_key)
                    if deleted > 0:
                        cache_debug(f"Invalidated function cache: {func_cache_key}")
                except redis_exceptions.RedisError as e:
                    cache_warning(f"Failed to invalidate function cache: {e}")

    # ---------------- Cache Validation Methods ----------------

    @classmethod
    def _get_validation_metrics(cls):
        """
        Get or create singleton metrics instance for cache validation.

        Returns:
            CacheValidationMetrics: Singleton metrics instance
        """
        if cls._validation_metrics is None:
            from wedeliver_core_plus.helpers.caching.cache_validation_metrics import CacheValidationMetrics
            cls._validation_metrics = CacheValidationMetrics()
        return cls._validation_metrics

    def _should_validate(self, validation_mode):
        """
        Determine if this request should be validated based on mode.

        Args:
            validation_mode: Validation mode ('off', 'sample', 'always')

        Returns:
            bool: True if validation should be performed
        """
        import random

        if validation_mode == 'always':
            return True
        elif validation_mode == 'sample':
            sample_rate = current_app.config.get('CACHE_VALIDATION_SAMPLE_RATE', 0.01)
            return random.random() < float(sample_rate)

        return False

    def _validate_cache_data(self, cache_key, cached_data, route_handler_func, validated_data,
                            schema=None, many=False, metrics_enabled=True, app=None):
        """
        Validate cached data against fresh DB query.

        This method:
        1. Calls the route handler function to get fresh data
        2. Serializes fresh data using the same schema as the route
        3. Compares cached vs fresh data
        4. Records metrics and sends alerts if mismatch

        Args:
            cache_key: The cache key
            cached_data: Data from cache (already serialized)
            route_handler_func: The route handler function (calls business logic)
            validated_data: Request parameters
            schema: Marshmallow schema class for serialization
            many: Boolean flag for list serialization
            metrics_enabled: Whether to record validation metrics (default: True)
            app: Flask app instance for context (required when running in background thread)

        Note: This is called asynchronously in a background thread to prevent blocking the request.
        """
        try:
            # Fetch fresh data by calling the SAME route handler function
            # This automatically calls the business logic execute() function
            # Note: We're already inside app.app_context() from the caller
            fresh_data = route_handler_func(validated_data=validated_data)

            # Serialize fresh data using the same logic as the route decorator
            if schema:
                from wedeliver_core_plus.app_decorators.serializer import _serialize_result
                fresh_data = _serialize_result(fresh_data, schema, many)

            # Compare data
            matched = self._data_matches(cached_data, fresh_data)

            # Record metrics (use parameter instead of current_app.config)
            if metrics_enabled:
                metrics = self._get_validation_metrics()
                metrics.record_validation(
                    matched=matched,
                    details={
                        'api_path': self.path,
                        'params': validated_data,
                        'cache_key': cache_key,
                        'timestamp': datetime.now().isoformat(),
                        'cached_data_preview': str(cached_data)[:200],  # First 200 chars
                        'fresh_data_preview': str(fresh_data)[:200]
                    } if not matched else None
                )

            if not matched:
                cache_warning(f"⚠️ MISMATCH detected for {self.path} with params {validated_data}")

                # Auto-invalidate stale cache to ensure next request gets fresh data
                try:
                    # 1. Delete the main cache key
                    if self.cache and cache_key:
                        self.cache.delete(cache_key)
                        cache_info(f"🗑️ Auto-deleted stale cache key: {cache_key}")

                    # 2. Delete related function cache keys
                    self._invalidate_function_cache(validated_data)
                    cache_info(f"🗑️ Auto-deleted related function cache for params: {validated_data}")
                except Exception as e:
                    cache_warning(f"Failed to auto-invalidate stale cache: {e}")

        except Exception as e:
            cache_warning(f"Error during validation: {e}")
            # Don't fail the request if validation fails

    def _data_matches(self, cached_data, fresh_data):
        """
        Compare cached vs fresh data using JSON serialization.

        Args:
            cached_data: Data from cache
            fresh_data: Fresh data from database

        Returns:
            bool: True if data matches, False otherwise
        """
        try:
            # Serialize both to JSON for deep comparison
            cached_json = json.dumps(cached_data, sort_keys=True, default=str)
            fresh_json = json.dumps(fresh_data, sort_keys=True, default=str)

            return cached_json == fresh_json

        except Exception as e:
            cache_warning(f"Error comparing data: {e}")
            return True  # Assume match on error to avoid false alerts

    # ---------------- Cache Flush Methods ----------------

    @classmethod
    def flush_all_cache(cls):
        """
        Flush all cache entries for the current service.

        This is a CLASS METHOD that can be called without instantiating the cache rule.
        Useful for clearing all cache on application startup to prevent stale data issues
        after deployments.

        Uses SCAN pattern to only delete keys prefixed with the service name.
        This allows multiple services to share the same Redis instance safely.
        Respects ENABLE_REDIS flag - only flushes if Redis is enabled.

        Returns:
            bool: True if flush succeeded, False if Redis is disabled or flush failed

        Example:
            # In app initialization
            from wedeliver_core_plus import BaseCacheRule
            BaseCacheRule.flush_all_cache()
        """
        from flask import current_app

        try:
            app = current_app

            # Check if Redis is enabled via CACHE_ENABLE flag
            enable_redis = app.config.get("CACHE_ENABLE", False)

            if not enable_redis:
                cache_info("Redis is disabled via ENABLE_REDIS flag, skipping cache flush")
                return False

            # Initialize service name if not set
            if cls._service_name is None:
                cls._service_name = app.config.get("SERVICE_NAME", "default-service")

            # Use singleton client if exists, otherwise create it
            if cls._redis_client is None:
                # Create singleton client using existing method
                temp_instance = cls.__new__(cls)  # Create instance without calling __init__
                cls._redis_client = temp_instance._create_redis_client()

            # If client creation failed, return False
            if cls._redis_client is None:
                cache_warning("Redis client unavailable, skipping cache flush")
                return False

            # Scan and delete only keys for this service
            pattern = f"{cls._service_name}:*"
            deleted = 0

            for key in cls._redis_client.scan_iter(pattern):
                cls._redis_client.delete(key)
                deleted += 1

            cache_info(f"Successfully flushed {deleted} cache entries for service '{cls._service_name}'")
            return True

        except redis_exceptions.RedisError as e:
            cache_error(f"Failed to flush cache: {e}")
            return False
        except Exception as e:
            cache_error(f"Unexpected error during cache flush: {e}")
            return False

    @classmethod
    def flush_service_cache(cls, service_name=None):
        """
        Flush all cache entries for a specific service.

        This is a CLASS METHOD that can be called to clear cache for any service.
        Useful for cross-service cache management or administrative operations.

        Args:
            service_name: Service name to flush. If None, uses current service from config.

        Returns:
            int: Number of keys deleted, or -1 if operation failed

        Example:
            # Flush cache for a specific service
            from wedeliver_core_plus import BaseCacheRule
            deleted = BaseCacheRule.flush_service_cache("thrivve-service")
            print(f"Deleted {deleted} keys")
        """
        from flask import current_app

        try:
            app = current_app

            # Check if Redis is enabled via CACHE_ENABLE flag
            enable_redis = app.config.get("CACHE_ENABLE", False)

            if not enable_redis:
                cache_info("Redis is disabled via ENABLE_REDIS flag, skipping cache flush")
                return -1

            # Use provided service name or get from config
            target_service = service_name
            if target_service is None:
                target_service = app.config.get("SERVICE_NAME", "default-service")

            # Use singleton client if exists, otherwise create it
            if cls._redis_client is None:
                # Create singleton client using existing method
                temp_instance = cls.__new__(cls)  # Create instance without calling __init__
                cls._redis_client = temp_instance._create_redis_client()

            # If client creation failed, return -1
            if cls._redis_client is None:
                cache_warning("Redis client unavailable, skipping cache flush")
                return -1

            # Scan and delete only keys for the target service
            pattern = f"{target_service}:*"
            deleted = 0

            for key in cls._redis_client.scan_iter(pattern):
                cls._redis_client.delete(key)
                deleted += 1

            cache_info(f"Flushed {deleted} cache entries for service '{target_service}'")
            return deleted

        except redis_exceptions.RedisError as e:
            cache_error(f"Failed to flush cache for service '{target_service}': {e}")
            return -1
        except Exception as e:
            cache_error(f"Unexpected error during cache flush: {e}")
            return -1
