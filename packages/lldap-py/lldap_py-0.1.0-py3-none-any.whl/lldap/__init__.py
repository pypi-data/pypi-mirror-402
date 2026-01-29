"""LLDAP-py - Simple Python interface for managing LLDAP servers."""

__version__ = "0.1.0"

from .config import Config
from .client import LLDAPClient
from .users import UserManager
from .groups import GroupManager
from .exceptions import LLDAPError, AuthenticationError, ConnectionError, GraphQLError, ValidationError


class LLDAPManager(UserManager, GroupManager):
    """Simplified LLDAP manager combining user and group management.
    
    This is the main interface for interacting with LLDAP servers.
    Pass connection values in the constructor and use methods for operations.
    """
    
    def __init__(
        self,
        http_url: str, # (http(s)://<host>:<port>)
        username: str = None,
        password: str = None,
        token: str = None,
        refresh_token: str = None,
    ):
        """Initialize LLDAP Manager with connection details.
        
        Args:
            http_url: HTTP URL of LLDAP server (e.g., "http://localhost:17170")
            username: Admin username (default: "admin")
            password: Admin password
            token: Authentication token (if already authenticated)
            refresh_token: Refresh token for token renewal
            
        Raises:
            AuthenticationError: If connection/authentication fails
        """
        self.config = Config(
            http_url=http_url,
            username=username,
            password=password,
            token=token,
            refresh_token=refresh_token,
        )
        
        try:
            self.config.validate()
        except LLDAPError:
            raise
        
        self.client = LLDAPClient(self.config)
        
        # Authenticate on initialization
        try:
            self.client.authenticate()
        except (AuthenticationError, ConnectionError):
            raise
    
    def close(self):
        """Close the session."""
        if hasattr(self.client, 'session'):
            self.client.session.close()


__all__ = [
    "LLDAPManager",
    "LLDAPClient",
    "LLDAPError",
    "UserManager",
    "GroupManager",
    "AuthenticationError",
    "ConnectionError",
    "ValidationError",
    "GraphQLError",
]
