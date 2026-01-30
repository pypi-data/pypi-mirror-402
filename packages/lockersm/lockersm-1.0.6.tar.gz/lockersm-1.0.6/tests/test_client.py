import os
import pytest
from dotenv import load_dotenv

import locker.error
from locker.client import Locker
from locker.ls_resources import Secret, Environment


class TestClient(object):
    @staticmethod
    def init_client():
        load_dotenv()
        access_key_id = os.getenv("ACCESS_KEY_ID")
        secret_access_key = os.getenv("SECRET_ACCESS_KEY")
        client = Locker(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
        )
        return client

    def test_init_client(self):
        client = self.init_client()
        access_key_id = os.getenv("ACCESS_KEY_ID")
        secret_access_key = os.getenv("SECRET_ACCESS_KEY")
        assert client.access_key_id == access_key_id
        assert client.secret_access_key == secret_access_key

    def test_secrets(self):
        client = self.init_client()
        if not client.access_key_id or not client.secret_access_key:
            return

        # Test create secret
        test_key = "SDK_TEST_CLIENT"
        test_value = "SDK_TEST_VALUE"
        try:
            new_secret = client.create(key=test_key, value=test_value)
        except locker.error.APIConnectionError:
            new_secret = client.retrieve(key=test_key)
            test_value = new_secret.value
        assert new_secret.key == test_key and new_secret.value == test_value, "The creation secret is invalid"

        # Test list secrets
        secrets = client.list()
        for secret in secrets:
            assert isinstance(secret, Secret)
            assert isinstance(secret.key, str)
            assert isinstance(secret.value, str)
            assert isinstance(secret.description, str) or isinstance(secret.description, None)

        # Test get secret
        secret_value = client.get(key=test_key)
        assert secret_value == test_value and isinstance(secret_value, str)
        secret_value = client.get_secret(key=test_key)
        assert secret_value == test_value and isinstance(secret_value, str)

        # Test retrieve secret
        secret = client.retrieve(key=test_key)
        assert hasattr(secret, "id") and hasattr(secret, "key") and hasattr(secret, "value")
        assert hasattr(secret, "secret_hash")
        assert hasattr(secret, "environment_name") and hasattr(secret, "environment_hash") and \
               hasattr(secret, "environment_id")
        assert secret.key == test_key and secret.value == test_value

        # Test modify the secret
        new_test_value = "SDK_TEST_VALUE_UPDATED"
        secret = client.modify(key=test_key, value=new_test_value)
        assert secret.value == new_test_value

    def test_environments(self):
        client = self.init_client()
        if not client.access_key_id or not client.secret_access_key:
            return

        # Test create env
        test_name = "sdk_env"
        test_external_url = "sdk_env.example.com"
        try:
            new_environment = client.create_environment(name=test_name, external_url=test_external_url)
        except locker.error.APIConnectionError:
            new_environment = client.retrieve_environment(name=test_name)
            test_external_url = new_environment.external_url
        assert new_environment.name == test_name and new_environment.external_url == test_external_url

        # Test list environments
        environments = client.list_environments()
        for environment in environments:
            assert isinstance(environment, Environment)
            assert isinstance(environment.name, str)
            assert isinstance(environment.external_url, str) or environment.external_url is None
            assert isinstance(environment.description, str) or environment.description is None

        # Test get env
        env = client.get_environment(name=test_name)
        assert env.external_url == test_external_url and isinstance(env.external_url, str)

        # Test retrieve secret
        env = client.retrieve_environment(name=test_name)
        assert hasattr(env, "id") and hasattr(env, "name") and hasattr(env, "external_url")
        assert hasattr(env, "hash")
        assert env.name == test_name and env.external_url == test_external_url

        # Test modify the secret
        new_test_external_url = "new_sdk_env.example.com"
        secret = client.modify_environment(name=test_name, external_url=new_test_external_url)
        assert secret.external_url == new_test_external_url

    def test_secrets_with_env(self):
        client = self.init_client()
        if not client.access_key_id or not client.secret_access_key:
            return
        # Test create secret with env
        test_env_name = "test"
        test_env_external_url = "test.locker.io"
        try:
            new_environment = client.create_environment(name=test_env_name, external_url=test_env_external_url)
        except locker.error.APIConnectionError:
            new_environment = client.retrieve_environment(name=test_env_name)
            test_env_external_url = new_environment.external_url
        assert new_environment.name == test_env_name and new_environment.external_url == test_env_external_url

        general_key = "GENERAL_SDK_KEY"
        general_value = "GENERAL_SDK_VALUE"
        test_key = "TEST_SDK_KEY"
        test_value = "TEST_SDK_VALUE"
        try:
            general_secret = client.create(key=general_key, value=general_value)
        except locker.error.APIConnectionError:
            general_secret = client.retrieve(key=general_key)
            general_value = general_secret.value
        assert (general_secret.key == general_key and
                general_secret.value == general_value), "The creation general secret is invalid"

        try:
            test_secret = client.create(key=test_key, value=test_value, environment=test_env_name)
        except locker.error.APIConnectionError:
            test_secret = client.retrieve(key=test_key, environment_name=test_env_name)
            test_value = test_secret.value
        assert (test_secret.key == test_key and
                test_secret.value == test_value), "The creation test secret is invalid"

        # Get general and test secret
        test_general_secret = client.get(key=general_key, environment_name=test_env_name)
        assert test_general_secret == general_value
        t_secret = client.get(key=test_key, environment_name=test_env_name)
        assert t_secret == test_value
