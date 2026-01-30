from __future__ import absolute_import, division, print_function

import locker


class LockerError(Exception):
    def __init__(self, message=None,
                 http_body=None, http_status=None, json_body=None, headers=None,
                 code=None,
                 status_code=None,
                 ):
        super().__init__(message)

        if http_body and hasattr(http_body, "decode"):
            try:
                http_body = http_body.decode("utf-8")
            except BaseException:
                http_body = (
                    "<Could not decode body as utf-8. Please report to support@locker.io>"
                )

        self._message = message
        self.http_body = http_body
        self.http_status = http_status
        self.json_body = json_body
        self.headers = headers or {}
        self.code = code
        self.status_code = status_code
        self.request_id = self.headers.get("request-id", None)
        self.error = self.construct_error_object()

    def __str__(self):
        msg = self._message or "<empty message>"
        if self.request_id is not None:
            return u"Request {0}: {1}".format(self.request_id, msg)
        else:
            return msg

    @property
    def user_message(self):
        return self._message

    def __repr__(self):
        return "%s(message=%r, http_status=%r, request_id=%r)" % (
            self.__class__.__name__,
            self._message,
            self.http_status,
            self.request_id,
        )

    def construct_error_object(self):
        if (
            self.json_body is None
            or "error" not in self.json_body
            # or not isinstance(self.json_body["error"], dict)
        ):
            return None

        return locker.ls_resources.error_object.ErrorObject.construct_from(
            self.json_body, locker.access_key
        )


class APIError(LockerError):
    pass


class CliRunError(LockerError):
    """."""

    process = None

    def __init__(
        self,
        message,
        http_body=None,
        http_status=None,
        json_body=None,
        headers=None,
        code="cli_error",
        status_code=None,
        should_retry=False,
    ):
        super(CliRunError, self).__init__(
            message, http_body, http_status, json_body, headers, code, status_code
        )
        self.should_retry = should_retry


class APIConnectionError(LockerError):
    def __init__(
        self,
        message,
        http_body=None,
        http_status=None,
        json_body=None,
        headers=None,
        code=None,
        status_code=None,
        should_retry=False,
    ):
        super(APIConnectionError, self).__init__(
            message, http_body, http_status, json_body, headers, code, status_code
        )
        self.should_retry = should_retry


class APIServerError(LockerError):
    pass


class LockerErrorWithParamCode(LockerError):
    def __init__(
        self,
        message,
        param,
        code=None,
        status_code=None,
        http_body=None,
        http_status=None,
        json_body=None,
        headers=None,
    ):
        super(LockerErrorWithParamCode, self).__init__(
            message, http_body, http_status, json_body, headers, code, status_code
        )
        self.param = param

    def __repr__(self):
        return ("%s(message=%r, param=%r, code=%r, http_status=%r, request_id=%r)" % (
            self.__class__.__name__,
            self._message,
            self.param,
            self.code,
            self.http_status,
            self.request_id,
        ))


class IdempotencyError(LockerError):
    pass


class InvalidRequestError(LockerErrorWithParamCode):
    def __init__(
        self,
        message,
        param,
        code=None,
        status_code=None,
        http_body=None,
        http_status=None,
        json_body=None,
        headers=None,
    ):
        super(InvalidRequestError, self).__init__(
            message, http_body, http_status, json_body, headers, code, status_code
        )
        self.param = param


class AuthenticationError(LockerError):
    pass


class PermissionDeniedError(LockerError):
    pass


class ResourceNotFoundError(LockerError):
    pass


class RateLimitError(LockerError):
    pass


