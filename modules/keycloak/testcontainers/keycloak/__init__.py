#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import os
from typing import Optional

import requests

from keycloak import KeycloakAdmin
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_container_is_ready


class KeycloakContainer(DockerContainer):
    """
    Keycloak container.

    Example:

        .. doctest::

            >>> from testcontainers.keycloak import KeycloakContainer

            >>> with KeycloakContainer() as kc:
            ...    keycloak = kc.get_client()
    """

    def __init__(
        self,
        image="quay.io/keycloak/keycloak:latest",
        username: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 8080,
    ) -> None:
        super().__init__(image=image)
        self.username = username or os.environ.get("KEYCLOAK_ADMIN", "test")
        self.password = password or os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "test")
        self.port = port
        self.with_exposed_ports(self.port)

    def _configure(self) -> None:
        self.with_env("KEYCLOAK_ADMIN", self.username)
        self.with_env("KEYCLOAK_ADMIN_PASSWORD", self.password)
        self.with_command("start-dev")

    def get_url(self) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self.port)
        return f"http://{host}:{port}"

    @wait_container_is_ready(requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout)
    def _connect(self) -> None:
        response = requests.get(self.get_url(), timeout=1)
        response.raise_for_status()

    def start(self) -> "KeycloakContainer":
        self._configure()
        super().start()
        self._connect()
        return self

    def get_client(self, **kwargs) -> KeycloakAdmin:
        default_kwargs = {
            "server_url": self.get_url(),
            "username": self.username,
            "password": self.password,
            "realm_name": "master",
            "verify": True,
        }
        kwargs = {**default_kwargs, **kwargs}
        return KeycloakAdmin(**kwargs)
