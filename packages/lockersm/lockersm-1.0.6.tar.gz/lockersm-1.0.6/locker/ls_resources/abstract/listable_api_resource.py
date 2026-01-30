from __future__ import absolute_import, division, print_function

from locker.ls_resources.abstract.api_resource import APIResource


class ListableAPIResource(APIResource):
    @classmethod
    def auto_paging_iter(cls, *args, **params):
        return cls.list(*args, **params).auto_paging_iter()

    @classmethod
    def list(cls, access_key_id=None, secret_access_key=None, api_base=None, api_version=None, **params):
        return cls._static_call(
            [cls.class_cli(), "list"],
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            api_base=api_base,
            api_version=api_version,
            params=params,
        )
