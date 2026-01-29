import platform

import requests
import requests.utils
from requests.models import PreparedRequest

from ._version import version as __version__

# Monkey patch requests to always include a User-Agent header. All our requests
# use either default_headers()   or PreparedRequest objects.

# Format user-agent based on
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent#firefox_ua_string
DEFAULT_USER_AGENT = f"MemfaultCLI/{__version__} ({platform.platform(terse=True)})"


# Match positional args of the original method.
def prepare_request(self, method=None, url=None, headers=None, files=None, *args, **kwargs):
    headers = headers or {}
    headers["User-Agent"] = DEFAULT_USER_AGENT
    return self._prepare(method, url, headers, files, *args, **kwargs)


# Save the original prepare method so we can call it from our monkey-patched
# version.
PreparedRequest._prepare = PreparedRequest.prepare  # pyright: ignore[reportAttributeAccessIssue]
PreparedRequest.prepare = prepare_request
requests.utils.default_user_agent = lambda: DEFAULT_USER_AGENT


__all__ = [
    "__version__",
]
