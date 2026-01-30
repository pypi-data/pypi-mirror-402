from typing import Dict, Any, Optional

from gunicorn.app.wsgiapp import WSGIApplication  # type: ignore


class UnicLabWSGIApplication(WSGIApplication):
    def __init__(self, app_uri: str, options: Optional[Dict[str, Any]] = None) -> None:
        self.options = options or {}
        self.app_uri = app_uri
        super().__init__()

    def load_config(self) -> None:
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self) -> str:
        return self.app_uri
