from __future__ import absolute_import, division, print_function

from six.moves.urllib.parse import quote_plus

from locker.error import CliRunError
from locker.ls_resources.abstract import ListableAPIResource, CreateableAPIResource, UpdateableAPIResource, \
    DeletableAPIResource, DetailableAPIResource


class Environment(ListableAPIResource, DetailableAPIResource,
                  CreateableAPIResource, UpdateableAPIResource, DeletableAPIResource):

    OBJECT_NAME = "environment"

    @classmethod
    def get_environment(cls, name, access_key_id=None, secret_access_key=None, api_base=None, api_version=None, **params):
        """
        Get Environment object by name
        :param name:
        :param access_key_id:
        :param secret_access_key:
        :param api_base:
        :param api_version:
        :param params:
        :return:
        """
        base = cls.class_cli()
        cli_ = [f"{base}", "get", "--name", f"{name}"]
        instance = cls(None, access_key_id, secret_access_key, **params)
        try:
            instance._call_and_refresh(
                cli_, access_key_id=access_key_id, secret_access_key=secret_access_key,
                api_base=api_base, api_version=api_version, params=params
            )
        except CliRunError as e:
            # TODO: Change the return result when not found the environment
            return None
        return instance

    @classmethod
    def retrieve_environment(cls, name, access_key_id=None, secret_access_key=None, api_base=None, api_version=None,
                             **params):
        """
        Get Environment object by name
        :param name:
        :param access_key_id:
        :param secret_access_key:
        :param api_base:
        :param api_version:
        :param params:
        :return:
        """
        base = cls.class_cli()
        cli_ = [f"{base}", "get", "--name", f"{name}"]
        instance = cls(None, access_key_id, secret_access_key, **params)
        # try:
        instance._call_and_refresh(
            cli_, access_key_id=access_key_id, secret_access_key=secret_access_key,
            api_base=api_base, api_version=api_version, params=params
        )
        # except CliRunError as e:
        #     # TODO: Handle exception
        #     return None
        return instance

    @classmethod
    def modify(cls, **params):
        name = params.get("name")
        cli = [f"{cls.class_cli()}", "update", "--name", f"{quote_plus(name)}"]

        if "external_url" in params:
            cli += ["--new-url", f"{params.get('external_url')}"]
        # if "new_name" in params:
        #     cli += ["--new-name", f"{params.get('new_name')}"]
        # if "new_description" in params:
        #     cli += ["--new-description", f"{params.get('new_description')}"]

        return cls._static_call(cli, params=params)

    @classmethod
    def create(cls, access_key_id=None, secret_access_key=None, api_base=None, api_version=None, **params):
        cli = [f"{cls.class_cli()}", "create"]
        if "external_url" in params:
            cli += ["--url", f"{params.get('external_url')}"]
        return cls._static_call(
            cli,
            access_key_id,
            secret_access_key,
            api_base=api_base,
            api_version=api_version,
            params=params,
        )
