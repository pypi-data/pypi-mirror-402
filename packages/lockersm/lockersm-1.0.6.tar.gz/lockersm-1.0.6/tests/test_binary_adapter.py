import json
import os
import sys

from dotenv import load_dotenv
from locker.binary_adapter import BinaryAdapter
from locker.error import ResourceNotFoundError


class TestBinaryAdapter(object):
    @staticmethod
    def init_binary_adapter():
        load_dotenv()
        access_key_id = os.getenv('ACCESS_KEY_ID')
        secret_access_key = os.getenv('SECRET_ACCESS_KEY')
        binary_adapter = BinaryAdapter(
            api_base="https://api.locker.io/locker_secrets",
            access_key_id=access_key_id, secret_access_key=secret_access_key
        )
        return binary_adapter

    def test_get_platform(self):
        binary_adapter = self.init_binary_adapter()
        platform = binary_adapter.get_platform()
        assert platform == sys.platform

    def test_get_sdk_version(self):
        binary_adapter = self.init_binary_adapter()
        sdk_version = binary_adapter.get_sdk_version()
        assert isinstance(sdk_version, str) and len(sdk_version.split(".")) == 3

    def test_call(self):
        binary_adapter = self.init_binary_adapter()
        cli = ["secret", "list"]
        secrets = binary_adapter.call(cli)
        assert isinstance(secrets, list)
        for secret in secrets:
            assert isinstance(secret, dict)
            assert isinstance(secret.get('key'), str)
            assert isinstance(secret.get('value'), str)
            assert isinstance(secret.get('description'), str) or isinstance(secret.get('description'), None)

    def test_interpret_response(self):
        binary_adapter = self.init_binary_adapter()
        error_body = {
            "object": "error",
            "error": "not_found",
            "message": "Not found the resource"
        }
        error_body_raw = json.dumps(error_body)
        try:
            exc = binary_adapter.interpret_response(error_body_raw)
        except ResourceNotFoundError:
            pass