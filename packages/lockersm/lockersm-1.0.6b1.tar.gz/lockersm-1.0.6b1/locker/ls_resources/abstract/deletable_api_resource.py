from __future__ import absolute_import, division, print_function

from six.moves.urllib.parse import quote_plus
from locker import util
from locker.ls_resources.abstract.api_resource import APIResource


class DeletableAPIResource(APIResource):
    @classmethod
    def _cls_delete(cls, sid, **params):
        # TODO: Get delete resource cli
        url = "%s/%s" % (cls.class_url(), quote_plus(sid))
        return cls._static_request("delete", url, params=params)

    # @util.class_method_variant("_cls_delete")
    def delete(self, **params):
        return self._call_and_refresh(
            self.instance_cli(), params=params
        )
