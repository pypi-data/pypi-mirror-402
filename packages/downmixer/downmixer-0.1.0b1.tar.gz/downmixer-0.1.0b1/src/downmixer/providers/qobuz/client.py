"""Qobuz API client implementation.

This module provides the QobuzClient class for making authenticated requests
to the Qobuz API, including login and content retrieval.
"""

import hashlib

import requests

from downmixer.providers.qobuz.bundle import Bundle
from downmixer.types import LoggerLike

API_URL = "https://www.qobuz.com/api.json/0.2/"


class QobuzClient:
    """HTTP client for the Qobuz API.

    Handles authentication and API requests to Qobuz. Requires a valid
    app bundle with credentials and a paid subscription for full access.

    Attributes:
        auth_token: The user's authentication token after login.
        sec: The active app secret for signing requests.
        secrets: Available app secrets from the bundle.
        app_id: The application ID for API requests.
        session: The requests session with configured headers.
        logger: Logger instance for logging messages.
    """

    auth_token: str

    def __init__(self, bundle: Bundle, logger: LoggerLike):
        """Initialize the Qobuz client with app credentials.

        Args:
            bundle: A Bundle instance containing app ID and secrets.
            logger: Logger instance for logging messages.
        """
        self.sec = None
        self.secrets = bundle.get_secrets().values()
        self.app_id = bundle.get_app_id()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0",
                "X-App-Id": self.app_id,
                "Content-Type": "application/json;charset=UTF-8",
            }
        )

        self.logger = logger

    def login(self, email: str, password: bytes) -> bool:
        """Authenticate with Qobuz using email and password.

        Args:
            email: The user's email address.
            password: The user's password as bytes.

        Returns:
            True if login was successful.

        Raises:
            IneligibleError: If the account is a free account.
            ValueError: If credentials are invalid.
        """
        params = {
            "email": email,
            "password": hashlib.md5(password).hexdigest(),
            "app_id": self.app_id,
        }

        response = self.request("user/login", **params)

        if not response["user"]["credential"]["parameters"]:
            raise IneligibleError("Free accounts are not eligible to download tracks.")

        self.auth_token = response["user_auth_token"]
        self.session.headers.update({"X-User-Auth-Token": self.auth_token})

        # self.label = response["user"]["credential"]["parameters"]["short_label"]

        # TODO: add try/catch to catch wrong email/password
        return True

    def request(self, endpoint: str, **kwargs) -> dict:
        """Make a request to the Qobuz API.

        Args:
            endpoint: The API endpoint path (e.g., "album/get").
            **kwargs: Query parameters to include in the request.

        Returns:
            The JSON response as a dictionary.

        Raises:
            ValueError: If credentials or app ID are invalid.
            InvalidAppSecretError: If the app secret is invalid.
            requests.HTTPError: If the request fails.
        """
        r = self.session.get(API_URL + endpoint, params=kwargs)

        # TODO: move this to specific requests
        if endpoint == "user/login":
            if r.status_code == 401:
                raise ValueError("Invalid credentials.")
            elif r.status_code == 400:
                raise ValueError("Invalid app id.")
            else:
                self.logger.info("Logged: OK")
        elif (
            endpoint in ["track/getFileUrl", "favorite/getUserFavorites"]
            and r.status_code == 400
        ):
            raise InvalidAppSecretError(f"Invalid app secret: {r.json()}.")

        r.raise_for_status()
        return r.json()

    def _test_secret(self, sec: str) -> bool:
        """Test if an app secret is valid.

        Args:
            sec: The app secret to test.

        Returns:
            True if the secret is valid, False otherwise.
        """
        try:
            # TODO: fix this and implement it on initialize of Connection
            self.request("track", 5, sec=sec)
            return True
        except InvalidAppSecretError:
            return False

    def _get_secrets(self) -> None:
        """Find and set a valid app secret from available secrets.

        Iterates through available secrets and tests each one until
        a valid one is found.

        Raises:
            InvalidAppSecretError: If no valid app secret is found.
        """
        for secret in self.secrets:
            if not secret:
                continue

            if self._test_secret(secret):
                self.sec = secret
                break

        if self.sec is None:
            raise InvalidAppSecretError("Can't find any valid app secret.\n")


class InvalidAppSecretError(BaseException):
    """Exception raised when the Qobuz app secret is invalid."""

    pass


class IneligibleError(BaseException):
    """Exception raised when the user's account is not eligible for downloads."""

    pass
