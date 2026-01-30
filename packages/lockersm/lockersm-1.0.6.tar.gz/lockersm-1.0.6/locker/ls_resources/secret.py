from __future__ import absolute_import, division, print_function


from locker.error import CliRunError
from locker.ls_resources.abstract import ListableAPIResource, CreateableAPIResource, UpdateableAPIResource, \
    DeletableAPIResource


class Secret(ListableAPIResource, CreateableAPIResource, UpdateableAPIResource, DeletableAPIResource):
    OBJECT_NAME = "secret"

    @classmethod
    def get_secret(cls, key, environment_name=None, default_value=None,
                   access_key_id=None, secret_access_key=None, api_base=None, api_version=None, **params):
        base = cls.class_cli()
        cli_ = [base, 'get', '--key', f'{key}']
        if environment_name:
            cli_ += ['--environment', f'{environment_name}']
        instance = cls(None, access_key_id, secret_access_key, **params)
        try:
            instance._call_and_refresh(
                cli_, access_key_id=access_key_id, secret_access_key=secret_access_key,
                api_base=api_base, api_version=api_version, params=params
            )
        except CliRunError as e:
            # logging.warning(f"[!] CliRunError when get_secret of {key}. So return default value is {default_value}\n"
            #                 f"Error: {e.code} - {e.user_message} ")
            return default_value
        try:
            return instance.value
        except AttributeError:
            return default_value

    @classmethod
    def retrieve_secret(cls, key, environment_name=None,
                        access_key_id=None, secret_access_key=None, api_base=None, api_version=None, **params):
        base = cls.class_cli()
        cli_ = [base, 'get', '--key', f'{key}']
        if environment_name:
            cli_ += ['--environment', f'{environment_name}']
        instance = cls(None, access_key_id, secret_access_key, **params)
        instance._call_and_refresh(
            cli_, access_key_id=access_key_id, secret_access_key=secret_access_key,
            api_base=api_base, api_version=api_version, params=params
        )
        return instance

    @classmethod
    def modify(cls, **params):
        key = params.get("key")
        value = params.get("value")
        cli = [f"{cls.class_cli()}", "update", "--key", f"{key}"]
        environment_name = params.get("environment_name")
        new_environment_name = params.get("new_environment_name")
        if value:
            cli += ["--new-value", f"{value}"]
            params.pop("value", None)
        if environment_name:
            cli += ['--environment', f'{environment_name}']
            params.pop("environment_name", None)
        if new_environment_name:
            cli += ['--new-environment', f'{new_environment_name}']

        return cls._static_call(cli, params=params)

    @classmethod
    def create(cls, access_key_id=None, secret_access_key=None, api_base=None, api_version=None, **params):
        cli = [f"{cls.class_cli()}", "create"]

        if "environment_name" in params:
            environment_name = params.get("environment_name") or None
            cli += ['--environment', f'{environment_name}']

        # environment_name = params.get("environment_name")
        # if not environment_name:
        #     params.update({"environment_name": None})
        # else:

        return cls._static_call(
            cli,
            access_key_id,
            secret_access_key,
            api_base=api_base,
            api_version=api_version,
            params=params,
        )

    @classmethod
    def export(cls, environment_name=None, output_format="dotenv",
               access_key_id=None, secret_access_key=None, api_base=None, api_version=None, **params):
        assert output_format in ["dotenv", "json"]
        cli = [f"{cls.class_cli()}", "list", "--output"]
        if environment_name:
            cli += ['--environment', f'{environment_name}']
        return cls._static_call(
            cli,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            api_base=api_base,
            api_version=api_version,
            asjson=False,
            output_format=output_format,
            params=params,
        )
