"""
Unified cache invalidation registry.

This module handles registration and execution of both local and cross-service cache invalidation.
It provides a unified registry and handler for all cache invalidation events.
"""

import json
import os

from sqlalchemy import event, inspect
from concurrent.futures import ThreadPoolExecutor
from wedeliver_core_plus.helpers.caching.cache_logger import (
    cache_debug, cache_info, cache_warning, cache_error
)

# ============================================================================
# POOL TYPE CONFIGURATION
# ============================================================================

def _should_use_gevent_pool():
    """
    Determine if gevent Pool should be used based on global configuration.

    Returns:
        bool: True if gevent Pool should be used, False for ThreadPoolExecutor
    """
    # Check environment variable
    use_gevent = os.getenv('CACHE_USE_GEVENT_POOL', 'False').lower() == 'true'

    if not use_gevent:
        return False

    # Verify gevent is available
    try:
        from gevent.pool import Pool as GeventPool
        return True
    except ImportError:
        cache_warning("CACHE_USE_GEVENT_POOL=true but gevent not available, falling back to ThreadPoolExecutor")
        return False


# ============================================================================
# GLOBAL CACHE ENABLE CHECK
# ============================================================================

def is_cache_enabled():
    """
    Check if cache system is enabled globally.

    This is the single source of truth for cache enabled/disabled state.
    When ENABLE_REDIS=False, all cache operations are skipped for zero overhead.

    Returns:
        bool: True if CACHE_ENABLE=True, False otherwise
    """
    try:
        from flask import current_app
        return current_app.config.get("CACHE_ENABLE", False)
    except RuntimeError:
        # Outside app context (e.g., during imports)
        return False


# ============================================================================
# UNIFIED REGISTRY - Handles both local and cross-service invalidation
# ============================================================================

# Unified registry structure (simplified):
# {
#     model_class: [
#         {
#             "cache_rule": cache_rule_instance,
#             "path": "/core/api/v1/mobile/home/messages",
#             "scoped_cache_keys": {...},
#             "conditions": {
#                 "events": ["after_update"],
#                 "filters": [("id", "=", "customer_id")],
#             }
#         },
#         # ... more rules for this model
#     ]
# }
_unified_registry = {}
_listeners_registered = set()  # {(model_class, tuple(events))}

# Global thread pool for event listeners
# Handles async processing of cache invalidation events
# Prevents blocking database transactions
_event_pool = None
_event_pool_initialized = False





# ============================================================================
# INITIALIZATION FUNCTION
# ============================================================================

def initialize_cache_system(app):
    """
    Initialize the unified cache invalidation system on app startup.

    This function:
    1. Checks if cache is enabled (ENABLE_REDIS flag)
    2. Initializes the unified registry
    3. Eagerly initializes ModelDiscovery (scans all models at startup)
    4. Verifies worker cache resources (for multi-worker environments)
    5. Flushes all cache (optional, AFTER verification to keep Redis client lazy)

    Args:
        app: Flask application instance

    Returns:
        bool: True if initialization successful, False if disabled or failed
    """
    try:
        with app.app_context():
            # Check if cache is enabled
            if not is_cache_enabled():
                app.logger.info("[Cache] Cache system disabled (ENABLE_REDIS=False)")
                return False

            # Initialize unified registry (empty, will be populated lazily)
            global _unified_registry, _listeners_registered
            _unified_registry = {}
            _listeners_registered = set()

            # Eagerly initialize ModelDiscovery
            from wedeliver_core_plus.helpers.model_discovery import ModelDiscovery
            discovery = ModelDiscovery()  # Scans app/models directory NOW
            model_count = len(discovery.list_models())
            app.logger.info(f"[Cache] ModelDiscovery initialized: {model_count} models discovered")

            app.logger.info("[Cache] Unified cache system initialized")

            # Verify worker cache resources (for Gunicorn multi-worker environments)
            # This runs BEFORE cache flush to ensure Redis client is still None
            _verify_worker_cache_resources(app)

            # Flush all cache on startup (optional)
            # This happens AFTER verification to keep Redis client lazy
            flush_on_startup = app.config.get('CACHE_FLUSH_ON_STARTUP', True)
            if flush_on_startup:
                from wedeliver_core_plus import BaseCacheRule
                success = BaseCacheRule.flush_all_cache()
                if success:
                    app.logger.info("[Cache] All cache cleared on startup")

            # ✅ NEW: Start Pub/Sub subscriber for cache registration
            pubsub_enabled = app.config.get('CACHE_REGISTRATION_PUBSUB_ENABLED', True)
            if pubsub_enabled:
                try:
                    from wedeliver_core_plus.helpers.caching.valkey_pubsub import ValkeyRegistrationSubscriber

                    subscriber = ValkeyRegistrationSubscriber.get_instance()
                    subscriber.start(app)  # Pass app instance for application context

                    app.logger.info(f"[Cache] Pub/Sub registration subscriber started in worker {os.getpid()}")
                except Exception as e:
                    app.logger.error(f"[Cache] Failed to start Pub/Sub subscriber: {e}")

            return True

    except Exception as e:
        app.logger.error(f"[Cache] Error during cache system initialization: {e}")
        return False


def _verify_worker_cache_resources(app):
    """
    Verify cache resources are properly initialized for this worker process.

    This function runs automatically at the end of initialize_cache_system() in each worker.
    It ensures that each worker has its own Redis connection, event pools, and registries.

    This is necessary for multi-worker environments (Gunicorn) because:
    1. Gunicorn's post_fork hook runs BEFORE Flask app is loaded
    2. We need Flask app context to properly verify cache resources
    3. Each worker needs its own Redis connection (not shared socket)

    The post_fork hook (in gunicorn_config.py) resets module-level state.
    This function verifies that reset was successful and logs the status.

    Args:
        app: Flask application instance
    """
    import os

    # Get worker PID for logging
    worker_pid = os.getpid()

    try:
        app.logger.info(f"[Worker {worker_pid}] Verifying worker cache resources...")

        # Import cache modules
        from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule

        # 1. Verify Redis connection is fresh (not inherited)
        if BaseCacheRule._redis_client is None:
            app.logger.info(f"[Worker {worker_pid}] ✓ Redis client clean (will initialize on first use)")
        else:
            # This shouldn't happen if post_fork worked correctly
            app.logger.warning(f"[Worker {worker_pid}] ⚠ Redis client already exists (may be inherited from master)")

        # 2. Verify event pool is fresh
        if _event_pool is None:
            app.logger.info(f"[Worker {worker_pid}] ✓ Event pool clean (will initialize on first use)")
        else:
            app.logger.warning(f"[Worker {worker_pid}] ⚠ Event pool already exists (may be inherited from master)")

        # 3. Verify registries are empty (will be populated on first cache rule access)
        if len(_unified_registry) == 0:
            app.logger.info(f"[Worker {worker_pid}] ✓ Cache registries clean (will populate on first use)")
        else:
            app.logger.info(f"[Worker {worker_pid}] ℹ Cache registries already populated with {len(_unified_registry)} models")

        app.logger.info(f"[Worker {worker_pid}] ✓ Worker cache verification complete")

    except Exception as e:
        app.logger.error(f"[Worker {worker_pid}] ✗ Worker cache verification failed: {e}")
        import traceback
        app.logger.error(traceback.format_exc())


