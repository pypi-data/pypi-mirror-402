"""Exception classes for LLDAP."""


class LLDAPError(Exception):
    """Base exception for all LLDAP errors."""
    pass


class AuthenticationError(LLDAPError):
    """Raised when authentication fails."""
    pass


class ConnectionError(LLDAPError):
    """Raised when connection to LLDAP server fails."""
    pass


class GraphQLError(LLDAPError):
    """Raised when GraphQL query returns an error."""
    pass


class ConfigurationError(LLDAPError):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(LLDAPError):
    """Raised when input validation fails."""
    pass
