import ast
import json
import threading
from functools import wraps

from sqlalchemy.orm.base import object_mapper
import flask_sqlalchemy
from flask import request, g
from marshmallow import ValidationError
from sqlalchemy.orm.exc import UnmappedInstanceError

from wedeliver_core_plus.helpers.exceptions import AppValidationError


def is_mapped(obj):
    try:
        data = obj
        if isinstance(data, list) and len(data):
            data = obj[0]
        object_mapper(data)
    except UnmappedInstanceError:
        return False
    return True

def is_result_row(obj):
    try:
        data = obj
        if isinstance(data, list) and len(data):
            data = obj[0]

        if hasattr(data, '__row_data__'):
            return True
    except UnmappedInstanceError:
        return False
    return False


def _serialize_result(result, schema, many):
    """
    Serialize the result from a route handler function.

    Handles three types of results:
    1. Pagination objects - extracts items and metadata
    2. Mapped SQLAlchemy models - uses schema to dump
    3. Raw data (dict/list) - returns as-is

    Args:
        result: The raw result from the route handler
        schema: Marshmallow schema class for serialization
        many: Boolean flag for list serialization

    Returns:
        Serialized output (dict or list)
    """
    if isinstance(result, flask_sqlalchemy.Pagination):
        items = schema(many=isinstance(result.items, list)).dump(result.items)
        output = dict(
            items=items,
            total=result.total,
            next_num=result.next_num,
            prev_num=result.prev_num,
            page=result.page,
            per_page=result.per_page
        )
    elif is_mapped(result) or is_result_row(result):  # is model instance
        output = schema(many=isinstance(result, list)).dump(result)
    else:
        output = result

    return output


def _store_cache_metadata_in_context(service_name, api_path, scoped_cache_keys, cross_service_models):
    """
    Store cache metadata in Flask request context (g object).
    This allows MicroFetcher to access it and piggyback registration data.

    Args:
        service_name: Current service name (e.g., "thrivve-service")
        api_path: API path (e.g., "/finance/api/v1/me/balance")
        scoped_cache_keys: Cache key structure (e.g., {"customer_id": "api_params"})
        cross_service_models: Cross-service model invalidation conditions
    """
    if not hasattr(g, '_cache_registration_metadata'):
        g._cache_registration_metadata = []

    g._cache_registration_metadata.append({
        "source_service": service_name,
        "api_path": api_path,
        "scoped_cache_keys": scoped_cache_keys,
        "models": cross_service_models
    })


def serializer(path, schema=None, many=False, cache_rule=None):
    def factory(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            # user_language = Auth.get_user_language()
            # with force_locale(user_language):
            is_function_with_validated_data = False
            if hasattr(func, '__wrapped__'):
                old_vars = func.__wrapped__.__code__.co_varnames
                is_function_with_validated_data = old_vars.__contains__('validated_data')

            appended_kws = kwargs.pop('appended_kws', None)

            try:
                client_data = dict()

                if kwargs:
                    client_data.update(**kwargs)

                content_type = request.headers.get('Content-Type')
                if content_type and 'application/json' in content_type:
                    # if the request have json payload, the user need to send the Content-Type as application/json
                    try:
                        client_data.update(request.json)
                    except Exception:
                        pass

                elif request.form:
                    client_data.update(request.form.to_dict())

                    def _sanitize(cd):
                        for _k in cd.keys():
                            try:
                                value = ast.literal_eval(cd[_k])
                                if isinstance(value, int):
                                    value = str(value)
                                cd[_k] = value
                            except Exception:
                                try:
                                    value = json.loads(cd[_k])
                                    if isinstance(value, list):
                                        output = []
                                        for _v in value:
                                            output.append(_sanitize(_v))
                                        cd[_k] = output
                                    if isinstance(value, dict):
                                        cd[_k] = _sanitize(value)
                                except Exception:
                                    pass
                        return cd

                    _sanitize(client_data)

                if request.args:
                    client_data.update(request.args.to_dict())

                inputs = client_data  # .to_dict()
                if appended_kws:
                    inputs.update(appended_kws)

                if schema:
                    result = schema(many=many).load(inputs)
                else:
                    result = inputs
            except ValidationError as e:
                raise AppValidationError(e.messages)

            if result:
                if is_function_with_validated_data:
                    kwargs.update(dict(validated_data=result))
            # if schema and request.method == "GET":

            # ---------------- Cache logic using CacheManager ----------------
            from wedeliver_core_plus.helpers.caching.cache_manager import CacheManager

            cache_manager = CacheManager(
                cache_rule=cache_rule,
                path=path,
                request_data=kwargs.get("validated_data", {})
            )

            # Initialize cache and check for cached response
            if cache_manager.initialize():
                # Set validation context (needed for cache validation)
                from wedeliver_core_plus.helpers.auth import Auth
                user_language = Auth.get_user_language()
                cache_manager.set_validation_context(func, schema, many, user_language)

                # Try to get cached response
                cached_response = cache_manager.get_cached_response()
                if cached_response is not None:
                    return cached_response  # 🟢 Cache hit - return immediately

            # ---------------- Execute main function ----------------

            try:
                result = func(*args, **kwargs)
                output = _serialize_result(result, schema, many)
            except ValidationError as e:
                raise AppValidationError(e.messages)

            # ---------------- Store in cache (async, non-blocking) ----------------
            cache_manager.store_response_async(output)

            return output

        return decorator

    return factory
