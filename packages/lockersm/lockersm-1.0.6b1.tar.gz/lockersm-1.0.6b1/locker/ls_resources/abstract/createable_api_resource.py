from __future__ import absolute_import, division, print_function

from locker.ls_resources.abstract.api_resource import APIResource


class CreateableAPIResource(APIResource):
    @classmethod
    def create(cls, access_key_id=None, secret_access_key=None, api_base=None, api_version=None, **params):
        return cls._static_call(
            [f"{cls.class_cli()}", "create"],
            access_key_id,
            secret_access_key,
            api_base=api_base,
            api_version=api_version,
            params=params,
        )
