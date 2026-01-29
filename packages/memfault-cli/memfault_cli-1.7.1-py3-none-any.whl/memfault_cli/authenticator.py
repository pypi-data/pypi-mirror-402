import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .context import MemfaultCliClickContext


log = logging.getLogger(__name__)


class Authenticator:
    def __init__(self, ctx: "MemfaultCliClickContext"):
        self.ctx = ctx

    @staticmethod
    @abstractmethod
    def project_key_auth() -> bool:
        pass

    @classmethod
    @abstractmethod
    def required_args(cls) -> List[str]:
        pass

    @abstractmethod
    def requests_auth_params(self) -> dict:
        pass


class ProjectKeyAuthenticator(Authenticator):
    """
    Project Key Authentication with the Memfault service (Memfault-Project-Key)
    """

    @staticmethod
    def project_key_auth() -> bool:
        return True

    @classmethod
    def required_args(cls) -> List[str]:
        return [
            "project_key",
        ]

    def requests_auth_params(self) -> dict:
        return {"headers": {"Memfault-Project-Key": self.ctx.project_key}}


class BasicAuthenticator(Authenticator):
    """
    Basic Authentication with the Memfault service

    Various ways a user can authenticate:
    - Email + Password
    - Email + User API Key
    - DEPRECATED: Organization Auth Token (passed in as password) -- --org-token should be used instead
    """

    def __init__(self, ctx: "MemfaultCliClickContext") -> None:
        super().__init__(ctx)
        if not self.ctx.obj.get("email") and self.ctx.password.startswith("oat_"):
            log.warning(
                "Please use --org-token instead of --password to pass organization auth token"
            )

    @staticmethod
    def project_key_auth() -> bool:
        return False

    @classmethod
    def required_args(cls) -> List[str]:
        return [
            "org",
            "project",
            "password",
        ]

    def requests_auth_params(self) -> dict:
        # Email can be None in the case of using Organization auth tokens (prefixed with oat_*)
        auth = (self.ctx.obj.get("email") or "", self.ctx.password)
        return {"auth": auth}


class OrgTokenAuthenticator(Authenticator):
    """
    Org Token Authentication with the Memfault service, passed in with --org-token
    """

    @staticmethod
    def project_key_auth() -> bool:
        return False

    @classmethod
    def required_args(cls) -> List[str]:
        return [
            "org",
            "org_token",
            "project",
        ]

    def requests_auth_params(self) -> dict:
        auth = ("", self.ctx.org_token)
        return {"auth": auth}
