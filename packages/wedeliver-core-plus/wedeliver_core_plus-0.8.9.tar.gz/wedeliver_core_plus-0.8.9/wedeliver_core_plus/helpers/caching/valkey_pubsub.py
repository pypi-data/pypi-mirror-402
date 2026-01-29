"""
Valkey Pub/Sub for cache registration across workers/pods.

This module provides publisher and subscriber for broadcasting cache rule
registration events across all workers and pods, ensuring consistent cache
invalidation in multi-worker/multi-pod deployments.

Architecture:
    1. Worker 1 handles request → Registers cache rule locally → Publishes event
    2. ALL workers/pods receive event via Pub/Sub
    3. Each worker checks if model exists in THIS service
    4. If model exists → Register invalidation config in local memory
    5. When model updates → All workers have listeners registered → Cache invalidated

Key Benefits:
    - No data duplication (only store invalidation config, not cache rule instance)
    - Reuses existing ModelDiscovery mechanism
    - Service isolation (each service checks its own models)
    - Memory efficient (config dict is smaller than cache rule instance)
"""

import json
import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from flask import current_app
from redis import Redis
from redis import exceptions as redis_exceptions

from wedeliver_core_plus.helpers.caching.cache_logger import (
    cache_debug,
    cache_error,
    cache_info,
    cache_warning,
)


