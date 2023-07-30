import time
import sys
import re
import threading
import json

from sseclient import SSEClient


WIKIMEDIA_URL = 'https://stream.wikimedia.org/v2/stream/recentchange'


class FieldFilter(object):
    """
    Generic/abstract class for checking whether a specific field of the "recent changes"
    JSON event data matches some expected format/values.

    The json_data provided to the on_match callback is an JSON-encoded event from the WikiMedia
    "recent changes" event stream, as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
    """
    def __init__(self):
        self._on_match = None

    def on_match(self, on_match_handler):
        self._on_match = on_match_handler
        return self

    def _handler(self, json_data):
        raise NotImplementedError

    def check_match(self, json_data):
        return self._handler(json_data)

    def run_on_match(self, json_data):
        if self._on_match is not None:
            self._on_match(json_data)


class MatchType(object):
    """
    Enumerates all match types handled by a FilterCollection
    """
    ALL = 0
    ANY = 1


class FilterCollection(FieldFilter):
    """
    A Filter object that holds multiple filters, and can run a callback if all or any one
    of the filters matches
    """
    def __init__(self, *filters):
        super(FilterCollection, self).__init__()
        self._filters = filters
        self._on_all_match_handler = None
        self._on_any_match_handler = None
        self._match_type = MatchType.ALL

    def set_match_type(self, match_type):
        self._match_type = match_type
        return self

    def _handler(self, json_data):
        match = False

        if self._match_type == MatchType.ALL:
            match = all(f.check_match(json_data) for f in self._filters)

        elif self._match_type == MatchType.ANY:
            match = any(f.check_match(json_data) for f in self._filters)

        return match

def _ipv4_field_tostr(stringval):
    intval = int(stringval)
    if not (0 <= intval <= 255):
        raise ValueError

    return intval


class IpV4Filter(FieldFilter):
    """
    FieldWatcher implementation to watch for "user" fields that contain IPv4 addresses
    in the specified ranges
    """
    def __init__(self, ip_addr_pattern="*.*.*.*"):
        super(IpV4Filter, self).__init__()
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


class FieldStringFilter(FieldFilter):
    """
    FieldFilter implementation to watch for a named field with a specific fixed string
    """
    def __init__(self, fieldname, value):
        super(FieldStringFilter, self).__init__()
        self.fieldname = fieldname
        self.value = value

    def _handler(self, json_data):
        if self.fieldname not in json_data:
            return False

        return json_data[self.fieldname] == self.value


class FieldRegexMatchFilter(FieldFilter):
    """
    FieldFilter implementation to watch for a named field that matches a provided regular expression
    """
    def __init__(self, fieldname, regex):
        super(FieldRegexMatchFilter, self).__init__()
        self.fieldname = fieldname
        self.regex = re.compile(regex)

    def _handler(self, json_data):
        if self.fieldname not in json_data:
            return False

        return bool(self.regex.match(json_data[self.fieldname]))


class FieldRegexSearchFilter(FieldFilter):
    """
    FieldFilter implementation to watch for a named field that contains one or more instances of
    the provided regular expression
    """
    def __init__(self, fieldname, regex):
        super(FieldRegexSearchFilter, self).__init__()
        self.fieldname = fieldname
        self.regex = re.compile(regex)

    def _handler(self, json_data):
        if self.fieldname not in json_data:
            return False

        return bool(self.regex.search(json_data[self.fieldname]))


class PageUrlFilter(FieldStringFilter):
    """
    FieldString Filter implementation to watch for a specific page URL
    """
    def __init__(self, page_url):
        super(PageUrlFilter, self).__init__("title_url", page_url)


class PageUrlRegexMatchFilter(FieldRegexMatchFilter):
    """
    FieldRegexMatchFilter implementation to watch for a "title_url" field that matches a provided regular expression
    """
    def __init__(self, regex):
        super(UsernameRegexMatchFilter, self).__init__("title_url", regex)


class PageUrlRegexSearchFilter(FieldRegexSearchFilter):
    """
    FieldRegexSearchFilter implementation to watch for a "title_url" field that contains one or more matches of
    a provided regular expression
    """
    def __init__(self, regex):
        super(UsernameRegexSearchFilter, self).__init__("title_url", regex)


class UsernameFilter(FieldStringFilter):
    """
    FieldStringFilter implementation to watch for a "user" field with a specific fixed string
    """
    def __init__(self, string):
        super(UsernameFilter, self).__init__("user", string)


class UsernameRegexMatchFilter(FieldRegexMatchFilter):
    """
    FieldRegexMatchFilter implementation to watch for a "user" field that matches a provided regular expression
    """
    def __init__(self, regex):
        super(UsernameRegexMatchFilter, self).__init__("user", regex)


class UsernameRegexSearchFilter(FieldRegexSearchFilter):
    """
    FieldRegexSearchFilter implementation to watch for a "user" field that contains one or more matches of
    a provided regular expression
    """
    def __init__(self, regex):
        super(UsernameRegexSearchFilter, self).__init__("user", regex)


class WikiChangeWatcher(object):
    """
    Consumes all events from the Wikimedia "recent changes" stream, and
    applies all provided FieldFilter instances to each received event.
    """
    def __init__(self, *filters):
        self._thread = None
        self._stop_event = threading.Event()
        self._filters = filters

    def add_filter(self, filter):
        self._filters.append(filter)

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

                for f in self._filters:
                    if f.check_match(change):
                        f.run_on_match(change)
