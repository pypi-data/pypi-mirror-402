import os
import tempfile
import time

DEFAULT_POLL_TIME = .1


class AtomicNameLock(object):

    def __init__(self, name, lock_dir=None, max_lock_age=None):
        """
        This uses a named directory, which is defined by POSIX as an atomic operation.
        :param name: (str) The lock name, Cannot contain directory seperator (like '/')
        :param lock_dir: (str/None) Directory in which to store locks. Defaults to tempdir
        :param max_lock_age: (float/None) Maximum number of seconds lock can be held before it is considered "too old"
        and fair game to be taken.
        You should likely define this as a reasonable number, maybe 4x as long as you think the operation will take,
        so that the lock doesn't get held by a dead process.
        """
        self.name = name
        self.max_lock_age = max_lock_age

        if os.sep in name:
            raise ValueError('Name cannot contain "%s"' % (os.sep,))

        if lock_dir:
            if lock_dir[-1] == os.sep:
                lock_dir = lock_dir[:-1]
                if not lock_dir:
                    raise ValueError('lockDir cannot be ' + os.sep)
        else:
            lock_dir = tempfile.gettempdir()

        self.lock_dir = lock_dir

        if not os.path.isdir(lock_dir):
            raise ValueError('lockDir %s either does not exist or is not a directory.' % (lock_dir,))

        if not os.access(lock_dir, os.W_OK):
            raise ValueError('Cannot write to lock directory: %s' % (lock_dir,))
        self.lock_path = lock_dir + os.sep + name

        self.held = False
        self.acquired_at = None

    def acquire(self, timeout=None):
        """
        Acquire given lock. Can be blocking or nonblocking by providing a timeout.
        Returns "True" if you got the lock, otherwise "False"
        :param timeout: (float/None) Max number of seconds to wait, or None to block until we can acquire it.
        :return: (bool) True if you got the lock, otherwise False.
        """

        if self.held is True:
            # NOTE: Without some type of in-directory marker (like an uuid) we cannot refresh an expired lock accurately
            if os.path.exists(self.lock_path):
                return True
            # Someone removed our lock
            self.held = False

        # If we aren't going to poll at least 5 times, give us a smaller interval
        if timeout:
            if timeout / 5.0 < DEFAULT_POLL_TIME:
                poll_time = timeout / 10.0
            else:
                poll_time = DEFAULT_POLL_TIME

            end_time = time.time() + timeout
            keep_going = lambda: bool(time.time() < end_time)
        else:
            poll_time = DEFAULT_POLL_TIME
            keep_going = lambda: True

        success = False
        while keep_going():
            try:
                os.mkdir(self.lock_path)
                success = True
                break
            except:
                time.sleep(poll_time)
                if self.max_lock_age:
                    if os.path.exists(self.lock_path) and \
                            os.stat(self.lock_path).st_mtime < time.time() - self.max_lock_age:
                        try:
                            os.rmdir(self.lock_path)
                        except:
                            # If we did not remove the lock, someone else is at the same point and contending.
                            # Let them win.
                            time.sleep(poll_time)

        if success is True:
            self.acquired_at = time.time()

        self.held = success
        return success

    def release(self, force_release=False):
        """
        Release the lock.
        :param force_release: (bool) If True, will release the lock even if we don't hold it.
        :return: True if lock is released, otherwise False
        """
        if not self.held:
            if force_release is False:
                return False  # We were not holding the lock
            else:
                self.held = True  # If we have force release set, pretend like we held its

        if not os.path.exists(self.lock_path):
            self.held = False
            self.acquired_at = None
            return True

        if force_release is False:
            # We waited too long and lost the lock
            if self.max_lock_age and time.time() > self.acquired_at + self.max_lock_age:
                self.held = False
                self.acquired_at = None
                return False

        self.acquired_at = None

        try:
            os.rmdir(self.lock_path)
            self.held = False
            return True
        except:
            self.held = False
            return False

    def __checkExpiration(self, mtime=None):
        """
        Check if we have expired
        :param mtime: (int/None) Optional mtime if known, otherwise will be gathered
        :return: rue if we did expire, otherwise False
        """
        if not self.max_lock_age:
            return False

        if mtime is None:
            try:
                mtime = os.stat(self.lock_path).st_mtime
            except FileNotFoundError as e:
                return False

        if mtime < time.time() - self.max_lock_age:
            return True

        return False

    @property
    def is_held(self):
        """
        True if anyone holds the lock, otherwise False.
        :return: If lock is held by anyone
        """
        if not os.path.exists(self.lock_path):
            return False

        try:
            mtime = os.stat(self.lock_path).st_mtime
        except FileNotFoundError as e:
            return False

        if self.__checkExpiration(mtime):
            return False

        return True

    @property
    def has_lock(self):
        """
        Property, returns True if we have the lock, or False if we do not.
        :return: True/False if we have the lock or not.
        """
        # If we don't hold it currently, return False
        if self.held is False:
            return False

        # Otherwise if we think we hold it, but it is not held, we have lost it.
        if not self.is_held:
            self.acquired_at = None
            self.held = False
            return False

        # Check if we expired
        if self.__checkExpiration(self.acquired_at):
            self.acquired_at = None
            self.held = False
            return False

        return True
