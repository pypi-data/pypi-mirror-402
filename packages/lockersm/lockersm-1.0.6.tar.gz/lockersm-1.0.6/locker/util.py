from __future__ import absolute_import, division, print_function

import datetime
import calendar
from collections import OrderedDict
import six
import time

import locker
from locker.ls_response import LSResponse
from locker.ls_object import LSObject


def get_object_classes():
    # This is here to avoid a circular dependency
    from locker.object_classes import OBJECT_CLASSES
    return OBJECT_CLASSES


def convert_to_ls_object(
    resp, access_key_id=None, secret_access_key=None, api_base=None, api_version=None, params=None
):
    # This is here to avoid a circular dependency
    # If we get a LSResponse, we'll want to return a
    # LSObject with the last_response field filled out with
    # the raw API response information
    ls_response = None

    if isinstance(resp, locker.ls_response.LSResponse):
        ls_response = resp
        resp = ls_response.data

    if isinstance(resp, list):
        return [
            convert_to_ls_object(i, access_key_id, secret_access_key, api_base, api_version) for i in resp
        ]
    elif isinstance(resp, dict) and not isinstance(
        resp, locker.ls_object.LSObject
    ):
        resp = resp.copy()
        klass_name = resp.get("object")
        if isinstance(klass_name, six.string_types):
            klass = get_object_classes().get(
                klass_name, locker.ls_object.LSObject
            )
        else:
            klass = locker.ls_object.LSObject

        obj = klass.construct_from(
            resp,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            api_base=api_base,
            api_version=api_version,
            last_response=ls_response,
        )

        # We only need to update _retrieve_params when special params were
        # actually passed. Otherwise, leave it as is as the list / search result
        # constructors will instantiate their own params.
        if (
            params is not None
            and hasattr(obj, "object")
            and ((obj.object == "list") or (obj.object == "search_result"))
        ):
            obj._retrieve_params = params
        return obj
    else:
        return resp


def read_special_variable(params, key_name, default_value):
    value = default_value
    params_value = None

    if params is not None and key_name in params:
        params_value = params[key_name]
        del params[key_name]
    if value is None:
        value = params_value
    return value


def encode_datetime(dttime):
    if dttime.tzinfo and dttime.tzinfo.utcoffset(dttime) is not None:
        utc_timestamp = calendar.timegm(dttime.utctimetuple())
    else:
        utc_timestamp = time.mktime(dttime.timetuple())

    return int(utc_timestamp)


def _encode_datetime(dttime):
    if dttime.tzinfo and dttime.tzinfo.utcoffset(dttime) is not None:
        utc_timestamp = calendar.timegm(dttime.utctimetuple())
    else:
        utc_timestamp = time.mktime(dttime.timetuple())

    return int(utc_timestamp)


def _encode_nested_dict(key, data, fmt="%s[%s]"):
    d = OrderedDict()
    for sub_key, sub_value in six.iteritems(data):
        d[fmt % (key, sub_key)] = sub_value
    return d


def api_encode(data):
    for key, value in six.iteritems(data):
        if value is None:
            continue
        elif hasattr(value, "locker_id"):
            yield key, value.stripe_id
        elif isinstance(value, list) or isinstance(value, tuple):
            for i, sv in enumerate(value):
                if isinstance(sv, dict):
                    subdict = _encode_nested_dict("%s[%d]" % (key, i), sv)
                    for k, v in api_encode(subdict):
                        yield k, v
                else:
                    yield "%s[%d]" % (key, i), sv
        elif isinstance(value, dict):
            subdict = _encode_nested_dict(key, value)
            for sub_key, sub_value in api_encode(subdict):
                yield sub_key, sub_value
        elif isinstance(value, datetime.datetime):
            yield key, _encode_datetime(value)
        else:
            yield key, value


def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z