# ============================================================================
# EVENT LISTENER THREAD POOL
# ============================================================================

def _get_event_pool():
    """
    Get or create the event listener pool.

    This pool handles async processing of cache invalidation events
    to prevent blocking database transactions.

    Uses gevent Pool or ThreadPoolExecutor based on CACHE_USE_GEVENT_POOL config.

    Returns:
        GeventPool or ThreadPoolExecutor: Pool for event listeners
    """
    global _event_pool, _event_pool_initialized

    if not _event_pool_initialized:
        # Get pool size from config
        try:
            from flask import current_app
            pool_size = current_app.config.get('CACHE_INVALIDATION_POOL_SIZE', 20)
        except:
            pool_size = int(os.getenv('CACHE_INVALIDATION_POOL_SIZE', '20'))

        # Determine pool type based on configuration
        if _should_use_gevent_pool():
            from gevent.pool import Pool as GeventPool
            _event_pool = GeventPool(size=pool_size)
            _event_pool_initialized = True
            cache_debug(f"Initialized gevent invalidation pool with {pool_size} greenlets")
        else:
            # Use ThreadPoolExecutor
            _event_pool = ThreadPoolExecutor(
                max_workers=pool_size,
                thread_name_prefix="cache-invalidation"
            )
            _event_pool_initialized = True
            cache_debug(f"Initialized ThreadPoolExecutor invalidation pool with {pool_size} workers")

    return _event_pool


# ============================================================================
# UNIFIED REGISTRATION FUNCTIONS
# ============================================================================
# Note: Model registration is now handled via Pub/Sub in valkey_pubsub.py
# Cache rules publish to Pub/Sub, and all workers receive and register locally


def _register_model_in_worker(model_class, path, scoped_cache_keys, conditions, cache_rule_instance=None):
    """
    Register model invalidation config in worker's local memory.

    Uses simplified unified registry structure (no local/cross-service distinction).
    """
    if model_class not in _unified_registry:
        _unified_registry[model_class] = []

    # Check for duplicates (same path)
    existing_paths = [rule["path"] for rule in _unified_registry[model_class]]
    if path in existing_paths:
        cache_debug(f"Rule already registered: {path} → {model_class.__name__}")
        return

    # Add to registry
    _unified_registry[model_class].append({
        "cache_rule": cache_rule_instance,
        "path": path,
        "scoped_cache_keys": scoped_cache_keys,
        "conditions": conditions
    })

    cache_debug(f"Registered rule: {path} → {model_class.__name__}")


def _register_sqlalchemy_listener(model_class, events):
    """Register SQLAlchemy event listener (once per model+events)."""
    registry_key = (model_class, tuple(events))

    if registry_key not in _listeners_registered:
        for ev in events:
            event.listen(model_class, ev, unified_invalidation_handler)

        _listeners_registered.add(registry_key)
        cache_debug(f"Registered SQLAlchemy listener: {model_class.__name__} → {events}")


# ============================================================================
# UNIFIED INVALIDATION HANDLER
# ============================================================================

def _extract_model_snapshot(target, model_class):
    """
    Extract all attributes needed for cache invalidation from the model instance.

    This MUST be called while the session is still active (synchronously in the event handler).
    Returns a dictionary with all attribute values needed for filter evaluation.

    This prevents "Instance is not bound to a Session" errors when the background thread
    tries to access model attributes after the session has been closed.

    Args:
        target: SQLAlchemy model instance (still bound to session)
        model_class: Model class

    Returns:
        dict: Snapshot of model attributes
            {
                '__class__': model_class,
                '__class_name__': 'PushNotificationLog',
                'id': 123,
                'customer_id': 456,
                'notification_type': 'push',
                ...
            }
    """
    snapshot = {
        '__class__': model_class,
        '__class_name__': model_class.__name__
    }

    # Get all fields that might be used in invalidation conditions
    registry = _unified_registry[model_class]

    # Collect all fields referenced in filters
    fields_to_extract = set()

    # Iterate through all rules (simplified unified structure)
    for rule_config in registry:
        conditions = rule_config["conditions"]

        # Extract fields from filters
        for filter_tuple in conditions.get("filters", []):
            field = filter_tuple[0]
            fields_to_extract.add(field)

        # Extract fields from or_filters
        for filter_tuple in conditions.get("or_filters", []):
            field = filter_tuple[0]
            fields_to_extract.add(field)

    # Extract attribute values while session is active
    for field in fields_to_extract:
        if hasattr(target, field):
            try:
                # Access attribute while session is active
                snapshot[field] = getattr(target, field)
            except Exception as e:
                cache_warning(f"Failed to extract field '{field}' from {model_class.__name__}: {e}")
                snapshot[field] = None

    cache_debug(f"Extracted snapshot for {model_class.__name__} with fields: {list(fields_to_extract)}")

    return snapshot


