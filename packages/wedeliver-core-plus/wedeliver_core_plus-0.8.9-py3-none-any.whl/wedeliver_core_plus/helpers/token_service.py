from datetime import datetime, timedelta
import jwt
from flask import request, current_app as app
from wedeliver_core_plus.helpers.system_roles import Role
from wedeliver_core_plus.helpers.enums import App
from wedeliver_core_plus.helpers.exceptions import (
    AppExpiredTokenError,
    AppAccessTokenExpiredError,
)
from flask_babel import _


class TokenService:
    @staticmethod
    def generate_access_token(account, device, token_version, expires_minutes=None):
        """Generate a short-lived access token (30 minutes by default)"""
        if not expires_minutes:
            expires_minutes = int(app.config.get("ACCESS_TOKEN_EXPIRATION_MINUTES", 60))

        token_data = dict(
            account_id=account.id,
            device_id=device.id,
            language=device.language,
            app=App.CUSTOMER_APP.value,
            role=Role.APP_USER,
            customer=dict(id=account.party_id),
            is_logged=True,
            exp=int(
                datetime.timestamp(datetime.now() + timedelta(minutes=expires_minutes))
            ),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            mobile=account.mobile,
            app_version=device.app_version,
            platform=device.platform,
            token_version=token_version,
        )
        token = jwt.encode(token_data, app.config.get("SECRET_KEY"), algorithm="HS256")
        return token  # PyJWT 2.x returns string directly

    @staticmethod
    def generate_pre_token(account, expires_days=30):
        """Generate a pre-login token (used after OTP verification)"""
        token_data = dict(
            account_id=account.id,
            pre_auth=True,
            exp=int(datetime.timestamp(datetime.now() + timedelta(days=expires_days))),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        token = jwt.encode(token_data, app.config.get("SECRET_KEY"), algorithm="HS256")
        return token if isinstance(token, str) else token.decode("utf-8")

    @staticmethod
    def verify_access_token(token, skip_expiration_check=False):
        """Verify an access token and return the decoded data"""
        try:
            verify_token = (
                    app.config.get("TESTING") is True
                    or app.config.get("FLASK_ENV") == "production"
            )

            # Decode without verification to read the payload
            # (we're just checking the version, not authenticating)
            options = {"verify_signature": verify_token}

            # Skip expiration check if requested
            if skip_expiration_check:
                options["verify_exp"] = False

            token_data = jwt.decode(
                token,
                key=app.config.get("SECRET_KEY"),
                algorithms=["HS256"],
                options=options,
            )

            # If needed, add additional verification logic here
            # For example, check if the device is still active

            return token_data
        except jwt.DecodeError:
            raise AppExpiredTokenError(_("Token is not valid, please do login"))
        except jwt.ExpiredSignatureError:
            raise AppAccessTokenExpiredError(
                _("Token is expired, please refresh token")
            )

    @staticmethod
    def get_token_from_request():
        """Helper method to extract token from request headers"""
        if "Authorization" not in request.headers:
            return None
        return request.headers["Authorization"]
