from __future__ import absolute_import, division, print_function

from six.moves.urllib.parse import quote_plus

from locker.ls_resources.abstract.api_resource import APIResource


class UpdateableAPIResource(APIResource):
    @classmethod
    def modify(cls, **params):
        name = params.get("sid") or params.get("name")
        cli = [f"{cls.class_cli()}", "update", "--id", f"{quote_plus(name)}"]
        return cls._static_call(cli, params=params)
