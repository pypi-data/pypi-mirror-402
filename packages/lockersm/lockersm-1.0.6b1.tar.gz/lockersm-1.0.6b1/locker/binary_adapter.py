from __future__ import absolute_import, division, print_function

import json
import logging
import os
import stat
import sys
import subprocess

from six.moves.urllib.parse import urlencode

from locker import ROOT_PATH, DEV_MODE, DEFAULT_TIMEOUT, util, error, binary_file_path


class BinaryAdapter(object):
    def __init__(self, access_key_id=None, secret_access_key=None, api_base=None, api_version=None, headers=None,
                 logger=None, resttime: int = 120, fetch: bool = False):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.api_base = api_base
        self.api_version = api_version
        self.headers = headers
        self.system_platform = self.get_platform()
        self.logger = logger or logging.getLogger("locker")
        self.resttime = resttime
        self.fetch = fetch

    @classmethod
    def make_executable(cls, path):
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)

    @staticmethod
    def get_platform():
        # Return darwin/win32/linux
        return sys.platform

    @staticmethod
    def get_sdk_version():
        _about_file = os.path.join(ROOT_PATH, "__about__.json")
        with open(_about_file, 'r') as fd:
            version = json.load(fd).get("version")
        return version

    def get_binary_file(self):
        if DEV_MODE:
            # Checking the os system, returns the corresponding binary
            # OS X
            if self.system_platform == "darwin":
                return os.path.join(ROOT_PATH, "bin", "locker_mac")
            # Windows
            elif self.system_platform == "win32":
                return os.path.join(ROOT_PATH, "bin", "locker_windows.exe")
            # Default is linux
            else:
                return os.path.join(ROOT_PATH, "bin", "locker_linux")
        return binary_file_path

    def call(
        self,
        cli,
        params=None,
        asjson=True,
        timeout=DEFAULT_TIMEOUT,
        skip_cli_lines=0,
        output_format="json"
    ):
        # with self._lock:
        binary_file = self.get_binary_file()
        my_access_key_id = self.access_key_id
        my_secret_access_key = self.secret_access_key
        # if my_access_key_id is None or my_secret_access_key is None:
        #     raise error.AuthenticationError(
        #         "No Access key provided. (HINT: set your API key using "
        #         '"locker.access_key_id = <ACCESS-KEY-ID>" and "locker.secret_access_key = <SECRET-ACCESS-KEY>"). '
        #         "You can generate Access Key from the Locker Secret web interface."
        #     )
        my_headers = self.headers or {}
        default_client_agent = f"Python - {self.get_sdk_version()}"

        if isinstance(cli, list):
            cli_arr = cli
        else:
            self.logger.warning("[!] The string command will be deprecated in the feature")
            cli_arr = cli.split(' ')
        command_arr = [f'{binary_file}'] + cli_arr
        if my_access_key_id is not None:
            command_arr += [
                '--access-key-id', f'{my_access_key_id}'
            ]
        if my_secret_access_key is not None:
            command_arr += [
                '--secret-access-key', f'{my_secret_access_key}'
            ]

        command_arr += [
            '--api-base', f'{self.api_base}',
            '--agent', f'{default_client_agent}',
            '--resttime', f'{self.resttime}',
            # '--verbose'
        ]
        if output_format:
            command_arr += [f"--output-format", f"{output_format}"]
        if self.fetch is True:
            command_arr += ['--fetch']

        if my_headers:
            if isinstance(my_headers, dict):
                my_headers_list = [f"{k}:{v}" for k, v in my_headers.items()]
                my_headers = ",".join(my_headers_list)
            command_arr += ['--headers', f'{my_headers}']
        else:
            command_arr += ['--headers', '']

        # Building full command with params
        post_data = None
        if "get" in cli or "delete" in cli:
            encoded_params = urlencode(list(util.api_encode(params or {})))
            # Don't use strict form encoding by changing the square bracket control
            # characters back to their literals. This is fine by the server, and
            # makes these parameter strings easier to read.
            encoded_params = encoded_params.replace("%5B", "[").replace("%5D", "]")
            # TODO: Build api url by passing filter params to command
            # if params:
            #     abs_url = _build_api_url(abs_url, encoded_params)
            pass
        elif "update" in cli or "create" in cli:
            params_data = params or {}
            for k, v in params_data.items():
                if k in ["key", "value", "description", "new_key", "new_value", "new_description", "env",
                         "name", "url", "new_name", "new_url", "new_environment",
                         "new-key", "new-value", "new-environment", "new-description", "new-name", "new-url"]:
                    command_arr += [f'--{k.replace("_", "-")}', f'{v}']

        #     post_data = json.dumps(params or {})
        # if post_data:
        #     command_arr += ['--data', f'{post_data}']

        self.logger.debug(f"[+] Running with timeout {timeout} cli command: {command_arr}")
        try:
            raw = subprocess.check_output(
                command_arr,
                stderr=subprocess.STDOUT, shell=False, universal_newlines=True, timeout=timeout
            )
        except subprocess.TimeoutExpired as e:
            exc = error.CliRunError(e.stdout)
            exc.process = e
            raise exc
        except subprocess.CalledProcessError as e:
            signs = ['"success": false', '"success": true', '"object": "error"']
            if any(s in e.output for s in signs):
                raw = e.output
            elif str(e.output).strip() == 'Killed' or 'returned non-zero exit status 1' in str(e):
                exc = error.CliRunError(e.stdout)
                exc.process = e
                raise exc
            else:
                self.logger.warning(f"[!] subprocess.CalledProcessError: {e} {e.output}. The command is: {command_arr}")
                exc = error.CliRunError(e.stdout)
                exc.process = e
                raise exc
        return self.interpret_response(res_body=raw, asjson=asjson, skip_cli_lines=skip_cli_lines)

    def interpret_response(self, res_body, asjson=True, skip_cli_lines=0):
        # Skip cli lines
        if skip_cli_lines > 0:
            res_body = res_body.split("\n", skip_cli_lines)[skip_cli_lines]
        # Log break
        try:
            res_body = res_body.split("----------- LOG BREAK -----------")[1]
        except IndexError:
            pass
        if not asjson:
            return res_body
        try:
            if hasattr(res_body, "decode"):
                res_body = res_body.decode("utf-8")
        except Exception:
            self.logger.warning(f"[!] Invalid decode response body from CLI:::{res_body}")
            exc = error.CliRunError(
                f"Invalid decode response body from CLI: {res_body}",
                res_body
            )
            exc.process = res_body
            raise exc
        try:
            res_body = json.loads(res_body)
        except json.decoder.JSONDecodeError:
            self.logger.warning(f"[!] CLI result json decode error:::{res_body}")
            exc = error.CliRunError(
                f"CLI JSONDecodeError:::{res_body}", res_body
            )
            exc.process = res_body
            raise exc
        if self._should_handle_as_error(res_body):
            res_body.update({"object": "error"})
            self.handle_error_response(res_body)
        return res_body

    @staticmethod
    def _should_handle_as_error(res_body):
        try:
            return res_body.get("object") == "error" or res_body.get("success") is False or\
                res_body.get("success") == "false"
        except AttributeError:
            return False

    def handle_error_response(self, res_body):
        exc = self.specific_cli_error(error_data=res_body)
        self.logger.warning(f"[!] CLI return error object:::{exc.http_body}")
        raise exc

    def specific_cli_error(self, error_data):
        status_code = error_data.get("status_code")
        error_code = error_data.get("error")
        if status_code == 429 or error_code == "rate_limit":
            return error.RateLimitError(
                error_data.get("message"),
                http_body=error_data,
                http_status=429,
                code="rate_limit",
                status_code=429
            )
        elif status_code == 401 or error_code in ["unauthorized", "invalid_secret_access_key"]:
            return error.AuthenticationError(
                error_data.get("message"),
                http_body=error_data,
                http_status=401,
                code="unauthorized",
                status_code=401
            )
        elif status_code == 403 or error_code == "permission_denied":
            return error.PermissionDeniedError(
                error_data.get("message"),
                http_body=error_data,
                http_status=403,
                code="permission_denied",
                status_code=403
            )
        elif status_code == 404 or error_code in ["not_found", "not_found_error"]:
            return error.ResourceNotFoundError(
                error_data.get("message"),
                http_body=error_data,
                http_status=404,
                code="not_found",
                status_code=404
            )
        elif (status_code and status_code >= 500) or error_code == "server_error":
            return error.APIServerError(
                error_data.get("message"),
                http_body=error_data,
                http_status=500,
                code="server_error",
                status_code=500
            )
        elif error_code == "http_error":
            return error.APIConnectionError(
                error_data.get("message"),
                http_body=error_data,
                http_status=503,
                code="http_error",
                status_code=503
            )
        elif error_code in ["database_error", "command_error"]:
            return error.CliRunError(
                error_data.get("message"),
                http_body=error_data,
                code="cli_error",
            )
        else:
            return error.LockerError(
                error_data.get("message"),
                http_body=error_data,
                code="locker_error"
            )
