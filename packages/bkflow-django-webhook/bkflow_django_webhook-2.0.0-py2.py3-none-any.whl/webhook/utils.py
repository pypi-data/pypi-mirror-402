# -*- coding: utf-8 -*-
import base64
import json

from cryptography.fernet import Fernet
from django.conf import settings

from webhook.config import webhook_settings

CRYPT_SECRET_KEY = getattr(settings, "PRIVATE_SECRET", None) or settings.SECRET_KEY
KEY_LENGTH = webhook_settings.KEY_LENGTH


class SecretFieldProcessor:
    def __init__(self):
        key = CRYPT_SECRET_KEY.encode()
        if len(key) < KEY_LENGTH:
            key = key.ljust(KEY_LENGTH, b"\0")
        elif len(key) > KEY_LENGTH:
            key = key[:KEY_LENGTH]
        self.key = base64.urlsafe_b64encode(key)
        self.cipher = Fernet(self.key)

    def decrypt_value(self, value, expression=None, connection=None):
        if not value:
            return None
        try:
            return self.cipher.decrypt(value.encode()).decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt value: {e}")

    def encrypt_value(self, value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        try:
            return self.cipher.encrypt(value.encode()).decode()
        except Exception as e:
            raise ValueError(f"Failed to encrypt value: {e}")


def process_sensitive_info(extra_info, is_decrypt=False):
    secret_field = SecretFieldProcessor()
    secret_func = secret_field.decrypt_value if is_decrypt else secret_field.encrypt_value
    if isinstance(extra_info, dict):
        headers = extra_info.get("headers")
        if headers is not None and isinstance(headers, (dict, list)):
            for header in headers:
                header["value"] = secret_func(header["value"])

        if "authorization" in extra_info:
            auth = extra_info["authorization"]
            auth["token"] = secret_func(auth["token"])
            auth["password"] = secret_func(auth["password"])

    return extra_info