def unified_invalidation_handler(mapper, connection, target):
    """
    Unified handler for both local and cross-service cache invalidation.

    This handler is called by SQLAlchemy events but immediately submits
    work to a background thread pool to avoid blocking the database transaction.

    Flow:
        1. SQLAlchemy event fires (after_update, after_insert, etc.)
        2. This handler is called synchronously
        3. Extract model attributes while session is active (snapshot)
        4. Work is submitted to thread pool with snapshot (returns immediately)
        5. Database transaction continues without blocking
        6. Background thread processes invalidation asynchronously using snapshot

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Model instance that triggered the event
    """
    # Check if cache is enabled - skip if disabled
    if not is_cache_enabled():
        return

    model_class = target.__class__

    if model_class not in _unified_registry:
        # ⚠️ ADD THIS WARNING
        cache_warning(
            f"⚠️ CACHE INVALIDATION SKIPPED: Model {model_class.__name__} updated "
            f"but NO cache rules registered in worker {os.getpid()}! "
            f"This may cause stale cache. Consider eager registration."
        )
        return  # No rules registered for this model

    # Extract model attributes NOW while session is still active
    # This prevents "Instance is not bound to a Session" errors in background thread
    target_snapshot = _extract_model_snapshot(target, model_class)

    # Submit to pool for async processing (non-blocking)
    # This returns immediately - database transaction continues
    pool = _get_event_pool()

    # Use spawn() for gevent Pool, submit() for ThreadPoolExecutor
    if hasattr(pool, 'spawn'):
        # gevent Pool
        pool.spawn(_async_invalidation_worker, model_class, target_snapshot)
    else:
        # ThreadPoolExecutor
        pool.submit(_async_invalidation_worker, model_class, target_snapshot)


def _async_invalidation_worker(model_class, target_snapshot):
    """
    Background worker that processes cache invalidation asynchronously.

    This runs in a background thread from the event pool.
    All exceptions are caught to prevent affecting the database transaction.

    Args:
        model_class: Model class that triggered the event
        target_snapshot: Dictionary snapshot of model attributes (not live instance)
            This prevents "Instance is not bound to a Session" errors since the
            session may be closed by the time this worker executes.
    """
    try:
        registry = _unified_registry[model_class]

        # Handle all cache rules (simplified unified structure)
        for rule_config in registry:
            try:
                _handle_invalidation(rule_config, target_snapshot)
            except Exception as e:
                # Catch exceptions per cache rule to continue processing other rules
                path = rule_config.get("path", "unknown")
                cache_error(f"Invalidation failed for {path}: {e}")

    except Exception as e:
        # Catch all exceptions to prevent affecting DB transaction
        cache_error(f"Invalidation worker failed for {model_class.__name__}: {e}")


def _handle_invalidation(rule_config, target_snapshot):
    """
    Handle invalidation for a cache rule (unified for all models).

    Args:
        rule_config: Rule configuration dict from unified registry:
            {
                "cache_rule": cache_rule_instance or None,
                "path": "/core/api/v1/mobile/home/messages",
                "scoped_cache_keys": {...},
                "conditions": {...}
            }
        target_snapshot: Dictionary snapshot of model attributes
    """
    model_name = target_snapshot['__class_name__']

    # Extract config
    path = rule_config["path"]
    scoped_cache_keys = rule_config["scoped_cache_keys"]
    conditions = rule_config["conditions"]
    cache_rule_instance = rule_config.get("cache_rule")

    # Get service name
    try:
        service_name = os.environ.get("SERVICE_NAME", "default-service")
    except RuntimeError:
        service_name = "default-service"

    cache_debug(f"Evaluating invalidation for {path} triggered by {model_name}")

    # Evaluate conditions
    result = evaluate_invalidation_conditions(
        target_snapshot,
        conditions,
        scoped_cache_keys,
        service_name=service_name,
        api_path=path
    )

    if result is None:
        return  # Conditions not met

    # Invalidate cache
    if result.get("__invalidate_all__"):
        cache_debug(f"Invalidating all cache for {path} (scope: *)")

        # Use cache rule instance if available, otherwise use helper
        if cache_rule_instance:
            cache_rule_instance.invalidate_by_path()
        else:
            _invalidate_by_path(service_name, path)
    else:
        main_keys = result.get("main_cache_keys", [])
        func_keys = result.get("function_cache_keys", [])

        if main_keys or func_keys:
            all_keys = main_keys + func_keys
            cache_debug(f"Invalidating {len(main_keys)} main + {len(func_keys)} function cache keys")

            # Use cache rule instance if available, otherwise use helper
            if cache_rule_instance:
                cache_rule_instance._invalidate_async(all_keys)
            else:
                _batch_delete_keys(all_keys)


def _invalidate_by_path(service_name, path):
    """
    Invalidate all cache for a specific path (works without cache rule instance).

    This is used when invalidating from config dict (Pub/Sub registration).

    Args:
        service_name: Service name (e.g., "thrivve-service")
        path: API path (e.g., "/core/api/v1/mobile/home/messages")
    """
    from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule

    # Ensure Redis client is initialized (same pattern as flush_all_cache)
    if BaseCacheRule._redis_client is None:
        temp_instance = BaseCacheRule.__new__(BaseCacheRule)
        BaseCacheRule._redis_client = temp_instance._create_redis_client()

    # Check if client is available
    if BaseCacheRule._redis_client is None:
        cache_warning("[Cache] Redis client not available for invalidation")
        return

    redis_client = BaseCacheRule._redis_client

    pattern = f"{service_name}:{path}:*"
    cache_debug(f"[Cache] Invalidating cache by pattern: {pattern}")

    # Delete all keys matching pattern individually (Redis Cluster compatible)
    deleted_count = 0
    failed_count = 0

    for key in redis_client.scan_iter(match=pattern):
        try:
            result = redis_client.delete(key)
            if result > 0:
                deleted_count += 1
        except Exception as e:
            failed_count += 1
            cache_warning(f"[Cache] Failed to delete key {key}: {e}")

    if deleted_count > 0:
        cache_debug(f"[Cache] Deleted {deleted_count} cache keys")

    if failed_count > 0:
        cache_warning(f"[Cache] Failed to delete {failed_count} cache keys")


def _batch_delete_keys(cache_keys):
    """
    Delete cache keys individually (Redis Cluster compatible).

    This is used when invalidating from config dict (Pub/Sub registration).

    Note: Uses individual deletes instead of pipeline to avoid CROSSSLOT errors
    in Redis Cluster/Serverless environments where keys may hash to different slots.

    Args:
        cache_keys: List of cache keys to delete
    """
    from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule

    # Ensure Redis client is initialized (same pattern as flush_all_cache)
    if BaseCacheRule._redis_client is None:
        temp_instance = BaseCacheRule.__new__(BaseCacheRule)
        BaseCacheRule._redis_client = temp_instance._create_redis_client()

    # Check if client is available
    if BaseCacheRule._redis_client is None:
        cache_warning("[Cache] Redis client not available for invalidation")
        return

    redis_client = BaseCacheRule._redis_client

    # Delete keys individually to avoid CROSSSLOT errors in Redis Cluster
    deleted_count = 0
    failed_count = 0

    for key in cache_keys:
        try:
            result = redis_client.delete(key)
            if result > 0:
                deleted_count += 1
        except Exception as e:
            failed_count += 1
            cache_warning(f"[Cache] Failed to delete key {key}: {e}")

    if deleted_count > 0:
        cache_debug(f"[Cache] Successfully deleted {deleted_count}/{len(cache_keys)} cache keys")

    if failed_count > 0:
        cache_warning(f"[Cache] Failed to delete {failed_count}/{len(cache_keys)} cache keys")





