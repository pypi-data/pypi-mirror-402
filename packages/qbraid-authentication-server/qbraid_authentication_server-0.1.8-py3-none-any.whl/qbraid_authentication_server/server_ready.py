"""Handler for checking if the server is ready (qbraidrc synced)."""

import json
import sys
from pathlib import Path

import tornado
from jupyter_server.base.handlers import APIHandler


class ServerReadyHandler(APIHandler):
    """Handler for checking if the server credentials have been synced."""

    @tornado.web.authenticated
    def get(self):
        """Check if ~/.hotdog file exists (indicates priority restore complete).

        Returns:
            200: Server is ready (file exists)
            503: Server not ready (file not found)
            500: Error checking file
        """
        try:
            sync_file = Path.home() / ".hotdog"

            if sync_file.exists():
                self.set_status(200)
                self.finish(json.dumps({"status": "ready", "message": "Server credentials synced"}))
            else:
                self.set_status(503)
                self.finish(
                    json.dumps(
                        {"status": "not_ready", "message": "Server credentials not yet synced"}
                    )
                )
        except Exception as e:
            print(f"Error checking server ready status: {str(e)}", file=sys.stderr)
            self.set_status(500)
            self.finish(json.dumps({"status": "error", "message": str(e)}))
