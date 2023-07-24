import time
import sys
import re
import threading
import json

from sseclient import SSEClient


WIKIMEDIA_URL = 'https://stream.wikimedia.org/v2/stream/recentchange'


class FieldWatcher(object):
    """
    Generic/abstract  class for checking whether a specific field of the "recent changes"
    JSON event data matches some expected format/values.

    The json_data provided to the on_match callback is an JSON-encoded event from the WikiMedia
    "recent changes" event stream, as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
    """
    def __init__(self, on_match):
        self._on_match = on_match

    def _handler(self, json_data):
        raise NotImplementedError

    def check_match(self, json_data):
        if self._handler(json_data):
            self._on_match(json_data)


def _ipv4_field_tostr(stringval):
    intval = int(stringval)
    if not (0 <= intval <= 255):
        raise ValueError

    return intval


class IpV4Watcher(FieldWatcher):
    """
    FieldWatcher implementation to watch for "user" fields that contain IPv4 addresses
    in the specified ranges
    """
    def __init__(self, on_match, ip_addr_pattern="*.*.*.*"):
        super(IpV4Watcher, self).__init__(on_match)
        self.ip_addr_pattern = []

        for x in ip_addr_pattern.split("."):
            error = False

            if x == "*":
                self.ip_addr_pattern.append(None)
            else:
                ranges = x.split('-')
                if len(ranges) == 2:
                    try:
                        self.ip_addr_pattern.append((_ipv4_field_tostr(ranges[0]), _ipv4_field_tostr(ranges[1])))
                    except ValueError:
                        error = True

                else:
                    try:
                        self.ip_addr_pattern.append(_ipv4_field_tostr(x))
                    except ValueError:
                        error = True

            if error:
                raise ValueError(f"Invalid field '{x}' in IP address pattern '{ip_addr_pattern}'")

        if len(self.ip_addr_pattern) != 4:
            raise ValueError(f"Invalid number of fields ({len(self.ip_addr_pattern)}) for IP address pattern (expected 4)")

    def _handler(self, json_data):
        if "user" not in json_data:
            return False

        ipaddr = json_data["user"]

        try:
            fields = [int(x) for x in ipaddr.split(".")]
        except ValueError:
            return False

        if len(fields) != 4:
            return False

        for i in range(len(fields)):
            if self.ip_addr_pattern[i] is None:
                continue

            elif type(self.ip_addr_pattern[i]) == tuple:
                range_lo = self.ip_addr_pattern[i][0]
                range_hi = self.ip_addr_pattern[i][1]
                if (fields[i] < range_lo) or (fields[i] > range_hi):
                    return False

            elif self.ip_addr_pattern[i] != fields[i]:
                return False

        return True


class FieldStringWatcher(FieldWatcher):
    """
    FieldWatcher implementation to watch for a named field with a specific fixed string
    """
    def __init__(self, on_match, fieldname, value):
        super(FieldStringWatcher, self).__init__(on_match)
        self.fieldname = fieldname
        self.value

    def _handler(self, json_data):
        if self.fieldname not in json_data:
            return False

        return json_data[self.fieldname] == self.value


class FieldRegexMatchWatcher(FieldWatcher):
    """
    FieldWatcher implementation to watch for a named field that matches a provided regular expression
    """
    def __init__(self, on_match, fieldname, regex):
        super(FieldRegexMatchWatcher, self).__init__(on_match)
        self.fieldname = fieldname
        self.regex = re.compile(regex)

    def _handler(self, json_data):
        if self.fieldname not in json_data:
            return False

        return bool(self.regex.match(json_data[self.fieldname]))


class FieldRegexSearchWatcher(FieldWatcher):
    """
    FieldWatcher implementation to watch for a named field that contains one or more instances of
    the provided regular expression
    """
    def __init__(self, on_match, fieldname, regex):
        super(FieldRegexSearchWatcher, self).__init__(on_match)
        self.fieldname = fieldname
        self.regex = re.compile(regex)

    def _handler(self, json_data):
        if self.fieldname not in json_data:
            return False

        return bool(self.regex.search(json_data[self.fieldname]))


class UsernameStringWatcher(FieldStringWatcher):
    """
    FieldStringWatcher implementation to watch for a "user" field with a specific fixed string
    """
    def __init__(self, on_match, string):
        super(UsernameStringWatcher, self).__init__(on_match, "user", string)


class UsernameRegexMatchWatcher(FieldRegexMatchWatcher):
    """
    FieldRegexMatchWatcher implementation to watch for a "user" field that matches a provided regular expression
    """
    def __init__(self, on_match, regex):
        super(UsernameRegexMatchWatcher, self).__init__(on_match, "user", regex)


class UsernameRegexSearchWatcher(FieldRegexSearchWatcher):
    """
    FieldRegexSearchWatcher implementation to watch for a "user" field that contains one or more matches of
    a provided regular expression
    """
    def __init__(self, on_match, regex):
        super(UsernameRegexSearchWatcher, self).__init__(on_match, "user", regex)


class WikiChangeWatcher(object):
    """
    Consumes all events from the Wikimedia "recent changes" stream, and
    applies all provided FieldWatcher instances to each received event.
    """
    def __init__(self, watchers=[]):
        self._thread = None
        self._stop_event = threading.Event()
        self._watchers = watchers

    def add_watcher(self, watcher):
        self._watchers.append(watcher)

    def run(self):
        self._thread = threading.Thread(target=self._thread_task)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def _thread_task(self):
        for event in SSEClient(WIKIMEDIA_URL):
            if self._stop_event.is_set():
                return

            if event.event == "message":
                try:
                    change = json.loads(event.data)
                except ValueError:
                    continue

                for w in self._watchers:
                    w.check_match(change)
