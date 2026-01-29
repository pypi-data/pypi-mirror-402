"""
Cache Health and Management Functions

This module contains business logic for cache health endpoints.
Routes remain in base.py as thin wrappers that delegate to these functions.

Functions:
    - get_cache_health: Health check for cache system
    - get_cache_registry_details: Detailed registry information
    - list_customer_cache_keys: List all cache keys for a customer
    - delete_customer_cache_keys: Delete all cache keys for a customer
"""

import os


def get_cache_health():
    """
    Health check endpoint for cache system.

    Returns:
        dict: Cache system status and metrics (200 OK)

    Raises:
        AppSilentException: Cache system degraded (503) or unhealthy (500)
    """
    from wedeliver_core_plus.helpers.exceptions import AppSilentException

    try:
        from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule
        from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import (
            _unified_registry,
            _listeners_registered,
            _event_pool,
            _event_pool_initialized,
            _should_use_gevent_pool
        )

        health_status = {
            "status": "healthy",
            "worker_pid": os.getpid(),
            "gevent_available": _should_use_gevent_pool(),
            "redis": {},
            "event_pool": {},
            "invalidation_pool": {},
            "registration_pool": {},
            "registry": {},
        }

        # Check Redis connection
        if BaseCacheRule._redis_client is not None:
            try:
                BaseCacheRule._redis_client.ping()
                health_status["redis"] = {
                    "status": "connected",
                    "client_initialized": True
                }
            except Exception as e:
                health_status["status"] = "degraded"
                health_status["redis"] = {
                    "status": "error",
                    "error": str(e),
                    "client_initialized": True
                }
        else:
            health_status["status"] = "degraded"
            health_status["redis"] = {
                "status": "not_initialized",
                "client_initialized": False
            }

        # Check event pool
        if _event_pool_initialized and _event_pool is not None:
            pool_type = "gevent" if hasattr(_event_pool, 'spawn') else "thread"
            health_status["event_pool"] = {
                "status": "initialized",
                "type": pool_type,
                "initialized": True
            }
        else:
            health_status["event_pool"] = {
                "status": "not_initialized",
                "initialized": False
            }

        # Check invalidation pool
        if BaseCacheRule._invalidation_pool_initialized and BaseCacheRule._invalidation_pool is not None:
            pool_type = "gevent" if hasattr(BaseCacheRule._invalidation_pool, 'spawn') else "thread"
            health_status["invalidation_pool"] = {
                "status": "initialized",
                "type": pool_type,
                "initialized": True
            }
        else:
            health_status["invalidation_pool"] = {
                "status": "not_initialized",
                "initialized": False
            }

        # Check registration pool
        if BaseCacheRule._registration_pool_initialized and BaseCacheRule._registration_pool is not None:
            pool_type = "gevent" if hasattr(BaseCacheRule._registration_pool, 'spawn') else "thread"
            health_status["registration_pool"] = {
                "status": "initialized",
                "type": pool_type,
                "initialized": True
            }
        else:
            health_status["registration_pool"] = {
                "status": "not_initialized",
                "initialized": False
            }

        # Registry statistics
        health_status["registry"] = {
            "models_registered": len(_unified_registry),
            "listeners_registered": len(_listeners_registered),
            "model_names": [model.__name__ for model in _unified_registry.keys()]
        }

        # Check if system is degraded and raise exception
        if health_status["redis"]["status"] != "connected":
            exception = AppSilentException(
                f"Cache system degraded: Redis {health_status['redis']['status']}"
            )
            exception.code = 503
            raise exception

        # Success - return data only (no status code)
        return health_status

    except AppSilentException:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Unexpected errors - raise as 503 Service Unavailable
        exception = AppSilentException(
            f"Cache health check failed: {str(e)}"
        )
        exception.code = 503
        raise exception


