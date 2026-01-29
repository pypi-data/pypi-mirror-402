import json
from functools import wraps
from flask import Response
from werkzeug.wrappers import Response as WerkzeugResponse

SUCCESS_CODES = {200, 201, 204}
REDIRECT_CODES = {301, 302, 303, 307, 308}

def handle_response(func):
    @wraps(func)
    def inner_function(*args, **kwargs):
        result = func(*args, **kwargs)

        # ✅ Catch ANY response type (Flask/Werkzeug), including redirect()
        if isinstance(result, (Response, WerkzeugResponse)):
            return result

        response = result
        code = 200
        use_default_response_message_key = True
        headers = None

        # ✅ Handle tuples safely
        if isinstance(result, tuple):
            if len(result) == 2:
                response, code = result

            elif len(result) == 3:
                response, code, third = result

                # Your custom signature: (payload, code, bool)
                if isinstance(third, bool):
                    use_default_response_message_key = third
                else:
                    # Flask signature: (payload, code, headers)
                    headers = third

            else:
                raise ValueError("Invalid return tuple. Expected 2 or 3 items.")

        # ✅ If it’s a redirect code but returned as tuple/string, don't JSON-wrap it
        # (Usually redirect() returns Response, so you won't reach here)
        if code in REDIRECT_CODES and isinstance(response, (str, bytes)):
            return Response(response, status=code, headers=headers)

        # ✅ Your message wrapping logic
        if code not in SUCCESS_CODES and use_default_response_message_key:
            response = {"message": response}

        return Response(
            json.dumps(response),
            content_type="application/json",
            status=code,
            headers=headers,
        )

    return inner_function
