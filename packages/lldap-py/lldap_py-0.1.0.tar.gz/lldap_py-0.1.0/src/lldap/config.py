
from typing import Optional, Dict
from .exceptions import ConfigurationError


class Config:
    def __init__(
        self,
        http_url: Optional[str] = "http://localhost:17170",
        username: Optional[str] = "admin",
        password: Optional[str] = None,
        token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        user_dn: Optional[str] = None,
        ldap_server: Optional[str] = None,
        endpoints: Optional[Dict[str, str]] = None,
    ):

        self.http_url = http_url
        self.username = username
        self.password = password
        self.token = token
        self.refresh_token = refresh_token
        self.user_dn = user_dn
        self.ldap_server = ldap_server
        self.endpoints = endpoints or {
            "auth": "/auth/simple/login",
            "graphql": "/api/graphql",
            "logout": "/auth/logout",
            "refresh": "/auth/refresh",
        }

    def validate(self) -> None:
        """Validate that required configuration is present."""
        has_token = bool(self.token)
        has_credentials = bool(self.username and self.password)
        has_refresh = bool(self.refresh_token)

        if not (has_token or has_credentials or has_refresh):
            raise ConfigurationError(
                "Missing authentication: provide either token, refresh_token, or username+password"
            )

    def get_endpoint_url(self, endpoint: str) -> str:
        """Get full URL for an endpoint."""
        return f"{self.http_url}{self.endpoints[endpoint]}"
