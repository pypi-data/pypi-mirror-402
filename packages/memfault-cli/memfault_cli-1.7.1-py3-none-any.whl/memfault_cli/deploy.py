import logging
from typing import Dict, Tuple, Union

import click
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # pyright: ignore[reportMissingModuleSource]

from .authenticator import Authenticator
from .context import MemfaultCliClickContext

log = logging.getLogger(__name__)


class Deployer:
    def __init__(self, *, ctx: MemfaultCliClickContext, authenticator: Authenticator):
        self.ctx: MemfaultCliClickContext = ctx
        self.authenticator: Authenticator = authenticator
        self.session = self._create_requests_session()

    @staticmethod
    def _create_requests_session() -> Session:
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,  # Sleep for 2s, 4s, 8s, 16s, 32s, Stop
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @property
    def base_url(self) -> str:
        return self.ctx.api_url

    def _api_base_url(self) -> str:
        return f"{self.base_url}/api/v0"

    def _projects_base_url(self) -> str:
        return f"{self.base_url}/api/v0/organizations/{self.ctx.org}/projects/{self.ctx.project}"

    @property
    def deployment_url(self) -> str:
        """
        The upload URL for a 'prepared upload' for the configured authentication method.
        """
        return f"{self._projects_base_url()}/deployments"

    def deploy(
        self, *, release_version: Union[str, Tuple[str, str]], cohort: str, rollout_percent: int
    ) -> None:
        deployment_type = "normal" if rollout_percent == 100 else "staged_rollout"
        json_d: Dict[str, Union[str, Tuple[str, str], int]] = {
            "type": deployment_type,
            "release": release_version,
            "cohort": cohort,
        }

        if deployment_type == "staged_rollout":
            json_d["rollout_percent"] = rollout_percent

        response = self.session.post(
            self.deployment_url, json=json_d, **self.authenticator.requests_auth_params()
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Request failed with HTTP status {response.status_code}\nResponse"
                f" body:\n{response.content.decode()}"
            )
        log.info("Release %s successfully deployed to Cohort %s", release_version, cohort)

    def deactivate(self, *, release_version: Union[str, Tuple[str, str]], cohort: str) -> None:
        """
        Deactivate the specified release for the cohort, if it is currently active.
        """
        # First, query to see if there is a single active deployment that matches the version and cohort.
        if isinstance(release_version, str):
            release_params = {"release": release_version}
        elif isinstance(release_version, tuple):
            release_params = {"delta_from": release_version[0], "delta_to": release_version[1]}
        else:
            raise click.exceptions.UsageError(
                f"Invalid release version specified ({release_version})"
            )

        response = self.session.get(
            f"{self._projects_base_url()}/deployments",
            **self.authenticator.requests_auth_params(),
            params={"cohort": cohort, **release_params},
        )

        if response.status_code >= 400:
            raise click.exceptions.UsageError(
                f"Request failed with HTTP status {response.status_code}\nResponse"
                f" body:\n{response.content.decode()}"
            )

        active_deployments_list = [
            deployment
            for deployment in response.json()["data"]
            if deployment["status"] == "in_progress" or deployment["status"] == "done"
        ]

        if len(active_deployments_list) == 0:
            raise click.exceptions.UsageError(
                f"Could not find an active deployment for cohort {cohort} with version {release_version},"
                f" performing no action"
            )
        elif len(active_deployments_list) > 1:
            raise click.exceptions.UsageError(
                f"Found multiple matching active deployments for cohort {cohort} with version {release_version},"
                f" performing no action"
            )

        active_deployment = active_deployments_list[0]

        # Now, deactivate the deployment.
        deployment_url = f"{self._projects_base_url()}/deployments/{active_deployment['id']}"
        response = self.session.delete(deployment_url, **self.authenticator.requests_auth_params())
        if response.status_code >= 400:
            raise click.exceptions.UsageError(
                f"Request failed with HTTP status {response.status_code}\nResponse"
                f" body:\n{response.content.decode()}"
            )
        log.info("Release %s successfully deactivated from Cohort %s", release_version, cohort)