def _extract_scoped_key_values_from_redis(service_name, api_path, scoped_key):
    """
    Scan Redis cache keys and extract all values for a specific scoped key along with their cache keys.

    Args:
        service_name: Service name (e.g., "thrivve-service")
        api_path: API path (e.g., "/core/api/v1/mobile/home/messages")
        scoped_key: The scoped key to extract (e.g., "customer_id")

    Returns:
        list: List of (value, cache_key) tuples

    Example:
        Redis keys:
            thrivve-service/core/api/v1/mobile/home/messages:customer_id=123:app_version=app_version:hash1
            thrivve-service/core/api/v1/mobile/home/messages:customer_id=456:app_version=app_version:hash2

        _extract_scoped_key_values_from_redis("thrivve-service", "/core/api/v1/mobile/home/messages", "customer_id")
        → [(123, "thrivve-service/core/.../messages:customer_id=123:..."),
            (456, "thrivve-service/core/.../messages:customer_id=456:...")]
    """
    from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule
    import re

    if not BaseCacheRule._redis_client:
        cache_warning("Redis client not available for scanning keys")
        return []

    # Build pattern to match all cache keys for this endpoint
    pattern = f"{service_name}:{api_path}:*"

    results = []

    try:
        # Scan for all cache keys matching the pattern
        for key in BaseCacheRule._redis_client.scan_iter(match=pattern):
            try:
                # Decode key if it's bytes
                cache_key = key.decode('utf-8') if isinstance(key, bytes) else key

                # Parse the key to extract scoped key values
                # Format: service_name/path:key1=val1:key2=val2:hash
                # Extract the tags portion (between path and final hash)
                parts = cache_key.split(':')

                # Find the scoped key in the tags
                for part in parts:
                    if '=' in part and part.startswith(f"{scoped_key}="):
                        # Extract value after the equals sign
                        value_str = part.split('=', 1)[1]

                        # Try to parse the value (handle different types)
                        try:
                            # Try to parse as JSON (handles lists, numbers, etc.)
                            value = json.loads(value_str)
                        except (json.JSONDecodeError, ValueError):
                            # If not JSON, use as string
                            value = value_str

                        # Store (value, cache_key) tuple
                        results.append((value, cache_key))
                        break

            except Exception as e:
                cache_warning(f"Error parsing cache key {key}: {e}")
                continue

    except Exception as e:
        cache_warning(f"Error scanning Redis keys: {e}")

    cache_debug(f"Extracted {len(results)} cache keys for '{scoped_key}' from Redis")
    return results


def _apply_operator(actual_value, operator, expected_value, service_name=None, api_path=None, scoped_key=None):
    """
    Apply comparison operator between actual and expected values.

    Args:
        actual_value: Value from the model instance
        operator: Comparison operator (=, !=, in, >, <)
        expected_value: Expected value to compare against
        service_name: Service name (for Redis-aware operators)
        api_path: API path (for Redis-aware operators)
        scoped_key: Scoped key name (for Redis-aware operators)

    Returns:
        tuple: (bool, list) - (condition_passed, matching_cache_keys)
            - condition_passed: True if condition passes, False otherwise
            - matching_cache_keys: List of cache keys that match (for Redis-aware operators)

    Examples:
        _apply_operator("app_version", "=", "app_version") → (True, [])
        _apply_operator(123, "in", "customer_id", "thrivve-service", "/api/path", "customer_id")
        → (True, ["service/path:customer_id=123:...", ...])
    """
    matching_keys = []

    if operator == "=":
        # For equality with Redis context, find matching cache keys
        if service_name and api_path and scoped_key:
            cached_items = _extract_scoped_key_values_from_redis(service_name, api_path, scoped_key)
            for value, cache_key in cached_items:
                if value == actual_value:
                    matching_keys.append(cache_key)
            return (len(matching_keys) > 0, matching_keys)
        return (actual_value == expected_value, [])

    elif operator == "!=":
        return (actual_value != expected_value, [])

    elif operator == "in":
        # Special handling for 'in' operator
        if isinstance(expected_value, str) and service_name and api_path and scoped_key:
            # Redis-aware: scan cache keys and extract values
            cached_items = _extract_scoped_key_values_from_redis(service_name, api_path, scoped_key)

            # Check if actual_value is in any of the cached values
            # Handle both scalar values and list values (flatten lists)
            for value, cache_key in cached_items:
                if isinstance(value, list):
                    # Flatten list and check membership
                    if actual_value in value:
                        matching_keys.append(cache_key)
                else:
                    # Direct comparison
                    if actual_value == value:
                        matching_keys.append(cache_key)

            passed = len(matching_keys) > 0
            cache_debug(f"'in' operator: found {len(matching_keys)} matching cache keys")
            return (passed, matching_keys)

        elif isinstance(expected_value, (list, tuple, set)):
            # Traditional list check (no cache keys)
            return (actual_value in expected_value, [])
        else:
            cache_warning(f"'in' operator requires list or Redis context. Got: {type(expected_value)}")
            return (False, [])

    elif operator == ">":
        return (actual_value > expected_value, [])
    elif operator == "<":
        return (actual_value < expected_value, [])
    else:
        cache_warning(f"Unknown operator: {operator}")
        return (False, [])


