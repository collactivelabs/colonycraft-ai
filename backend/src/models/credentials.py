import json
import os
from typing import Optional
from google.oauth2 import service_account
from google.auth.credentials import Credentials
from ..core.config import get_settings

settings = get_settings()

class CredentialManager:
    _instance: Optional['CredentialManager'] = None
    _credentials: Optional[Credentials] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def credentials(self) -> Credentials:
        if not self._credentials:
            self._load_credentials()
        return self._credentials

    def _load_credentials(self) -> None:
        creds_path = os.path.expandvars(settings.GOOGLE_APPLICATION_CREDENTIALS)
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Credentials file not found: {creds_path}")

        try:
            self._credentials = service_account.Credentials.from_service_account_file(
                creds_path
            )
        except Exception as e:
            raise ValueError(f"Failed to load credentials: {str(e)}")