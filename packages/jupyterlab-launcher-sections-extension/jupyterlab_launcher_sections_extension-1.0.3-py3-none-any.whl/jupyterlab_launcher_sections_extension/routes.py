import json

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado

from .config import load_all_configs


class SectionConfigHandler(APIHandler):
    """Handler for section icon configuration endpoint."""

    # Cached config data (lazy loaded)
    _config_data = None
    _checked_data = False

    @tornado.web.authenticated
    def get(self):
        """Return section icon configurations."""
        if not SectionConfigHandler._checked_data:
            SectionConfigHandler._config_data = load_all_configs()
            SectionConfigHandler._checked_data = True

        self.finish(json.dumps({"sections": SectionConfigHandler._config_data or []}))


class HelloRouteHandler(APIHandler):
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": (
                "Hello, world!"
                " This is the '/jupyterlab-launcher-sections-extension/hello' endpoint."
                " Try visiting me in your browser!"
            ),
        }))


def setup_route_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]

    # Config endpoint
    config_route_pattern = url_path_join(
        base_url, "jupyterlab-launcher-sections-extension", "config"
    )

    # Hello endpoint (kept for testing)
    hello_route_pattern = url_path_join(
        base_url, "jupyterlab-launcher-sections-extension", "hello"
    )

    handlers = [
        (config_route_pattern, SectionConfigHandler),
        (hello_route_pattern, HelloRouteHandler),
    ]

    web_app.add_handlers(host_pattern, handlers)
