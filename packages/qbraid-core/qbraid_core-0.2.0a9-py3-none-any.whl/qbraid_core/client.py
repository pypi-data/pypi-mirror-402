# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining abstract base clas for qBraid micro-service clients.

"""
import re
import warnings
from typing import Any, Optional

from ._compat import check_version
from .config import load_config
from .exceptions import AuthError, RequestsApiError, ResourceNotFoundError, UserNotFoundError
from .sessions import QbraidSession, QbraidSessionV1


class QbraidClient:
    """Base class for qBraid micro-service clients."""

    def __init__(self, api_key: Optional[str] = None, session: Optional[QbraidSession] = None):
        if api_key and session:
            raise ValueError("Provide either api_key or session, not both.")

        self._user_metadata: Optional[dict[str, str]] = None
        self.session = session or QbraidSession(api_key=api_key)
        check_version("qbraid-core")

    @property
    def session(self) -> QbraidSession:
        """The QbraidSession used to make requests."""
        return self._session

    @session.setter
    def session(self, value: Optional[QbraidSession]) -> None:
        """Set the QbraidSession, ensuring it is a valid QbraidSession instance.

        Raises:
            AuthError: If the provided session is not valid.
            TypeError: If the value is not a QbraidSession instance.
        """
        session = value if value is not None else QbraidSession()

        if not isinstance(session, QbraidSession):
            raise TypeError("The session must be a QbraidSession instance.")

        try:
            user = session.get_user()
            self._user_metadata = {
                "organization": user.get("organization", "qbraid"),
                "role": user.get("role", "user"),
            }
            self._session = session
        except UserNotFoundError as err:
            raise AuthError(f"Access denied due to missing or invalid credentials: {err}") from err

    @staticmethod
    def _is_valid_object_id(candidate_id: str) -> bool:
        """
        Check if the provided string is a valid MongoDB ObjectId format.

        Args:
            candidate_id (str): The string to check.

        Returns:
            bool: True if the string is a valid ObjectId format, False otherwise.
        """
        try:
            return bool(re.match(r"^[0-9a-fA-F]{24}$", candidate_id))
        except (TypeError, SyntaxError):
            return False

    @staticmethod
    def _convert_email_symbols(email: str) -> Optional[str]:
        """Convert email to compatible string format"""
        return (
            email.replace("-", "-2d")
            .replace(".", "-2e")
            .replace("@", "-40")
            .replace("_", "-5f")
            .replace("+", "-2b")
        )

    def user_credits_value(self) -> float:
        """
        Get the current user's qBraid credits value.

        .. deprecated::
            Use :meth:`QbraidClientV1.user_credits_value` instead.

        Returns:
            float: The current user's qBraid credits value.
        """
        warnings.warn(
            "QbraidClient.user_credits_value() is deprecated. "
            "Use QbraidClientV1.user_credits_value() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            res = self.session.get("/billing/credits/get-user-credits").json()
            credits_value = res["qbraidCredits"]
            return float(credits_value)
        except (RequestsApiError, KeyError, ValueError) as err:
            raise ResourceNotFoundError(f"Credits value not found: {err}") from err


class QbraidClientV1:  # pylint: disable=too-few-public-methods
    """Base class for qBraid micro-service clients interfacing with the new
    qBraid API."""

    def __init__(self, api_key: Optional[str] = None, session: Optional[QbraidSessionV1] = None):
        if api_key and session:
            raise ValueError("Provide either api_key or session, not both.")

        self._user_metadata: Optional[dict[str, str]] = None
        self.session = session or QbraidSessionV1(api_key=api_key)
        check_version("qbraid-core")

    @property
    def session(self) -> QbraidSessionV1:
        """The QbraidSessionV1 used to make requests."""
        return self._session

    @session.setter
    def session(self, value: Optional[QbraidSessionV1]) -> None:
        """Set the QbraidSessionV1, ensuring it is a valid QbraidSessionV1 instance.

        Raises:
            AuthError: If the provided session is not valid.
            TypeError: If the value is not a QbraidSessionV1 instance.
        """
        session = value or QbraidSessionV1()

        if not isinstance(session, QbraidSessionV1):
            raise TypeError("The session must be a QbraidSessionV1 instance.")

        try:
            self._user_metadata = session.get_user_auth_metadata()
        except UserNotFoundError as err:
            raise AuthError(f"Access denied due to missing or invalid credentials: {err}") from err

        self._session = session

    @staticmethod
    def running_in_lab() -> bool:
        """Check if running in the qBraid Lab environment.

        Reads the 'cloud' setting from ~/.qbraid/qbraidrc config file.
        Only the "default" section is supported. The "cloud" value must be
        set to "true" (case-insensitive) for this method to return True.

        Returns:
            bool: True if running in qBraid Lab, False otherwise
        """
        try:
            config = load_config()
            if config.has_option("default", "cloud"):
                cloud_value = config.get("default", "cloud").strip().lower()
                return cloud_value == "true"
        except (FileNotFoundError, OSError, KeyError):
            # If config file doesn't exist or can't be read, assume not on Lab
            pass

        return False

    def get_credits_balance(self) -> dict[str, Any]:
        """Get the current user's credit balance for their organization.

        The balance is tied to the organization associated with the API key
        used for authentication.

        Returns:
            dict: Credit balance info with keys:
                - qbraidCredits (float): qBraid credit balance
                - awsCredits (float): AWS credit balance
                - autoRecharge (str): Auto-recharge status
                - organizationId (str): Organization ID
                - userId (str): User ID
        """
        org_id = self._user_metadata.get("organizationId")
        try:
            res = self.session.get("/billing/credits/balance", params={"organizationId": org_id})
            return res.json()["data"]
        except RequestsApiError as err:
            raise ResourceNotFoundError(f"Credits balance not found: {err}") from err

    def user_credits_value(self) -> float:
        """Get the current user's qBraid credits value.

        Returns:
            float: The current user's qBraid credits value.
        """
        try:
            balance = self.get_credits_balance()
            return float(balance["qbraidCredits"])
        except (KeyError, ValueError) as err:
            raise ResourceNotFoundError(f"Credits value not found: {err}") from err