class ValkeyRegistrationPublisher:
    """
    Publishes model registration events to Valkey Pub/Sub.
    
    Features:
    - Singleton pattern (shared across all cache rules)
    - Non-blocking async publishing (thread pool)
    - Automatic deduplication (tracks published events)
    - Minimal message payload (only invalidation config)
    
    Message Format:
        {
            "type": "REGISTER_MODEL",
            "model": "Customer",
            "path": "/core/api/v1/mobile/home/messages",
            "scoped_cache_keys": {"customer_id": "api_params"},
            "conditions": {
                "events": ["after_update", "after_insert"],
                "filters": [("id", "=", "customer_id")]
            },
            "timestamp": "2025-11-26T10:30:00Z",
            "service": "thrivve-service"
        }
    """
    
    _instance = None
    _publish_pool = None
    _published = set()  # Track published events to avoid duplicates
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset singleton (called in gunicorn post_fork)."""
        cls._instance = None
        cls._published = set()
    
    def __init__(self):
        """Initialize publisher with thread pool."""
        # Thread pool for async publishing (small pool, low overhead)
        self._publish_pool = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="cache-reg-pub"
        )
    
    def publish(self, model_name, path, scoped_cache_keys, conditions, service_name=None):
        """
        Publish registration message to Valkey channel (async).

        Args:
            model_name: Model name (e.g., "Customer")
            path: API path (e.g., "/core/api/v1/mobile/home/messages")
            scoped_cache_keys: Cache key structure (e.g., {"customer_id": "api_params"})
            conditions: Invalidation conditions (events, filters, etc.)
            service_name: Service name (optional, uses env var if not provided)
        """
        # Check if already published (avoid duplicates)
        registry_key = (model_name, path)
        if registry_key in self._published:
            cache_debug(f"[Cache] Already published: {model_name} for {path}")
            return

        # Use environment variable if not provided (no app context needed)
        if service_name is None:
            service_name = os.environ.get("SERVICE_NAME", "default-service")

        # Build message
        message = {
            "type": "REGISTER_MODEL",
            "model": model_name,
            "path": path,
            "scoped_cache_keys": scoped_cache_keys,
            "conditions": conditions,
            "timestamp": datetime.utcnow().isoformat(),
            "service": service_name
        }

        # Publish asynchronously (non-blocking)
        self._publish_pool.submit(self._publish_sync, message, service_name)

        # Mark as published
        self._published.add(registry_key)

    def publish_bulk(self, models, path, scoped_cache_keys, service_name=None):
        """
        Publish bulk registration message for multiple models (async).

        This is more efficient than calling publish() for each model individually.

        Args:
            models: Dict of {model_name: conditions}
            path: API path
            scoped_cache_keys: Cache key structure
            service_name: Service name (optional, uses env var if not provided)
        """
        # Use environment variable if not provided (no app context needed)
        if service_name is None:
            service_name = os.environ.get("SERVICE_NAME", "default-service")

        # Build list of models to publish (filter out duplicates and invalid types)
        models_list = []
        for model_name, conditions in models.items():
            # Only support string-based model names
            if not isinstance(model_name, str):
                cache_error(
                    f"model_invalidation_conditions keys must be strings (model names), not class references. "
                    f"Got: {type(model_name).__name__}. Please use model name like 'Customer' instead of Customer class."
                )
                continue

            # Check if already published
            registry_key = (model_name, path)
            if registry_key in self._published:
                cache_debug(f"[Cache] Already published: {model_name} for {path}")
                continue

            models_list.append({
                "model": model_name,
                "conditions": conditions
            })
            self._published.add(registry_key)

        if not models_list:
            cache_debug(f"[Cache] No new models to publish for {path}")
            return  # Nothing to publish

        # Build bulk message
        message = {
            "type": "REGISTER_MODELS_BULK",
            "path": path,
            "scoped_cache_keys": scoped_cache_keys,
            "models": models_list,
            "timestamp": datetime.utcnow().isoformat(),
            "service": service_name
        }

        # Publish asynchronously
        self._publish_pool.submit(self._publish_sync, message, service_name)
        cache_debug(f"[Cache] Published bulk registration for {len(models_list)} models on {path}")
    
    def _publish_sync(self, message, service_name):
        """
        Background worker that publishes to Valkey.

        Args:
            message: Registration message to publish
            service_name: Service name (captured from app context before async execution)
        """
        try:
            from wedeliver_core_plus.helpers.caching.valkey_redis_utils import BaseCacheRule

            # Access the class variable directly (same pattern as flush_all_cache)
            redis_client = BaseCacheRule._redis_client
            if not redis_client:
                # Initialize if needed
                temp_instance = BaseCacheRule.__new__(BaseCacheRule)
                BaseCacheRule._redis_client = temp_instance._create_redis_client()
                redis_client = BaseCacheRule._redis_client

            if not redis_client:
                cache_warning("[Cache] Redis client not available for publishing")
                return

            # Use service_name passed from publish() method (no app context needed)
            channel = f"cache:registration:{service_name}"

            redis_client.publish(channel, json.dumps(message))
            cache_debug(f"[Cache] Published registration: {message['model']} for {message['path']}")
        except Exception as e:
            cache_error(f"[Cache] Failed to publish registration: {e}")


class ValkeyRegistrationSubscriber:
    """
    Subscribes to model registration events and registers models locally.
    
    Flow:
        1. Worker 1 handles request → Registers model → Publishes event
        2. ALL workers receive event
        3. Each worker checks: Does this model exist in MY service?
        4. If YES → Register invalidation config in local memory
        5. If NO → Ignore (model not in this service)
    
    Features:
    - Runs in background daemon thread
    - Automatic reconnection on failure
    - Idempotent (handles duplicate messages)
    - Reuses existing ModelDiscovery mechanism
    """
    
    _instance = None
    _subscriber_thread = None
    _running = False
    _registered_models = set()  # Track registered models to avoid duplicates
    _app = None  # Store Flask app instance for application context

    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (called in gunicorn post_fork)."""
        if cls._instance and cls._instance._running:
            cls._instance.stop()
        cls._instance = None
        cls._registered_models = set()

    def start(self, app=None):
        """
        Start subscriber in background daemon thread.

        Args:
            app: Flask application instance (needed for app context in background thread)
        """
        if self._running:
            cache_debug("[Cache] Registration subscriber already running")
            return

        # Store app instance for use in background thread
        if app:
            self._app = app

        self._running = True
        self._subscriber_thread = threading.Thread(
            target=self._subscribe_loop,
            daemon=True,
            name=f"cache-reg-sub-{os.getpid()}"
        )
        self._subscriber_thread.start()
        cache_info(f"[Cache] Registration subscriber started in worker {os.getpid()}")
    
    def stop(self):
        """Stop subscriber gracefully."""
        self._running = False
        if self._subscriber_thread:
            self._subscriber_thread.join(timeout=2)
        cache_info(f"[Cache] Registration subscriber stopped in worker {os.getpid()}")

    def _create_pubsub_redis_client(self):
        """
        Create a dedicated Redis client for Pub/Sub with long timeout.

        This client is separate from the cache client and configured specifically
        for blocking Pub/Sub operations:
        - No socket timeout (can wait indefinitely for messages)
        - Socket keepalive enabled (detect dead connections)
        - Longer connect timeout (5 seconds)

        Returns:
            Redis client or None if creation failed
        """
        # Get Redis configuration from app context or environment
        if self._app:
            with self._app.app_context():
                host = self._app.config.get("CACHE_VALKEY_HOST", "valkey-redis")
                port = self._app.config.get("CACHE_VALKEY_PORT", 6379)
                ssl = self._app.config.get("CACHE_VALKEY_SSL", False)
        else:
            host = os.environ.get("CACHE_VALKEY_HOST", "valkey-redis")
            port = int(os.environ.get("CACHE_VALKEY_PORT", 6379))
            ssl = os.environ.get("CACHE_VALKEY_SSL", "False") == "True"

        try:
            client = Redis(
                host=host,
                port=port,
                ssl=ssl,
                decode_responses=True,
                socket_connect_timeout=5,  # 5 seconds to connect
                socket_timeout=None,  # No timeout for blocking Pub/Sub operations
                socket_keepalive=True,  # Enable TCP keepalive
                socket_keepalive_options={
                    socket.TCP_KEEPIDLE: 60,   # Start keepalive after 60s idle
                    socket.TCP_KEEPINTVL: 10,  # Send keepalive every 10s
                    socket.TCP_KEEPCNT: 3      # Close after 3 failed keepalives
                }
            )
            client.ping()
            cache_info(f"[Cache] Created Pub/Sub Redis client: {host}:{port}")
            return client
        except redis_exceptions.ConnectionError as e:
            cache_error(f"[Cache] Failed to create Pub/Sub Redis client: {e}")
            return None
        except Exception as e:
            cache_error(f"[Cache] Unexpected error creating Pub/Sub Redis client: {e}")
            return None

    def _subscribe_loop(self):
        """Background loop listening for registration events."""
        # Get service name using app context if available
        if self._app:
            with self._app.app_context():
                service_name = self._app.config.get("SERVICE_NAME", "default-service")
        else:
            # Fallback to environment variable if app not available
            service_name = os.environ.get("SERVICE_NAME", "default-service")

        channel = f"cache:registration:{service_name}"

        cache_info(f"[Cache] Subscribing to registration channel: {channel}")

        while self._running:
            try:
                # Create dedicated Pub/Sub Redis client (with no socket timeout)
                redis_client = self._create_pubsub_redis_client()

                # Check if client is available
                if redis_client is None:
                    cache_warning("[Cache] Pub/Sub Redis client not available, retrying in 5s...")
                    time.sleep(5)
                    continue

                # Create Pub/Sub connection
                pubsub = redis_client.pubsub()
                pubsub.subscribe(channel)

                cache_info(f"[Cache] Subscribed to channel: {channel}")

                # Listen for messages (blocking, no timeout)
                for message in pubsub.listen():
                    if not self._running:
                        break

                    if message and message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            self._handle_registration_message(data)
                        except Exception as e:
                            cache_error(f"[Cache] Failed to process message: {e}")

            except Exception as e:
                cache_error(f"[Cache] Subscriber error: {e}")
                if self._running:
                    cache_info("[Cache] Reconnecting in 5 seconds...")
                    time.sleep(5)
            finally:
                # Clean up Pub/Sub connection
                try:
                    if 'pubsub' in locals():
                        pubsub.close()
                except:
                    pass
    
    def _handle_registration_message(self, message):
        """
        Process registration message (single or bulk).

        Supports two message types:
            - REGISTER_MODEL: Single model registration (backward compatible)
            - REGISTER_MODELS_BULK: Multiple models in one message (efficient)
        """
        try:
            msg_type = message.get('type', 'REGISTER_MODEL')

            if msg_type == 'REGISTER_MODELS_BULK':
                # Handle bulk registration
                path = message['path']
                scoped_cache_keys = message['scoped_cache_keys']
                models = message['models']

                cache_debug(f"[Cache] Received bulk registration for {len(models)} models on {path}")

                for model_config in models:
                    self._register_single_model(
                        model_name=model_config['model'],
                        path=path,
                        scoped_cache_keys=scoped_cache_keys,
                        conditions=model_config['conditions']
                    )
            else:
                # Handle single model registration (backward compatibility)
                self._register_single_model(
                    model_name=message['model'],
                    path=message['path'],
                    scoped_cache_keys=message['scoped_cache_keys'],
                    conditions=message['conditions']
                )
        except Exception as e:
            cache_error(f"[Cache] Failed to handle registration message: {e}")

    def _register_single_model(self, model_name, path, scoped_cache_keys, conditions):
        """
        Register a single model (extracted for reuse in bulk and single registration).

        Steps:
            1. Check if already registered (avoid duplicates)
            2. Check if model exists in THIS service (using ModelDiscovery)
            3. If model NOT found → Ignore (model not in this service)
            4. If model found → Register invalidation config in local memory
            5. Register SQLAlchemy listener (if not already registered)
        """
        try:
            # Check if already registered (avoid duplicates)
            registry_key = (model_name, path)
            if registry_key in self._registered_models:
                cache_debug(f"[Cache] Already registered: {model_name} for {path}")
                return

            # Check if model exists in THIS service
            from wedeliver_core_plus.helpers.model_discovery import ModelDiscovery
            discovery = ModelDiscovery()

            if not discovery.has_model(model_name):
                # Model not in this service → Ignore
                cache_debug(f"[Cache] Model '{model_name}' not found in this service, skipping")
                return

            # Get model class
            model_class = discovery.get_model_class(model_name)

            # Register invalidation config in local memory
            self._register_invalidation_config(
                model_class=model_class,
                path=path,
                scoped_cache_keys=scoped_cache_keys,
                conditions=conditions
            )

            # Mark as registered
            self._registered_models.add(registry_key)

            cache_info(f"[Cache] ✅ Registered {model_name} invalidation for {path} in worker {os.getpid()}")

        except Exception as e:
            cache_error(f"[Cache] Failed to register model {model_name}: {e}")
    
    def _register_invalidation_config(self, model_class, path, scoped_cache_keys, conditions):
        """
        Register invalidation configuration in local memory.

        Reuses existing functions from cache_invalidation_registry to avoid code duplication.
        """
        from wedeliver_core_plus.helpers.caching.cache_invalidation_registry import (
            _register_model_in_worker,
            _register_sqlalchemy_listener
        )

        # Register in worker's local memory (handles duplicate checking)
        _register_model_in_worker(
            model_class=model_class,
            path=path,
            scoped_cache_keys=scoped_cache_keys,
            conditions=conditions,
            cache_rule_instance=None  # No cache rule instance in Pub/Sub flow
        )

        # Register SQLAlchemy listener (once per model+events)
        events = conditions.get("events", [])
        _register_sqlalchemy_listener(model_class, events)

