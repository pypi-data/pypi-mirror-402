"""
Constantes partagées pour le client Rundeck.
"""

# Package metadata
__version__ = "0.1.0"

# Auth
RUNDECK_AUTH_HEADER = "X-Rundeck-Auth-Token"

# HTTP methods
HTTP_GET = "GET"
HTTP_POST = "POST"
HTTP_PUT = "PUT"
HTTP_DELETE = "DELETE"

# Content / formats
FORMAT_JSON = "json"

# API versions (cf. docs Rundeck: current 56, minimum 14, dépréciation 17)
API_VERSION_CURRENT = "56"
API_VERSION_MIN = "14"
API_VERSION_DEPRECATION = "17"

# Defaults
DEFAULT_API_VERSION = API_VERSION_CURRENT
DEFAULT_TIMEOUT = 30
USER_AGENT = "python-rundeck"


__all__ = [
    "__version__",
    "API_VERSION_CURRENT",
    "API_VERSION_DEPRECATION",
    "API_VERSION_MIN",
    "DEFAULT_API_VERSION",
    "DEFAULT_TIMEOUT",
    "FORMAT_JSON",
    "HTTP_DELETE",
    "HTTP_GET",
    "HTTP_POST",
    "HTTP_PUT",
    "RUNDECK_AUTH_HEADER",
    "USER_AGENT",
]
