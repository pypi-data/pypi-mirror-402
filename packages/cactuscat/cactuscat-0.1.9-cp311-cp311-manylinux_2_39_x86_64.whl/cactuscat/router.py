import re
import logging
from typing import Dict, Any, Callable, Optional, List, Union

logger = logging.getLogger("CactusCat.Router")

class Router:
    """
    Handles deep linking and custom protocol routing (e.g., myapp://profile/123).
    """
    def __init__(self):
        self.routes: Dict[str, Dict[str, Any]] = {}
        self.protocol: Optional[str] = None

    def add_route(self, pattern: str, callback: Callable):
        """
        Adds a route with named parameters.
        Example: /user/{id}/profile
        """
        # Convert {param} to (?P<param>[^/]+)
        regex_pattern = re.escape(pattern)
        regex_pattern = re.sub(r"\\{([a-zA-Z0-9_]+)\\}", r"(?P<\1>[^/]+)", regex_pattern)
        
        # Ensure it matches the whole string
        regex_pattern = f"^{regex_pattern}$"
        
        self.routes[pattern] = {
            "regex": re.compile(regex_pattern),
            "callback": callback
        }
        logger.debug(f"Registered route: {pattern} -> {regex_pattern}")

    def resolve(self, url: str) -> Optional[Any]:
        """
        Resolves a URL string against registered routes.
        Returns the result of the callback if matched.
        """
        # Strip protocol if present
        path = url
        if "://" in url:
            path = url.split("://", 1)[1]
        
        # Strip trailing slash
        if path.endswith("/"):
            path = path[:-1]
            
        for pattern, info in self.routes.items():
            match = info["regex"].match(path)
            if match:
                kwargs = match.groupdict()
                logger.info(f"Route matched: {pattern} with {kwargs}")
                return info["callback"](**kwargs)
        
        logger.warning(f"No route matched for: {url}")
        return None

    def set_protocol(self, protocol: str):
        """Sets the custom protocol name (e.g. 'myapp')."""
        self.protocol = protocol
        
    def handle_protocol_launch(self, args: List[str]):
        """Checks if the app was launched with a deep link and routes it."""
        if not self.protocol:
            return
            
        search_str = f"{self.protocol}://"
        for arg in args:
            if arg.startswith(search_str):
                return self.resolve(arg)
