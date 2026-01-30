from __future__ import absolute_import, division, print_function

import six
from six.moves.urllib.parse import quote_plus

from locker import util, binary_adapter, error, DEFAULT_TIMEOUT
from locker.ls_object import LSObject


class APIResource(LSObject):
    @classmethod
    def retrieve(cls, id, access_key_id=None, secret_access_key=None, **params):
        instance = cls(id, access_key_id, secret_access_key, **params)
        instance.refresh()
        return instance

    def refresh(self):
        return self._call_and_refresh(self.instance_cli())

    @classmethod
    def class_cli(cls):
        if cls == APIResource:
            raise NotImplementedError(
                "APIResource is an abstract class. You should perform "
                "actions on its subclasses (e.g. Environment, Secret)"
            )
        # The base cli command is object names of this class and the namespaces are separated in object name
        # with periods (.) and in CLI commands with (-), so replace the former with the latter
        base = cls.OBJECT_NAME.replace(".", "-")
        return base

        # # Namespaces are separated in object names with periods (.) and in URLs
        # # with forward slashes (/), so replace the former with the latter.
        # base = cls.OBJECT_NAME.replace(".", "/")
        # return "/v1/%ss" % (base,)

    def instance_cli(self):
        instance_id = self.get("id")

        if not isinstance(instance_id, six.string_types):
            raise error.InvalidRequestError(
                "Could not determine which URL to request: %s instance "
                "has invalid ID: %r, %s. ID should be of type `str` (or"
                " `unicode`)" % (type(self).__name__, instance_id, type(instance_id)),
                "id",
            )

        base = self.class_cli()
        extn = quote_plus(instance_id)
        # The -i param is `id` of the object
        return '%s get --id %s' % (base, extn)

    # The `method_` and `url_` arguments are suffixed with an underscore to
    # avoid conflicting with actual request parameters in `params`.
    def _call(
        self,
        cli_,
        access_key_id=None,
        secret_access_key=None,
        api_base=None,
        api_version=None,
        asjson=True,
        timeout=DEFAULT_TIMEOUT,
        output_format="json",
        params=None,
    ):
        obj = LSObject._call(
            self,
            cli_,
            access_key_id,
            secret_access_key,
            api_base,
            api_version,
            asjson,
            timeout,
            output_format,
            params,
        )

        if type(self) is type(obj):
            self.refresh_from(obj)
            return self
        else:
            return obj

    # The 'cli_' is suffixed with an underscore to avoid conflicting with request parameters in `params`
    def _call_and_refresh(
        self,
        cli,
        access_key_id=None,
        secret_access_key=None,
        api_base=None,
        api_version=None,
        asjson=True, timeout=DEFAULT_TIMEOUT, output_format="json", params=None
    ):
        obj = LSObject._call(
            self,
            cli, access_key_id, secret_access_key, api_base, api_version,
            asjson, timeout, output_format, params
        )
        self.refresh_from(obj)
        return self

    # The 'cli_' is suffixed with an underscore to avoid conflicting with request parameters in `params`
    @classmethod
    def _static_call(
        cls,
        cli_,
        access_key_id=None,
        secret_access_key=None,
        api_base=None,
        api_version=None,
        asjson=True,
        timeout=DEFAULT_TIMEOUT,
        output_format="json",
        params=None,
    ):
        params = None if params is None else params.copy()
        access_key_id = util.read_special_variable(params, "access_key_id", access_key_id)
        secret_access_key = util.read_special_variable(params, "secret_access_key", secret_access_key)
        api_base = util.read_special_variable(params, "api_base", api_base)
        api_version = util.read_special_variable(params, "api_version", api_version)
        headers = util.read_special_variable(params, "headers", None)
        skip_cli_lines = util.read_special_variable(params, "skip_cli_lines", 0)
        logger = util.read_special_variable(params, "logger", None) if params else None
        resttime = util.read_special_variable(params, "resttime", None)
        fetch = util.read_special_variable(params, "fetch", None)

        binary_executor = binary_adapter.BinaryAdapter(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            api_base=api_base,
            api_version=api_version,
            headers=headers,
            logger=logger,
            resttime=resttime,
            fetch=fetch
        )
        res_data = binary_executor.call(
            cli=cli_, params=params, asjson=asjson, timeout=timeout, skip_cli_lines=skip_cli_lines,
            output_format=output_format
        )
        return util.convert_to_ls_object(
            res_data, access_key_id, secret_access_key, api_base, api_version, params
        )