def _resolve_scoped_value(scoped_key, scoped_cache_keys, api_params=None):
    """
    Resolve a scoped key to its actual value.

    Args:
        scoped_key: Key from filter (e.g., "customer_id", "app_version")
        scoped_cache_keys: Dict defining cache key structure
        api_params: Optional dict of API parameters (for runtime resolution)

    Returns:
        Resolved value or the scoped_key itself if not found

    Examples:
        scoped_cache_keys = {
            "customer_id": "api_params",
            "app_version": "__static_value__('app_version')"
        }

        _resolve_scoped_value("app_version", scoped_cache_keys) → "app_version"
        _resolve_scoped_value("customer_id", scoped_cache_keys, {"customer_id": 123}) → 123
    """
    import re

    if scoped_key not in scoped_cache_keys:
        # Not in scoped keys, return as-is (might be a literal value)
        return scoped_key

    scoped_value = scoped_cache_keys[scoped_key]

    # Handle static value pattern
    if isinstance(scoped_value, str) and scoped_value.startswith("__static_value__"):
        match = re.match(r"__static_value__\(['\"](.+?)['\"]\)", scoped_value)
        if match:
            return match.group(1)

    # Handle api_params
    if scoped_value == "api_params" and api_params:
        return api_params.get(scoped_key)

    # Handle function call (return the scoped_key for now, will be resolved later)
    if isinstance(scoped_value, str) and "__function_call__" in scoped_value:
        return scoped_key  # Will be resolved during cache key generation

    return scoped_value


def _evaluate_filter(target_snapshot, filter_tuple, scoped_cache_keys, api_params=None, service_name=None, api_path=None):
    """
    Evaluate a single filter condition using snapshot dictionary.

    Args:
        target_snapshot: Dictionary snapshot of model attributes
        filter_tuple: Tuple of (field, operator, scoped_key)
        scoped_cache_keys: Dict defining cache key structure
        api_params: Optional dict of API parameters
        service_name: Service name (for Redis-aware operators)
        api_path: API path (for Redis-aware operators)

    Returns:
        tuple: (bool, list) - (filter_passed, matching_cache_keys)

    Examples:
        filter_tuple = ("group_type", "=", "app_version")
        scoped_cache_keys = {"app_version": "__static_value__('app_version')"}
        target_snapshot = {"group_type": "app_version", "__class_name__": "MyModel"}
        → Returns (True, ["service/path:app_version=app_version:..."])
    """
    field, operator, scoped_key = filter_tuple

    # Get actual value from snapshot (not live instance)
    if field not in target_snapshot:
        cache_warning(
            f"Filter field '{field}' not found in snapshot for "
            f"{target_snapshot.get('__class_name__', 'Unknown')}. Filter fails."
        )
        return (False, [])

    actual_value = target_snapshot[field]

    # Resolve expected value from scoped_cache_keys
    expected_value = _resolve_scoped_value(scoped_key, scoped_cache_keys, api_params)

    # Apply operator (pass Redis context)
    passed, matching_keys = _apply_operator(
        actual_value,
        operator,
        expected_value,
        service_name=service_name,
        api_path=api_path,
        scoped_key=scoped_key
    )

    if passed:
        cache_debug(
            f"Filter passed for {target_snapshot.get('__class_name__', 'Unknown')}: "
            f"{field} {operator} {expected_value} (actual: {actual_value}), "
            f"matched {len(matching_keys)} cache keys"
        )
    else:
        cache_debug(
            f"Filter failed for {target_snapshot.get('__class_name__', 'Unknown')}: "
            f"{field} {operator} {expected_value} (actual: {actual_value})"
        )

    return (passed, matching_keys)


def _evaluate_filters_and(target_snapshot, filters, scoped_cache_keys, api_params=None, service_name=None, api_path=None):
    """
    Evaluate multiple filters with AND logic (all must pass).

    Args:
        target_snapshot: Dictionary snapshot of model attributes
        filters: List of filter tuples [(field, operator, scoped_key), ...]
        scoped_cache_keys: Dict defining cache key structure
        api_params: Optional dict of API parameters
        service_name: Service name (for Redis-aware operators)
        api_path: API path (for Redis-aware operators)

    Returns:
        tuple: (bool, list) - (all_passed, matching_cache_keys)
            Returns intersection of cache keys (keys that match ALL filters)

    Examples:
        filters = [
            ("group_type", "=", "app_version"),
            ("status", "=", "active")
        ]
        → Returns (True, [matching_keys]) only if both conditions are met
    """
    if not filters:
        return (True, [])  # No filters means pass

    all_matching_keys = None  # Will hold intersection of keys

    for filter_tuple in filters:
        passed, matching_keys = _evaluate_filter(target_snapshot, filter_tuple, scoped_cache_keys, api_params, service_name, api_path)

        if not passed:
            return (False, [])  # One filter failed, AND logic fails

        # Collect intersection of matching keys
        if all_matching_keys is None:
            all_matching_keys = set(matching_keys)
        else:
            all_matching_keys = all_matching_keys.intersection(set(matching_keys))

    return (True, list(all_matching_keys) if all_matching_keys else [])


def _evaluate_filters_or(target_snapshot, or_filters, scoped_cache_keys, api_params=None, service_name=None, api_path=None):
    """
    Evaluate multiple filters with OR logic (at least one must pass).

    Args:
        target_snapshot: Dictionary snapshot of model attributes
        or_filters: List of filter tuples [(field, operator, scoped_key), ...]
        scoped_cache_keys: Dict defining cache key structure
        api_params: Optional dict of API parameters
        service_name: Service name (for Redis-aware operators)
        api_path: API path (for Redis-aware operators)

    Returns:
        tuple: (bool, list) - (any_passed, matching_cache_keys)
            Returns union of cache keys (keys that match ANY filter)

    Examples:
        or_filters = [
            ("status", "=", "active"),
            ("status", "=", "pending")
        ]
        → Returns (True, [matching_keys]) if status is either "active" or "pending"
    """
    if not or_filters:
        return (True, [])  # No filters means pass

    all_matching_keys = set()
    any_passed = False

    for filter_tuple in or_filters:
        passed, matching_keys = _evaluate_filter(target_snapshot, filter_tuple, scoped_cache_keys, api_params, service_name, api_path)

        if passed:
            any_passed = True
            all_matching_keys.update(matching_keys)

    return (any_passed, list(all_matching_keys))


