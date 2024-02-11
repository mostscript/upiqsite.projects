# chrome headless

import os
import shutil
import subprocess
import time


CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

BASE_HEADLESS_CHROME_ARGS = [
    '--headless',
    '--enable-logging',
    '--disable-extensions',
    '--print-to-pdf-no-header',
    '--disable-popup-blocking ',
    '--run-all-compositor-stages-before-draw',
    '--disable-checker-imaging',
    '--virtual-time-budget=20000',
]

MAX_SLEEP_SUBPROCESS = 15  # seconds
INTERVAL_CHECK = 0.5  # seconds

def chrome_cmd(url, path):
    """
    Given URL input, and ouput path, get headless chrome command as list
    of args for subprocess.Popen to use
    """
    arg_output = '--print-to-pdf={}'.format(path)
    return [CHROME] + BASE_HEADLESS_CHROME_ARGS + [
        arg_output,
        url,
    ]


def timed_out(_time):
    return _time > MAX_SLEEP_SUBPROCESS


def f_size(path):
    if not os.path.isfile(path):
        return -1
    return os.path.getsize(path)


class ChromeControl:

    def _fetch(self, url, path, attempt=None):
        if attempt is not None:
            path = '{}.{}'.format(path, attempt)
        cmd = chrome_cmd(url, path)
        subprocess.Popen(cmd)
        return path

    def _found(self, paths):
        """Found non-empty files given list of paths"""
        return list(filter(
            lambda p: os.path.isfile(p) and os.path.getsize(p) > 0,
            paths,
        ))

    def _largest(self, paths):
        """Largest file given found paths"""
        return sorted(
            paths,
            reverse=True,
            key=f_size,
        )[0]

    def _cleanup(self, paths):
        for path in paths:
            if os.path.isfile(path):
                os.remove(path)

    def fetch(self, url, path, attempts=1, check_wait=0.5):
        _time = 0
        _paths = []
        if attempts > 1:
            for attempt in range(1, attempts + 1):
                _paths.append(self._fetch(url, path, attempt))
            # wait until all paths rendered or timeout:
            _found = self._found(_paths)
            while len(_found) < len(_paths) or timed_out(_time):
                _time += check_wait
                time.sleep(INTERVAL_CHECK)  # seconds
                _found = self._found(_paths)
            # if no paths, we hit timeout with nothing, log and move on:
            if not _found:
                log.warning('Unable to make PDF for path: {}'.format(path))
                return None
            # pick biggest file, move it to path:
            _path_to_largest = self._largest(_found)
            if os.path.isfile(path):
                os.remove(path)  # remove existing at dest path before replace
            shutil.move(_path_to_largest, path)
            self._cleanup(_found)
        else:
            self._fetch(url, path)
        return path


def pdfget(url, path, attempts=1):
    return ChromeControl().fetch(url, path, attempts)

