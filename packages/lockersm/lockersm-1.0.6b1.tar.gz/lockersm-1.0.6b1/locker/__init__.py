from __future__ import absolute_import, division, print_function

import hashlib
import json
import os
import platform
import stat
import sys
import tempfile
import traceback
import requests

# from locker.atomic_locking import AtomicNameLock


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

DEFAULT_TIMEOUT = 180

DEV_MODE = False

_about_file = os.path.join(ROOT_PATH, "__about__.json")
with open(_about_file, 'r') as fd:
    about_data = json.load(fd)
    binary_version = about_data.get("binary_version")
    binary_checksum_dict = about_data.get("binary_checksum")


home_dir = os.path.expanduser("~")
locker_dir = os.path.join(home_dir, ".locker")
# Ensure the .locker directory exists
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
downloaded_checksum_path = os.path.join(locker_dir, f"CHECKSUM")

# Check os and get the binary url
if sys.platform == "darwin":
    if platform.processor() == "arm":
        binary_url = f"https://s.locker.io/download/locker-cli-mac-arm64-{binary_version}"
        checksum = binary_checksum_dict.get("mac-arm64")
    else:
        binary_url = f"https://s.locker.io/download/locker-cli-mac-x64-{binary_version}"
        checksum = binary_checksum_dict.get("mac-x64")
elif sys.platform == "win32":
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


# lock = AtomicNameLock('locker_downloader')
# if lock.acquire(timeout=30):
#     if not os.path.exists(binary_file_path):
#         r = requests.get(binary_url, stream=True)
#         if r.ok:
#             print("saving to", os.path.abspath(binary_file_path))
#             logging.debug(f"saving to {os.path.abspath(binary_file_path)}")
#             with open(binary_file_path, 'wb') as f:
#                 for chunk in r.iter_content(chunk_size=1024 * 8):
#                     if chunk:
#                         f.write(chunk)
#                         f.flush()
#                         os.fsync(f.fileno())
#             logging.warning(f"saving ok {os.path.abspath(binary_file_path)}")
#             try:
#                 # Make the binary executable
#                 # logging.warning(f"starting set permission {binary_file_path}")
#                 st = os.stat(binary_file_path)
#                 os.chmod(binary_file_path, st.st_mode | stat.S_IEXEC)
#                 # logging.warning(f"set permission ok {binary_file_path}")
#             except PermissionError as e:
#                 tb = traceback.format_exc()
#                 logging.error(f"set permission error {e} - {tb}")
#                 pass
#
#         # HTTP status code 4XX/5XX
#         else:
#             logging.error("Download failed: status code {}\n{}".format(r.status_code, r.text))
#             print("Download failed: status code {}\n{}".format(r.status_code, r.text))
#     lock.release()


def download_binary_cli(url, save_path):
    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(binary_file_path))
        # logging.debug(f"saving to {os.path.abspath(save_path)}")
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())

        print(f"saving ok {os.path.abspath(save_path)}")
        # logging.debug(f"saving ok {os.path.abspath(save_path)}")
        try:
            # Make the binary executable
            st = os.stat(save_path)
            os.chmod(save_path, st.st_mode | stat.S_IEXEC)
        except PermissionError as e:
            tb = traceback.format_exc()
            print(f"set permission error {e} - {tb}")
            # logging.error(f"set permission error {e} - {tb}")
            pass

        # Calc and save checksum
        with open(save_path, "rb") as f:
            binary_bytes = f.read()
            readable_hash = hashlib.sha256(binary_bytes).hexdigest()
        with open(downloaded_checksum_path, "w") as f:
            f.write(readable_hash)

        return True

    # HTTP status code 4XX/5XX
    else:
        # logging.error("Download failed: status code {}\n{}".format(r.status_code, r.text))
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))
        return False


def get_downloaded_checksum(save_path):
    try:
        with open(downloaded_checksum_path, "r") as f:
            downloaded_checksum = f.read()
            return downloaded_checksum
    except FileNotFoundError:
        with open(save_path, "rb") as f:
            binary_bytes = f.read()
            readable_hash = hashlib.sha256(binary_bytes).hexdigest()
        with open(downloaded_checksum_path, "w") as f:
            f.write(readable_hash)
        return readable_hash


def download_and_check(url, save_path):
    downloaded = download_binary_cli(url=url, save_path=save_path)
    if not downloaded:
        return False
    return get_downloaded_checksum(binary_file_path) == checksum


download_retry = 1
max_download_retries = 10
# Currently, not check the checksum
is_valid_binary = True

if not is_valid_binary:
    while download_retry <= max_download_retries:
        if not os.path.exists(binary_file_path):
            is_valid_binary = download_and_check(url=binary_url, save_path=binary_file_path)
        else:
            downloaded_checksum = get_downloaded_checksum(binary_file_path)
            is_valid_binary = downloaded_checksum == checksum or download_and_check(
                url=binary_url, save_path=binary_file_path
            )
        if not is_valid_binary:
            download_retry += 1
            continue
        break

else:
    if not os.path.exists(binary_file_path):
        download_binary_cli(url=binary_url, save_path=binary_file_path)

if not is_valid_binary:
    raise Exception("The binary CLI is not downloaded correctly")


from locker.client import Locker