def evaluate_invalidation_conditions(target_snapshot, conditions, scoped_cache_keys, api_params=None, service_name=None, api_path=None):
    """
    Evaluate invalidation conditions and return actual cache keys to invalidate.

    This is the main function used by both local and cross-service invalidation.

    Args:
        target_snapshot: Dictionary snapshot of model attributes (not live instance)
            This prevents "Instance is not bound to a Session" errors.
        conditions: Dict with filter configuration
            {
                "filters": [(field, operator, scoped_key), ...],  # AND logic
                "or_filters": [(field, operator, scoped_key), ...],  # OR logic
                "invalidate_scope": "*" or None  # "*" = invalidate all (path-based)
            }
        scoped_cache_keys: Dict defining cache key structure
            {
                "customer_id": "api_params",
                "app_version": "__static_value__('app_version')",
                "contract_ids": "__function_call__(get_contract_ids, [customer_id:scoped_key])"
            }
        api_params: Optional dict of API parameters (for runtime resolution)
        service_name: Service name (for Redis scanning)
        api_path: API path (for Redis scanning)

    Returns:
        dict: {"main_cache_keys": [...], "function_cache_keys": [...]}
        dict: {"__invalidate_all__": True} if invalidate_scope = "*"
        None: If conditions not met (skip invalidation)

    Examples:
        # Returns actual cache keys to invalidate
        conditions = {"filters": [("id", "=", "customer_id")]}
        → Returns {
            "main_cache_keys": ["service/path:customer_id=123:..."],
            "function_cache_keys": ["service:function_cache:get_contract_ids:customer_id=123"]
        }

        # Invalidate all (path-based)
        conditions = {"invalidate_scope": "*"}
        → Returns {"__invalidate_all__": True}
    """
    import re

    # Step 1: Evaluate filters (AND logic)
    filters = conditions.get("filters", [])
    and_passed, and_matching_keys = _evaluate_filters_and(target_snapshot, filters, scoped_cache_keys, api_params, service_name, api_path)

    if not and_passed:
        cache_debug(f"AND filters failed for {target_snapshot['__class_name__']}, skipping invalidation")
        return None  # Conditions not met

    # Step 2: Evaluate or_filters (OR logic)
    or_filters = conditions.get("or_filters", [])
    or_matching_keys = []

    if or_filters:
        or_passed, or_matching_keys = _evaluate_filters_or(target_snapshot, or_filters, scoped_cache_keys, api_params, service_name, api_path)
        if not or_passed:
            cache_debug(f"OR filters failed for {target_snapshot['__class_name__']}, skipping invalidation")
            return None  # Conditions not met

    # Step 3: Check invalidate_scope
    invalidate_scope = conditions.get("invalidate_scope")
    if invalidate_scope == "*":
        cache_debug(f"Invalidate scope is '*', will invalidate all cache for path")
        return {"__invalidate_all__": True}

    # Step 4: Collect all matching cache keys
    # Combine AND and OR matching keys (intersection for AND, union for OR)
    if and_matching_keys and or_matching_keys:
        # Both AND and OR filters exist - take intersection
        main_cache_keys = list(set(and_matching_keys).intersection(set(or_matching_keys)))
    elif and_matching_keys:
        main_cache_keys = and_matching_keys
    elif or_matching_keys:
        main_cache_keys = or_matching_keys
    else:
        main_cache_keys = []

    # Step 5: Find related function cache keys
    # For each main cache key, extract scoped params and find matching function caches
    function_cache_keys = []

    if main_cache_keys and service_name:
        for cache_key in main_cache_keys:
            # Parse cache key to extract scoped params
            # Format: service_name/path:key1=val1:key2=val2:hash
            parts = cache_key.split(':')
            cache_params = {}

            for part in parts:
                if '=' in part:
                    key, value_str = part.split('=', 1)
                    try:
                        value = json.loads(value_str)
                    except (json.JSONDecodeError, ValueError):
                        value = value_str
                    cache_params[key] = value

            # Find function calls in scoped_cache_keys and build their cache keys
            for scoped_key, source in scoped_cache_keys.items():
                if isinstance(source, str) and "__function_call__" in source:
                    # Parse function call
                    match = re.match(r"__function_call__\((\w+),\s*\[([^\]]+)\]\)", source)
                    if match:
                        func_name = match.group(1)
                        param_specs = [p.strip() for p in match.group(2).split(",")]

                        # Extract only scoped params
                        func_params = {}
                        for param_spec in param_specs:
                            if ":scoped_key" in param_spec:
                                param_name = param_spec.replace(":scoped_key", "").strip()
                                if param_name in cache_params:
                                    func_params[param_name] = cache_params[param_name]

                        # Build function cache key
                        if func_params:
                            from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import format_value_for_cache_key
                            param_parts = []
                            for key, value in sorted(func_params.items()):
                                formatted_value = format_value_for_cache_key(value)
                                param_parts.append(f"{key}={formatted_value}")

                            param_str = ":".join(param_parts)
                            func_cache_key = f"{service_name}:function_cache:{func_name}:{param_str}"
                            function_cache_keys.append(func_cache_key)

    cache_debug(f"Found {len(main_cache_keys)} main cache keys and {len(function_cache_keys)} function cache keys to invalidate")

    return {
        "main_cache_keys": main_cache_keys,
        "function_cache_keys": function_cache_keys
    }


def _find_matching_function_cache_keys(func_name, target_field_value, service_name):
    """
    Find function cache keys where the cached result contains target_field_value.

    This function scans Redis for all function cache keys matching the pattern
    and checks if the cached result contains the target field value.

    Args:
        func_name: Function name (e.g., "get_contract_ids")
        target_field_value: Value to search for (e.g., 101)
        service_name: Service name for cache key prefix

    Returns:
        list: List of (cache_key, api_params_dict) tuples that match

    Example:
        func_name = "get_contract_ids"
        target_field_value = 101
        service_name = "thrivve-service"

        Scans: thrivve-service:function_cache:get_contract_ids:*
        Finds: thrivve-service:function_cache:get_contract_ids:customer_id=123
        Cached result: [101, 102, 103]
        Match: 101 in [101, 102, 103] ✓
        Returns: [("thrivve-service:function_cache:get_contract_ids:customer_id=123", {"customer_id": 123})]
    """
    from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule
    import json

    if not BaseCacheRule._redis_client:
        return []

    # Pattern: {service_name}:function_cache:{func_name}:*
    pattern = f"{service_name}:function_cache:{func_name}:*"

    matching_keys = []

    try:
        # Scan for all function cache keys
        for key in BaseCacheRule._redis_client.scan_iter(match=pattern):
            try:
                # Decode key if it's bytes
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                # Get cached result
                data = BaseCacheRule._redis_client.get(key)
                if not data:
                    continue

                # Decode data if it's bytes
                if isinstance(data, bytes):
                    data = data.decode('utf-8')

                result = json.loads(data)

                # Check if target_field_value is in result
                match_found = False
                if isinstance(result, list):
                    if target_field_value in result:
                        match_found = True
                else:
                    if target_field_value == result:
                        match_found = True

                if match_found:
                    # Extract api_params from key
                    api_params = _parse_api_params_from_cache_key(key, func_name, service_name)
                    matching_keys.append((key, api_params))
                    cache_debug(f"Found matching function cache: {key} with result containing {target_field_value}")

            except Exception as e:
                cache_warning(f"Error checking function cache key {key}: {e}")
                continue
    except Exception as e:
        cache_warning(f"Error scanning function cache keys: {e}")

    return matching_keys


