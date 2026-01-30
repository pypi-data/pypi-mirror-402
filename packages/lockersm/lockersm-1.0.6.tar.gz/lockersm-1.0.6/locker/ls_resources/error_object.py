from __future__ import absolute_import, division, print_function

from locker.util import merge_dicts
from locker.ls_object import LSObject


class ErrorObject(LSObject):
    def refresh_from(self, values, access_key_id=None, secret_access_key=None, partial=False,
                     api_base=None, api_version=None, last_response=None):
        # Unlike most other API resources, the API will omit attributes in error objects when they have a null value.
        # We manually set default values here to facilitate generic error handling.
        # TODO: Add doc_url, etc... in the ErrorObject
        # {
        #     "code": None,
        #     "decline_code": None,
        #     "message": None,
        #     "param": None,
        #     "payment_intent": None,
        #     "payment_method": None,
        #     "setup_intent": None,
        #     "source": None,
        #     "type": None,
        # }
        values = merge_dicts(
            {
                "doc_url": None,
            },
            values,
        )
        return super(ErrorObject, self).refresh_from(
            values,
            access_key_id,
            secret_access_key,
            partial,
            api_base,
            api_version,
            last_response,
        )
