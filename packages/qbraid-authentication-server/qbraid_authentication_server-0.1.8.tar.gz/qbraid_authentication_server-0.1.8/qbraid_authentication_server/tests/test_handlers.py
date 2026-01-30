import json
from unittest.mock import patch

from qbraid_authentication_server.config import UserConfigHandler


async def test_get_config(jp_fetch):
    """Test the get config endpoint"""
    # Mock QbraidSessionV1 to return None for all config values
    with patch.object(
        UserConfigHandler, "get_config", return_value={"apiKey": None, "url": None, "cloud": None}
    ):
        response = await jp_fetch("qbraid-authentication-server", "qbraid-config")

        assert response.code == 200
        payload = json.loads(response.body)
        assert payload == {
            "apiKey": None,
            "url": None,
            "cloud": None,
        }