def _parse_api_params_from_cache_key(cache_key, func_name, service_name):
    """
    Parse api_params from function cache key.

    Args:
        cache_key: Function cache key
        func_name: Function name
        service_name: Service name

    Returns:
        dict: Parsed api_params

    Example:
        Key: "thrivve-service:function_cache:get_contract_ids:customer_id=123:country=sa"
        Returns: {"customer_id": 123, "country": "sa"}
    """
    # Remove prefix: service:function_cache:func_name:
    prefix = f"{service_name}:function_cache:{func_name}:"
    if not cache_key.startswith(prefix):
        return {}

    params_str = cache_key[len(prefix):]

    # Parse param1=value1:param2=value2
    params = {}
    for part in params_str.split(":"):
        if "=" in part:
            key, value = part.split("=", 1)
            # Try to convert to int if possible
            try:
                params[key] = int(value)
            except ValueError:
                params[key] = value

    return params


def format_value_for_cache_key(value):
    """
    Format a value for use in cache keys.
    
    Shared utility for consistent value formatting across local and cross-service invalidation.
    
    Args:
        value: The value to format (int, str, bool, dict, list, etc.)
    
    Returns:
        str: Formatted value suitable for cache key
    """
    if isinstance(value, (int, str)):
        return str(value)
    else:
        return json.dumps(value)


def build_cache_key_pattern(service_name, api_path, invalidation_params):
    """
    Build a cache key pattern for invalidation.
    
    Shared utility to ensure consistent pattern building.
    
    Args:
        service_name: Service name (e.g., "thrivve-service")
        api_path: API path (e.g., "/finance/api/v1/me/balance")
        invalidation_params: Parameters for granular invalidation (e.g., {"customer_id": 123})
    
    Returns:
        str: Cache key pattern for Redis SCAN
    
    Examples:
        build_cache_key_pattern("thrivve-service", "/api/balance", {"customer_id": 123})
        Returns: "thrivve-service:/api/balance:customer_id=123:*"
        
        build_cache_key_pattern("thrivve-service", "/api/balance", {})
        Returns: "thrivve-service:/api/balance:*"
    """
    if invalidation_params:
        tags = []
        for api_param, value in invalidation_params.items():
            formatted_value = format_value_for_cache_key(value)
            tags.append(f"{api_param}={formatted_value}")
        
        tag_str = ":".join(tags)
        return f"{service_name}:{api_path}:{tag_str}:*"
    else:
        # Path-based invalidation (all keys for this endpoint)
        return f"{service_name}:{api_path}:*"


def invalidate_cache_by_pattern(redis_client, pattern):
    """
    Invalidate cache entries matching a pattern.
    
    Shared utility for cache invalidation via Redis SCAN.
    
    Args:
        redis_client: Redis/Valkey client instance
        pattern: Redis key pattern (e.g., "service:/path:customer_id=123:*")
    
    Returns:
        int: Number of keys deleted
    """
    if not redis_client:
        cache_warning("Redis client not available for invalidation")
        return 0
    
    try:
        deleted = 0
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)
            deleted += 1
        
        if deleted > 0:
            cache_debug(f"Invalidated {deleted} key(s) matching pattern: {pattern}")
        
        return deleted
        
    except Exception as e:
        cache_warning(f"Cache invalidation failed for pattern {pattern}: {e}")
        return 0


def _model_exists(model_path):
    """
    Check if a model path exists before attempting to import.

    This allows graceful degradation when cache metadata references models
    that don't exist in the current service.

    Args:
        model_path: Full model path (e.g., "app.models.core.Customer")

    Returns:
        bool: True if model can be imported, False otherwise
    """
    import importlib

    try:
        module_path, class_name = model_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return hasattr(module, class_name)
    except (ImportError, ValueError, AttributeError):
        return False


# ============================================================================
# DEPRECATED FUNCTIONS - Kept for backward compatibility, will be removed
# ============================================================================

def register_cross_service_invalidation_batch(
    source_service,
    api_path,
    scoped_cache_keys,
    models
):
    """
    DEPRECATED: Use register_model_invalidation() instead.

    This function is kept for backward compatibility only.
    It will be removed in a future version.

    Register cross-service cache invalidation for multiple models.
    Called automatically when MicroFetcher receives cache metadata.

    Args:
        source_service: Service that owns the cache (e.g., "thrivve-service")
        api_path: API path to invalidate (e.g., "/finance/api/v1/me/balance")
        scoped_cache_keys: Cache key structure (e.g., {"customer_id": "api_params"})
        models: Dict of model paths and their invalidation conditions

    Example models structure:
        {
            "app.models.core.Customer": {
                "events": ["after_update"],
                "filters": [("id", "=", "customer_id")]
            },
            "app.models.settings.WalletSettings": {
                "events": ["after_update", "after_insert"],
                "filters": [("customer_id", "=", "customer_id")],
                "invalidate_scope": "*"
            }
        }

    Returns:
        int: Number of models successfully registered
    """
    cache_warning("register_cross_service_invalidation_batch() is deprecated, use register_model_invalidation() instead")
    import importlib

    registered_count = 0
    skipped_count = 0

    for model_path, conditions in models.items():
        # Check if model exists before importing
        if not _model_exists(model_path):
            cache_debug(f"Skipping cross-service registration: Model '{model_path}' not found in this service")
            skipped_count += 1
            continue

        try:
            # Import the model class
            module_path, class_name = model_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            model_class = getattr(module, class_name)

            events = conditions.get("events", [])
            filters = conditions.get("filters", [])
            or_filters = conditions.get("or_filters", [])
            invalidate_scope = conditions.get("invalidate_scope")

            # Add to registry
            if model_path not in _cross_service_registry:
                _cross_service_registry[model_path] = []

            # Check if already registered (avoid duplicates)
            existing = [
                r for r in _cross_service_registry[model_path]
                if r["source_service"] == source_service and r["api_path"] == api_path
            ]

            if existing:
                # print(f"[Cache] Cross-service rule already registered: {source_service}:{api_path} → {model_path}")
                continue

            # Add new rule
            _cross_service_registry[model_path].append({
                "source_service": source_service,
                "api_path": api_path,
                "scoped_cache_keys": scoped_cache_keys,
                "conditions": {
                    "filters": filters,
                    "or_filters": or_filters,
                    "invalidate_scope": invalidate_scope
                },
                "events": events
            })

            # Register SQLAlchemy listener (once per model+events)
            registry_key = (model_class, tuple(events))
            if registry_key not in _cross_service_listeners_registered:
                for ev in events:
                    event.listen(model_class, ev, _cross_service_invalidation_handler)

                _cross_service_listeners_registered.add(registry_key)
                cache_debug(f"Registered cross-service listener: {model_path} → {events}")

            registered_count += 1

        except Exception as e:
            cache_warning(f"Failed to register cross-service invalidation for {model_path}: {e}")
            skipped_count += 1
            continue

    if registered_count > 0:
        cache_debug(f"Registered {registered_count} cross-service invalidation rule(s) for {source_service}:{api_path}")
    if skipped_count > 0:
        cache_debug(f"Skipped {skipped_count} model(s) not present in this service")

    return registered_count


