"""Handler for validating qBraid credentials."""

import json
import sys
from pathlib import Path

import tornado
from jupyter_server.base.handlers import APIHandler
from qbraid_core import QbraidSessionV1


class ValidateConfigHandler(APIHandler):
    """Handler for validating stored qBraid credentials."""

    @tornado.web.authenticated
    async def get(self):
        """Validate the stored qBraid credentials.

        Returns:
            200: Credentials are valid
            404: No credentials file or API key found
            401: Invalid credentials
            500: Other API/server errors
        """
        import asyncio

        config_path = Path.home() / ".qbraid" / "qbraidrc"

        if not config_path.exists():
            self.set_status(404)
            self.finish(json.dumps({"status": "error", "message": "Credentials file not found"}))
            return

        try:
            session = QbraidSessionV1()
            api_key = session.api_key

            if not api_key:
                self.set_status(404)
                self.finish(json.dumps({"status": "error", "message": "No API key configured"}))
                return

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._validate_credentials, session)

            self.set_status(200)
            self.finish(json.dumps({"status": "valid", "message": "Credentials are valid"}))

        except PermissionError as e:
            print(f"Invalid credentials: {str(e)}", file=sys.stderr)
            self.set_status(401)
            self.finish(json.dumps({"status": "invalid", "message": "Invalid credentials"}))
        except Exception as e:
            print(f"Error validating credentials: {str(e)}", file=sys.stderr)
            self.set_status(500)
            self.finish(json.dumps({"status": "error", "message": str(e)}))

    @staticmethod
    def _validate_credentials(session: QbraidSessionV1) -> None:
        """Validate credentials against the API. Runs in thread pool."""
        session.get_user_auth_metadata()