def get_cache_registry_details():
    """
    Detailed cache registry information for debugging.

    Returns:
        dict: Detailed registry information (200 OK)

    Raises:
        AppSilentException: Registry retrieval failed (500)
    """
    from wedeliver_core_plus.helpers.exceptions import AppSilentException

    try:
        from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import (
            _unified_registry,
            _listeners_registered
        )

        registry_details = {
            "worker_pid": os.getpid(),
            "total_models": len(_unified_registry),
            "total_listeners": len(_listeners_registered),
            "models": {}
        }

        # Build detailed model information
        for model_class, rules in _unified_registry.items():
            model_name = model_class.__name__
            registry_details["models"][model_name] = {
                "local_rules_count": len(rules.get("local_rules", [])),
                "cross_service_rules_count": len(rules.get("cross_service_rules", [])),
                "local_rules": [
                    {
                        "path": rule.path,
                        "ttl_seconds": rule.ttl.total_seconds() if hasattr(rule.ttl, 'total_seconds') else None
                    }
                    for rule in rules.get("local_rules", [])
                ],
                "cross_service_rules": [
                    {
                        "source_service": rule["source_service"],
                        "api_path": rule["api_path"]
                    }
                    for rule in rules.get("cross_service_rules", [])
                ]
            }

        # Listener information
        registry_details["listeners"] = [
            {
                "model": model_class.__name__,
                "events": list(events)
            }
            for model_class, events in _listeners_registered
        ]

        # Success - return data only (no status code)
        return registry_details

    except Exception as e:
        # Unexpected errors - raise as 500 Internal Server Error
        raise AppSilentException(
            f"Cache registry details failed: {str(e)}"
        )


def list_customer_cache_keys(customer_id: int):
    """
    List all cache keys for a specific customer.

    Searches for keys containing 'customer_id={customer_id}' pattern.

    Args:
        customer_id: Customer ID to search for

    Returns:
        dict: List of cache keys with TTL information

    Raises:
        AppSilentException: Redis not available or operation failed
    """
    from wedeliver_core_plus.helpers.exceptions import AppSilentException
    from flask import current_app

    try:
        from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule

        # Check Redis availability
        if BaseCacheRule._redis_client is None:
            raise AppSilentException("Redis client not initialized")

        service_name = current_app.config.get("SERVICE_NAME", "default-service")

        # Pattern to match keys containing customer_id=<value>
        # Format: {service_name}:*customer_id={customer_id}*
        pattern = f"{service_name}:*customer_id={customer_id}*"

        keys_info = []
        total_keys = 0

        # Scan for matching keys
        for key in BaseCacheRule._redis_client.scan_iter(match=pattern):
            # Decode key if bytes
            if isinstance(key, bytes):
                key = key.decode('utf-8')

            # Get TTL for the key
            ttl = BaseCacheRule._redis_client.ttl(key)

            # Format TTL info
            if ttl == -1:
                ttl_display = "No expiry"
            elif ttl == -2:
                ttl_display = "Key does not exist"
            else:
                # Convert seconds to human readable
                minutes, seconds = divmod(ttl, 60)
                hours, minutes = divmod(minutes, 60)
                if hours > 0:
                    ttl_display = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    ttl_display = f"{minutes}m {seconds}s"
                else:
                    ttl_display = f"{seconds}s"

            keys_info.append({
                "key": key,
                "ttl_seconds": ttl,
                "expires_in": ttl_display
            })
            total_keys += 1

        return {
            "customer_id": customer_id,
            "service_name": service_name,
            "total_keys": total_keys,
            "keys": keys_info
        }

    except AppSilentException:
        raise
    except Exception as e:
        raise AppSilentException(f"Failed to list customer cache keys: {str(e)}")


def delete_customer_cache_keys(customer_id: int):
    """
    Delete all cache keys for a specific customer.

    Uses GET method for easy browser access.
    Searches for keys containing 'customer_id={customer_id}' pattern and deletes them.

    Args:
        customer_id: Customer ID to delete cache for

    Returns:
        dict: Count of deleted keys and status message

    Raises:
        AppSilentException: Redis not available or operation failed
    """
    from wedeliver_core_plus.helpers.exceptions import AppSilentException
    from flask import current_app

    try:
        from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule

        # Check Redis availability
        if BaseCacheRule._redis_client is None:
            raise AppSilentException("Redis client not initialized")

        service_name = current_app.config.get("SERVICE_NAME", "default-service")

        # Pattern to match keys containing customer_id=<value>
        pattern = f"{service_name}:*customer_id={customer_id}*"

        deleted_count = 0
        deleted_keys = []

        # Scan and delete matching keys
        for key in BaseCacheRule._redis_client.scan_iter(match=pattern):
            # Decode key if bytes
            if isinstance(key, bytes):
                key = key.decode('utf-8')

            # Delete the key
            BaseCacheRule._redis_client.delete(key)
            deleted_keys.append(key)
            deleted_count += 1

        return {
            "customer_id": customer_id,
            "service_name": service_name,
            "deleted_count": deleted_count,
            "deleted_keys": deleted_keys,
            "message": f"Successfully deleted {deleted_count} cache key(s) for customer {customer_id}"
        }

    except AppSilentException:
        raise
    except Exception as e:
        raise AppSilentException(f"Failed to delete customer cache keys: {str(e)}")

