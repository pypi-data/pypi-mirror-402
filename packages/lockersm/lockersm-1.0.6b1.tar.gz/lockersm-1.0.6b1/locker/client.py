import copy
import hashlib
import json
import logging
import os
import platform
import socket
import stat
import sys
import tempfile
import threading
import traceback
from typing import Dict, Any
import requests

from locker.ls_resources import Secret, Environment


LOCKER_LOG = os.environ.get("LOCKER_LOG")


class Locker:
    DEFAULT_OPTIONS = {
        "access_key_id": None,
        "secret_access_key": None,
        "thread_locking": False,
        "api_base": "https://api.locker.io/locker_secrets",
        "api_version": "v1",
        "proxy": None,
        "log": "error",
        "max_network_retries": 0,
        "skip_cli_lines": 0,
        "headers": {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
        },
    }

    def __init__(
        self,
        access_key_id: str = None,
        secret_access_key: str = None,
        api_base: str = None,
        api_version: str = None,
        proxy: Any = None,
        log: str = None,
        thread_locking: bool = False,
        max_network_retries: int = 0,
        resttime: int = 120,
        fetch: bool = False,
        options: Dict = None,
    ):
        # self.download_binary()
        if options is None:
            options = {}
        if api_base:
            options["api_base"] = api_base
        if api_version:
            options["api_version"] = api_version
        if proxy:
            options["proxy"] = proxy
        log = log or LOCKER_LOG
        if log:
            options["log"] = log
        assert resttime >= -1
        options["resttime"] = resttime
        options["fetch"] = fetch
        options["thread_locking"] = thread_locking

        if max_network_retries:
            options["max_network_retries"] = max_network_retries
        if access_key_id:
            options["access_key_id"] = access_key_id
        if secret_access_key:
            options["secret_access_key"] = secret_access_key

        self._options: dict[str, Any] = copy.deepcopy(Locker.DEFAULT_OPTIONS)

        # Set Headers
        if "headers" in options:
            headers = copy.copy(options["headers"])
        else:
            headers = {}

        self._options.update(options)
        self._options["headers"].update(headers)

        # Set Logger
        logger = self._set_stream_logger(level=self._options.get('log'))
        self._options["logger"] = logger

        # Rip off trailing slash since all urls depend on that
        assert isinstance(self._options["api_base"], str)
        if self._options["api_base"].endswith("/"):
            self._options["api_base"] = self._options["api_base"][:-1]

        # if access_key_basic_auth:
        #     self._create_access_key_basic_auth(*access_key_basic_auth)

        self.is_valid_binary = False

        # Locking
        self.lock = None
        if thread_locking:
            self.lock = threading.Lock()

    # ---- This method is DEPRECATED from 0.1.1b1 ------------------- #
    # def _create_access_key_basic_auth(self, access_key_id: str, secret_access_key: str):
    #     self._options["access_key"] = f"{access_key_id}:{secret_access_key}"

    @property
    def access_key_id(self):
        return self._options.get("access_key_id")

    @access_key_id.setter
    def access_key_id(self, access_key_id_value):
        self._options.update({"access_key_id": access_key_id_value})

    @property
    def secret_access_key(self):
        return self._options.get("secret_access_key")

    @secret_access_key.setter
    def secret_access_key(self, secret_access_key_value):
        self._options.update({"secret_access_key": secret_access_key_value})

    @property
    def api_base(self):
        return str(self._options.get("api_base"))

    @api_base.setter
    def api_base(self, api_base_value):
        self._options.update({"api_base": api_base_value})

    @property
    def api_version(self):
        return str(self._options.get("api_version"))

    @property
    def log(self):
        return self._options.get("log")

    @log.setter
    def log(self, log_value):
        self._options.update({"log": log_value})
        logger = self._set_stream_logger(level=log_value)
        self._options["logger"] = logger

    @property
    def thread_locking(self):
        return self._options.get("thread_locking")

    @thread_locking.setter
    def thread_locking(self, thread_locking_value):
        self._options.update({"thread_locking": thread_locking_value})
        if thread_locking_value is True:
            self.lock = threading.Lock()
        else:
            self.lock = None

    @staticmethod
    def _set_stream_logger(level, name='locker'):
        assert level in ["debug", "info", "warning", "error"], "The log level is not valid"
        level = level.upper()
        format_string = '%(asctime)s {hostname} %(levelname)s %(message)s'.format(**{'hostname': socket.gethostname()})

        logger = logging.getLogger(name)
        logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    @property
    def resttime(self):
        return self._options.get("resttime")

    @resttime.setter
    def resttime(self, resttime_value):
        self._options.update({"resttime": resttime_value})

    @property
    def fetch(self):
        return self._options.get("fetch")

    @fetch.setter
    def fetch(self, fetch_value):
        self._options.update({"fetch": fetch_value})

    @property
    def skip_cli_lines(self):
        return self._options.get("skip_cli_lines")

    @property
    def headers(self):
        return self._options.get("headers")

    @headers.setter
    def headers(self, custom_headers):
        self._options.update({"headers": custom_headers})

    @property
    def max_network_retries(self):
        return self._options.get("max_network_retries")

    def _translate_options(self, params):
        _params = copy.deepcopy(self._options)
        _params.update(params)
        return _params

    @staticmethod
    def __get_download_paths():
        _about_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "__about__.json")
        with open(_about_file, 'r') as fd:
            about_data = json.load(fd)
            binary_checksum_dict = about_data.get("binary_checksum")
            binary_version = about_data.get("binary_version")
        home_dir = os.path.expanduser("~")
        locker_dir = os.path.join(home_dir, ".locker")
        # Check if the .locker directory exists, and create it if not
        if not os.path.exists(locker_dir):
            try:
                os.makedirs(locker_dir)
            except (PermissionError, OSError):
                home_dir = tempfile.gettempdir()
                locker_dir = os.path.join(home_dir, ".locker")
                if not os.path.exists(locker_dir):
                    os.makedirs(locker_dir)
            except FileExistsError:
                pass

        binary_file_path = os.path.join(locker_dir, f"locker_binary-{binary_version}")
        if sys.platform == "darwin":
            if platform.processor() == "arm":
                checksum = binary_checksum_dict.get("mac-arm64")
                binary_url = f"https://s.locker.io/download/locker-cli-mac-arm64-{binary_version}"
            else:
                checksum = binary_checksum_dict.get("mac-x64")
                binary_url = f"https://s.locker.io/download/locker-cli-mac-x64-{binary_version}"
        elif sys.platform == "win32":
            # binary_version = "1.0.60"
            binary_url = f"https://s.locker.io/download/locker-cli-win-x64-{binary_version}.exe"
            binary_file_path = os.path.join(locker_dir, f"locker_binary-{binary_version}.exe")
            checksum = binary_checksum_dict.get("windows")
        else:
            p = platform.processor() or platform.machine()
            if p in ["arm", "aarch64"]:
                binary_url = f"https://s.locker.io/download/locker-cli-linux-arm64-{binary_version}"
                checksum = binary_checksum_dict.get("linux-arm64")
            else:
                binary_url = f"https://s.locker.io/download/locker-cli-linux-x64-{binary_version}"
                checksum = binary_checksum_dict.get("linux")

        return {
            "locker_dir": locker_dir,
            "binary_url": binary_url,
            "binary_file_path": binary_file_path,
            "checksum": checksum,
        }

    def check_binary(self):
        if not self.__check_binary_file():
            # TODO: Auto remove the .locker folder and re-check
            raise Exception("The binary CLI is not downloaded correctly. Please remove .locker folder and retry again")

    def __check_binary_file(self):

        p = self.__get_download_paths()
        binary_file_path = p.get("binary_file_path")
        binary_url = p.get("binary_url")
        checksum = p.get("checksum")

        download_retry = 1
        max_download_retries = 10
        if not self.is_valid_binary:
            print("[+] Starting checking binary")
            while download_retry <= max_download_retries:
                if not os.path.exists(binary_file_path):
                    is_valid_binary = self.__download_and_check(
                        url=binary_url, binary_file_path=binary_file_path, correct_checksum=checksum
                    )
                else:
                    downloaded_checksum = self.__get_downloaded_checksum(binary_file_path)
                    is_valid_binary = downloaded_checksum == checksum or self.__download_and_check(
                        url=binary_url, binary_file_path=binary_file_path, correct_checksum=checksum
                    )
                if not is_valid_binary:
                    download_retry += 1
                    continue
                self.is_valid_binary = is_valid_binary
                break
        return self.is_valid_binary

    @staticmethod
    def __get_downloaded_checksum(binary_file_path):
        try:
            with open(binary_file_path, "rb") as f:
                binary_bytes = f.read()
                return hashlib.sha256(binary_bytes).hexdigest()
        except FileNotFoundError:
            return None

    def __download_and_check(self, url, binary_file_path, correct_checksum):
        downloaded = self.__download_binary_cli(url=url, save_path=binary_file_path)
        if not downloaded:
            return False
        return self.__get_downloaded_checksum(binary_file_path) == correct_checksum

    @staticmethod
    def __download_binary_cli(url, save_path):
        r = requests.get(url, stream=True)
        if r.ok:
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 8):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                        os.fsync(f.fileno())
            try:
                # Make the binary executable
                st = os.stat(save_path)
                os.chmod(save_path, st.st_mode | stat.S_IEXEC)
            except PermissionError as e:
                tb = traceback.format_exc()
                print(f"set permission error {e} - {tb}")
                pass
            return True

        # HTTP status code 4XX/5XX
        else:
            print("Download failed: status code {}\n{}".format(r.status_code, r.text))
            return False

    def list(self, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Secret.list(**self._translate_options(params))
        else:
            self.check_binary()
            return Secret.list(**self._translate_options(params))

    def export(self, environment_name=None, output_format="dotenv",  **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Secret.export(
                    environment_name=environment_name, output_format=output_format, **self._translate_options(params)
                )
        else:
            self.check_binary()
            return Secret.export(
                environment_name=environment_name, output_format=output_format, **self._translate_options(params)
            )

    def get(self, key, environment_name=None, default_value=None, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Secret.get_secret(
                    key,
                    environment_name=environment_name,
                    default_value=default_value,
                    **self._translate_options(params)
                )
        else:
            self.check_binary()
            return Secret.get_secret(
                key,
                environment_name=environment_name,
                default_value=default_value,
                **self._translate_options(params)
            )

    def get_secret(self, key, environment_name=None, default_value=None, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Secret.get_secret(
                    key,
                    environment_name=environment_name,
                    default_value=default_value,
                    **self._translate_options(params)
                )
        else:
            self.check_binary()
            return Secret.get_secret(
                key,
                environment_name=environment_name,
                default_value=default_value,
                **self._translate_options(params)
            )

    def retrieve(self, key, environment_name=None, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Secret.retrieve_secret(key, environment_name=environment_name, **self._translate_options(params))
        else:
            self.check_binary()
            return Secret.retrieve_secret(key, environment_name=environment_name, **self._translate_options(params))

    def create(self, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Secret.create(**self._translate_options(params))
        else:
            self.check_binary()
            return Secret.create(**self._translate_options(params))

    def modify(self, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Secret.modify(**self._translate_options(params))
        else:
            self.check_binary()
            return Secret.modify(**self._translate_options(params))

    def list_environments(self, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Environment.list(**self._translate_options(params))
        else:
            self.check_binary()
            return Environment.list(**self._translate_options(params))

    def get_environment(self, name, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Environment.get_environment(
                    name=name,
                    **self._translate_options(params)
                )
        else:
            self.check_binary()
            return Environment.get_environment(
                name=name,
                **self._translate_options(params)
            )

    def retrieve_environment(self, name, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Environment.retrieve_environment(
                    name=name,
                    **self._translate_options(params)
                )
        else:
            self.check_binary()
            return Environment.retrieve_environment(
                name=name,
                **self._translate_options(params)
            )

    def create_environment(self, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Environment.create(**self._translate_options(params))
        else:
            self.check_binary()
            return Environment.create(**self._translate_options(params))

    def modify_environment(self, **params):
        if self.thread_locking is True:
            with self.lock:
                self.check_binary()
                return Environment.modify(**self._translate_options(params))
        else:
            self.check_binary()
            return Environment.modify(**self._translate_options(params))
