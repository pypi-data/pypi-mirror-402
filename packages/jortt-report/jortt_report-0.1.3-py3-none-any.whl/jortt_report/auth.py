"""OAuth authentication helper for Jortt API."""

import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class JorttAuth:
    """Handle OAuth authentication for Jortt API."""

    TOKEN_URL = "https://app.jortt.nl/oauth-provider/oauth/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scopes: Optional[str] = None,
    ):
        """Initialize Jortt OAuth client.

        Args:
            client_id: OAuth client ID. If not provided, reads from JORTT_CLIENT_ID env var.
            client_secret: OAuth client secret. If not provided, reads from JORTT_CLIENT_SECRET env var.
            scopes: Space-separated OAuth scopes. If not provided, reads from JORTT_SCOPES env var.
                   Common scopes: invoices:read invoices:write
        """
        self.client_id = client_id or os.getenv("JORTT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("JORTT_CLIENT_SECRET")
        self.scopes = scopes or os.getenv(
            "JORTT_SCOPES", "customers:read invoices:read invoices:write"
        )

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "JORTT_CLIENT_ID and JORTT_CLIENT_SECRET must be provided or set in environment"
            )

    def get_access_token(self) -> Dict[str, any]:
        """Fetch an access token using client credentials grant.

        Returns:
            Dictionary containing:
                - access_token: The bearer token to use for API requests
                - token_type: Should be "Bearer"
                - expires_in: Token lifetime in seconds
                - scope: Granted scopes

        Raises:
            requests.HTTPError: If the token request fails
        """
        data = {"grant_type": "client_credentials", "scope": self.scopes}

        response = requests.post(
            self.TOKEN_URL, data=data, auth=(self.client_id, self.client_secret)
        )

        response.raise_for_status()
        return response.json()


def fetch_token() -> str:
    """Helper function to fetch and return just the access token string.

    Returns:
        Access token string

    Raises:
        ValueError: If credentials are missing
        requests.HTTPError: If token request fails
    """
    auth = JorttAuth()
    token_response = auth.get_access_token()
    return token_response["access_token"]


if __name__ == "__main__":
    """Run this script to fetch and display an access token."""
    try:
        auth = JorttAuth()
        print(
            "Requesting access token from Jortt...\n"
            f"Client ID: {auth.client_id}\n"
            f"Scopes: {auth.scopes}\n"
        )

        token_data = auth.get_access_token()

        print(
            "✓ Successfully obtained access token!\n"
            "\n"
            "Token details:\n"
            f"  Token Type: {token_data.get('token_type')}\n"
            f"  Expires In: {token_data.get('expires_in')} seconds\n"
            f"  Scopes: {token_data.get('scope')}\n"
            "\n"
            "Access Token:\n"
            f"{token_data['access_token']}\n"
            "\n"
            "Add this to your .env file:\n"
            f"JORTT_ACCESS_TOKEN={token_data['access_token']}"
        )

    except ValueError as e:
        print(
            f"✗ Configuration error: {e}\n"
            "\n"
            "Make sure you have set JORTT_CLIENT_ID and JORTT_CLIENT_SECRET in your .env file"
        )
    except requests.HTTPError as e:
        print(
            f"✗ Authentication failed: {e}\n"
            f"Response: {e.response.text}\n"
            "\n"
            "Please check your credentials and try again"
        )
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