def _cross_service_invalidation_handler(mapper, connection, target):
    """
    DEPRECATED: Use unified_invalidation_handler() instead.

    Global handler for cross-service cache invalidation.
    Triggered when a model registered for cross-service invalidation changes.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Model instance that triggered the event
    """
    model_class = target.__class__
    model_path = f"{model_class.__module__}.{model_class.__name__}"

    if model_path not in _cross_service_registry:
        return

    # Extract snapshot while session is active (same fix as unified handler)
    target_snapshot = {
        '__class__': model_class,
        '__class_name__': model_class.__name__
    }

    # Extract all fields that might be needed
    fields_to_extract = set()
    for rule_config in _cross_service_registry[model_path]:
        conditions = rule_config["conditions"]
        for filter_tuple in conditions.get("filters", []):
            fields_to_extract.add(filter_tuple[0])
        for filter_tuple in conditions.get("or_filters", []):
            fields_to_extract.add(filter_tuple[0])

    for field in fields_to_extract:
        if hasattr(target, field):
            try:
                target_snapshot[field] = getattr(target, field)
            except Exception as e:
                cache_warning(f"Failed to extract field '{field}' from {model_class.__name__}: {e}")
                target_snapshot[field] = None

    # Get all cache rules registered for this model
    for rule_config in _cross_service_registry[model_path]:
        source_service = rule_config["source_service"]
        api_path = rule_config["api_path"]
        scoped_cache_keys = rule_config["scoped_cache_keys"]
        conditions = rule_config["conditions"]

        cache_debug(f"Evaluating cross-service invalidation for {source_service}:{api_path}")

        # Evaluate invalidation conditions using snapshot
        result = evaluate_invalidation_conditions(
            target_snapshot,
            conditions,
            scoped_cache_keys,
            service_name=source_service,
            api_path=api_path
        )

        if result is None:
            # Conditions not met, skip invalidation
            cache_debug(f"Conditions not met for {source_service}:{api_path}, skipping cross-service invalidation")
            continue

        if result.get("__invalidate_all__"):
            # Invalidate all cache for this path
            cache_debug(f"Invalidating all cache for {source_service}:{api_path} (scope: *)")
            _invalidate_remote_cache_by_path(source_service, api_path)
        else:
            # Invalidate specific cache keys
            main_cache_keys = result.get("main_cache_keys", [])
            function_cache_keys = result.get("function_cache_keys", [])

            if main_cache_keys or function_cache_keys:
                cache_debug(f"Invalidating {len(main_cache_keys)} main cache keys and {len(function_cache_keys)} function cache keys for {source_service}:{api_path}")
                _invalidate_remote_cache_keys(main_cache_keys + function_cache_keys)
            else:
                # No specific keys found, fallback to path invalidation
                cache_debug(f"No specific cache keys found, invalidating all cache for {source_service}:{api_path}")
                _invalidate_remote_cache_by_path(source_service, api_path)


def _invalidate_remote_cache_keys(cache_keys):
    """
    DEPRECATED: This is the old implementation, kept for backward compatibility.

    Invalidate specific cache keys in remote service by directly accessing Valkey.

    Since all services share the same Valkey instance, we can directly
    delete cache keys without making HTTP requests.

    Args:
        cache_keys: List of cache keys to delete
    """
    # Import here to avoid circular dependency
    from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule
    from redis import exceptions as redis_exceptions

    if not BaseCacheRule._redis_client:
        cache_warning("Redis client not available for cross-service invalidation")
        return

    deleted_count = 0
    for cache_key in cache_keys:
        try:
            deleted = BaseCacheRule._redis_client.delete(cache_key)
            if deleted > 0:
                deleted_count += 1
                cache_debug(f"Deleted cache key: {cache_key}")
        except redis_exceptions.RedisError as e:
            cache_warning(f"Failed to delete cache key {cache_key}: {e}")

    if deleted_count > 0:
        cache_debug(f"Cross-service invalidation: Deleted {deleted_count} cache key(s)")


def _invalidate_remote_cache_by_path(source_service, api_path):
    """
    DEPRECATED: This is the old implementation, kept for backward compatibility.

    Invalidate all cache for a path in remote service (path-based invalidation).

    Args:
        source_service: Service name that owns the cache (e.g., "thrivve-service")
        api_path: API path to invalidate (e.g., "/finance/api/v1/me/balance")
    """
    # Import here to avoid circular dependency
    from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule

    if not BaseCacheRule._redis_client:
        cache_warning("Redis client not available for cross-service invalidation")
        return

    # Build pattern for all keys on this path
    pattern = f"{source_service}/{api_path}:*"

    # Invalidate using shared utility
    deleted = invalidate_cache_by_pattern(BaseCacheRule._redis_client, pattern)

    if deleted > 0:
        cache_debug(f"Cross-service path invalidation: Deleted {deleted} key(s) for {source_service}:{api_path}")


def get_cross_service_registry():
    """
    Get the current cross-service registry for debugging/monitoring.
    
    Returns:
        dict: Current registry state with registry and listener count
    """
    return {
        "registry": _cross_service_registry,
        "listeners_count": len(_cross_service_listeners_registered),
        "registered_models": list(_cross_service_registry.keys())
    }

