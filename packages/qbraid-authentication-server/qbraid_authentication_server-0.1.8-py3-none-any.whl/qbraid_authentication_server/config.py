import configparser
import json
import sys
from pathlib import Path
from typing import Optional, Union

import tornado
from jupyter_server.base.handlers import APIHandler
from qbraid_core import QbraidSessionV1


class UserConfigHandler(APIHandler):
    """Handler for managing user configurations and other local data."""

    @tornado.web.authenticated
    def get(self):
        """Get user's qBraid credentials."""
        config = self.get_config()

        self.finish(json.dumps(config))

    @tornado.web.authenticated
    async def post(self):
        """Update user's qBraid credentials.

        Request body:
            apiKey (str, optional): The API key to save
            url (str, optional): The API URL
            cloud (bool, optional): Cloud mode flag
            validate (bool, optional): Whether to validate credentials after saving. Defaults to True.
        """
        try:
            data: dict = json.loads(self.request.body.decode("utf-8"))
            validate = data.get("validate", True)

            # Save all fields to qbraidrc FIRST (so QbraidSessionV1 can read url from config)
            self._update_additional_config(
                api_key=data.get("apiKey"),
                url=data.get("url"),
                cloud=data.get("cloud"),
            )

            # Optionally validate - QbraidSessionV1 will read url from qbraidrc
            # Run in executor to avoid blocking the event loop
            api_key = data.get("apiKey")
            if validate and api_key:
                import asyncio

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._validate_credentials, api_key)

            config = self.get_config()
            self.finish(json.dumps({"status": "success", "config": config}))
        except Exception as e:
            print(f"Error while updating user configuration: {str(e)}", file=sys.stderr)
            self.finish(json.dumps({"status": "error", "message": str(e)}))

    @staticmethod
    def _validate_credentials(api_key: str) -> None:
        """Validate credentials against the API. Runs in thread pool."""
        session = QbraidSessionV1(api_key)
        session.get_user_auth_metadata()

    @staticmethod
    def _update_additional_config(
        api_key: Optional[str] = None,
        url: Optional[str] = None,
        cloud: Optional[bool] = None,
    ) -> None:
        """Update fields in qbraidrc."""
        config_path = Path.home() / ".qbraid" / "qbraidrc"
        config = configparser.ConfigParser()

        if config_path.exists():
            config.read(config_path)

        section = "default"
        if section not in config.sections():
            config.add_section(section)

        if api_key is not None:
            config.set(section, "api-key", api_key)
        if url is not None:
            config.set(section, "url", url)
        if cloud is not None:
            config.set(section, "cloud", str(cloud).lower())

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            config.write(f)

    @staticmethod
    def get_config() -> dict[str, Optional[Union[str, bool]]]:
        """
        Retrieve the user's qBraid credentials.

        Returns:
            A dictionary containing user configuration details.
        """
        try:
            session = QbraidSessionV1()

            # TODO: Load config once. Currently reads file every time get_config is called.
            cloud_config = session.get_config("cloud")
            cloud = None if cloud_config is None else cloud_config.lower() == "true"
            config: dict[str, Optional[Union[str, bool]]] = {
                "apiKey": session.get_config("api-key"),
                "url": session.get_config("url"),
                "cloud": cloud,
            }

            return config
        except Exception as e:
            print(f"Error while retrieving user configuration: {str(e)}", file=sys.stderr)
            return {
                "apiKey": None,
                "url": None,
                "cloud": None,
            }
