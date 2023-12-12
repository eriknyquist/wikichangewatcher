import re
import threading
import requests
import json
import ctypes
import logging
from typing import Callable, Type, Self

from sseclient import SSEClient


logger = logging.getLogger(__name__)

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

    def on_match(self, on_match_handler: Callable[[dict], None]) -> Self:
        """
        Set a function to be called when an edit event matching this filter is seen

        :param on_match_handler: callback function
        """
        self._on_match = on_match_handler
        return self

    def _handler(self, json_data: dict) -> bool:
        raise NotImplementedError

    def check_match(self, json_data: dict) -> bool:
        """
        Check if an edit event matches this filter

        :param json_data: Edit event to check

        :return: True if match
        :rtype: bool
        """
        return self._handler(json_data)

    def run_on_match(self, json_data: dict):
        """
        Check if edit event matches this filter, and run on_match handler if it does match.

        :param json_data: Edit event to check
        """
        if self._on_match is not None:
            self._on_match(json_data)

    def _combine(self, this, other, match_type):
        self_collection = isinstance(this, FilterCollection)
        other_collection = isinstance(other, FilterCollection)
        self_filter = isinstance(this, FieldFilter) and (not self_collection)
        other_filter = isinstance(other, FieldFilter) and (not other_collection)
        self_valid = self_filter or self_collection
        other_valid = other_filter or other_collection

        if (not self_valid) or (not other_valid):
            raise ValueError(f"Cannot combine {self.__class__.__name__} and {other.__class__.__name__} objects")

        elif self_collection and other_collection:
            # Both operands are a filter collection
            if this._match_type == match_type:
                if other._match_type == match_type:
                    filters = this._filters + other._filters
                    return FilterCollection(*filters).set_match_type(match_type)
                else:
                    this._filters.append(other)
                    return this

        if self_filter and other_filter:
            # Both operands are a single filter
            return FilterCollection(this, other).set_match_type(match_type)

        else:
            # one operand is a filter and the other is a collection
            if self_filter:
                filter_obj = this
                collection_obj = other
            else:
                filter_obj = other
                collection_obj = this

            if collection_obj._match_type == match_type:
                collection_obj._filters.append(filter_obj)
                return collection_obj
            else:
                return FilterCollection(collection_obj, filter_obj).set_match_type(match_type)

    def __or__(self, other):
        return self._combine(self, other, MatchType.ANY)

    def __and__(self, other):
        return self._combine(self, other, MatchType.ALL)


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
        """
        :param filters: one or more filter instances to use
        """
        super(FilterCollection, self).__init__()
        self._filters = list(filters)
        self._match_type = MatchType.ALL

    def set_match_type(self, match_type: int) -> Self:
        """
        Set match type for this collection. If MatchType.ALL, then this collection will
        match only if all contained filters match. If MatchType.ANY, then this collection will
        match if one of the contained filters match.

        :match_type: Match type, must be one of the values defined in wikichangewatcher.MatchType
        """
        self._match_type = match_type
        return self

    def _handler(self, json_data: dict) -> bool:
        match = False

        if self._match_type == MatchType.ALL:
            match = all(f.check_match(json_data) for f in self._filters)

        elif self._match_type == MatchType.ANY:
            match = any(f.check_match(json_data) for f in self._filters)

        return match

    def __str__(self):
        params = ','.join(f"{f}" for f in self._filters)
        mtype = "ALL" if self._match_type == MatchType.ALL else "ANY"
        return f"{self.__class__.__name__}({mtype}, {params})"

    def __repr__(self):
        return self.__str__()


def _ipv4_field_tostr(stringval: str) -> int:
    intval = int(stringval)
    if not (0 <= intval <= 255):
        raise ValueError

    return intval


class IpV4Filter(FieldFilter):
    """
    FieldFilter implementation to watch for "user" fields that contain IPv4 addresses
    in the specified ranges
    """
    def __init__(self, ip_addr_pattern="*.*.*.*"):
        """
        IPv4 address pattern to use. Each of the 4 dot-seperated fields may be one of
        the following:

        - A decimal integer from 0 through 255, representing exactly and only the written value.
        - A range of values in the form "0-255" (two decimal integers, both between 0 and 255, separated
          by a dash), representing any value between and including the two written values.
        - An asterisk '\*', representing any value from 0 through 255.

        These can be used in combination. For example:

        - "\*.\*.\*.\*" matches any valid IPv4 address

        - "192.88.99.77" matches only one specific IPv4 address, 192.88.99.77

        - "192.88.0-9.\*" matches 2,550 specific IPv4 addresses:

           192.88.0.0

           192.88.0.1

           192.88.0.2

           ...

           And so on, all the way up to 192.88.9.255
        """
        super(IpV4Filter, self).__init__()
        self.orig_pattern = ip_addr_pattern
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

    def __str__(self):
        return f"{self.__class__.__name__}(\"{self.orig_pattern}\")"

    def __repr__(self):
        return self.__str__()

    def _handler(self, json_data: dict) -> bool:
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


def _ipv6_field_tostr(stringval: str) -> int:
    intval = int(stringval, 16)
    if not (0 <= intval <= 65535):
        raise ValueError

    return intval


class IpV6Filter(FieldFilter):
    """
    FieldFilter implementation to watch for "user" fields that contain IPv6 addresses
    in the specified ranges
    """
    def __init__(self, ip_addr_pattern="*:*:*:*:*:*:*:*"):
        """
        IPv6 address pattern to use. Each of the 8 dot-seperated fields may be one of
        the following:

        - A hexadecimal integer from 0 through ffff, representing exactly and only the written value.
        - A range of values in the form "0-255" (two hexadecimal integers, both between 0 and ffff, separated
          by a dash), representing any value between and including the two written values.
        - An asterisk '\*', representing any value from 0 through ffff.

        These can be used in combination. For example:

        - "\*:\*:\*:\*:\*:\*:\*:\*" matches any valid IPv6 address

        - "00.11.22.33.44.55.66.77" matches only one specific IPv6 address, 00.11.22.33.44.55.66.77

        - "00.11.22.33.44.55.0-9.\*" matches 655,350 specific IPv6 addresses:

           00.11.22.33.44.55.0.0

           00.11.22.33.44.55.0.1

           00.11.22.33.44.55.0.2

           ...

           And so on, all the way up to 00.11.22.33.44.55.9.ffff
        """
        super(IpV6Filter, self).__init__()
        self.orig_pattern = ip_addr_pattern
        self.ip_addr_pattern = []

        for x in ip_addr_pattern.split(":"):
            error = False

            if x == "*":
                self.ip_addr_pattern.append(None)
            else:
                ranges = x.split('-')
                if len(ranges) == 2:
                    try:
                        self.ip_addr_pattern.append((_ipv6_field_tostr(ranges[0]), _ipv6_field_tostr(ranges[1])))
                    except ValueError:
                        error = True

                else:
                    try:
                        self.ip_addr_pattern.append(_ipv6_field_tostr(x))
                    except ValueError:
                        error = True

            if error:
                raise ValueError(f"Invalid field '{x}' in IP address pattern '{ip_addr_pattern}'")

        if len(self.ip_addr_pattern) != 8:
            raise ValueError(f"Invalid number of fields ({len(self.ip_addr_pattern)}) for IP address pattern (expected 8)")

    def __str__(self):
        return f"{self.__class__.__name__}(\"{self.orig_pattern}\")"

    def __repr__(self):
        return self.__str__()

    def _handler(self, json_data: dict) -> bool:
        if "user" not in json_data:
            return False

        ipaddr = json_data["user"]

        try:
            fields = [int(x, 16) for x in ipaddr.split(":")]
        except ValueError:
            return False

        if len(fields) != 8:
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

class FieldRegexSearchFilter(FieldFilter):
    """
    FieldFilter implementation to watch for a named field that contains one or more instances of
    the provided regular expression
    """
    def __init__(self, fieldname: str, regex: str):
        super(FieldRegexSearchFilter, self).__init__()
        self.fieldname = fieldname
        self.regex = re.compile(regex)
        self.regex_string = regex

    def __str__(self):
        return f"{self.__class__.__name__}({self.fieldname}, \"{self.regex_string}\")"

    def __repr__(self):
        return self.__str__()

    def _handler(self, json_data: dict) -> bool:
        if self.fieldname not in json_data:
            return False

        return bool(self.regex.search(json_data[self.fieldname]))


class PageUrlRegexSearchFilter(FieldRegexSearchFilter):
    """
    FieldRegexSearchFilter implementation to watch for a "title_url" field that contains one or more matches of
    a provided regular expression
    """
    def __init__(self, regex: str):
        super(PageUrlRegexSearchFilter, self).__init__("title_url", regex)

    def __str__(self):
        return f"{self.__class__.__name__}(\"{self.regex_string}\")"

    def __repr__(self):
        return self.__str__()


class UsernameRegexSearchFilter(FieldRegexSearchFilter):
    """
    FieldRegexSearchFilter implementation to watch for a "user" field that contains one or more matches of
    a provided regular expression
    """
    def __init__(self, regex: str):
        super(UsernameRegexSearchFilter, self).__init__("user", regex)

    def __str__(self):
        return f"{self.__class__.__name__}(\"{self.regex_string}\")"

    def __repr__(self):
        return self.__str__()


class WikiChangeWatcher(object):
    """
    Consumes all events from the Wikimedia "recent changes" stream, and
    applies all provided FieldFilter instances to each received event.
    """
    def __init__(self, *filters):
        self._thread = None
        self._stop_event = threading.Event()
        self._filters = list(filters)
        self._session = None
        self._client = None
        self._on_edit_handler = None
        self._ignore_log_events = True
        self._retry_count = 0
        self._max_retries = 10
        self._connect()

    def _connect(self):
        self._session = requests.Session()
        self._client = SSEClient(WIKIMEDIA_URL, session=self._session)
        logger.debug(f"connected to {WIKIMEDIA_URL}")

    def on_edit(self, on_edit_handler: Callable[[dict], None]) -> Self:
        """
        Sets handler to run whenever any edit event is received (before any filters are processed)

        :param on_edit_handler: Handler to run on edit event
        """
        self._on_edit_handler = on_edit_handler
        return self

    def set_ignore_log_events(self, ignore: bool) -> Self:
        """
        Set whether log events will be ignored (default if unset is True).

        :param ignore: True to ignore log events, False to ignore nothing.
        """
        self._ignore_log_events = ignore
        return self

    def add_filter(self, fltr: Type[FieldFilter]) -> Self:
        """
        Add a new filter to the list of active filters

        :param fltr: filter instance to add
        """
        self._filters.append(fltr)
        return self

    def run(self):
        """
        Start WikiChangeWatcher running in a separate thread
        """
        if self._thread is not None:
            raise RuntimeError("'run()' has already been called!")

        self._thread = threading.Thread(target=self._thread_task)
        self._thread.daemon = True
        self._thread.start()

    def is_running(self):
        """
        Returns true if WikiChangeWatcher thread is active

        :return: True if thread is active
        :rtype: bool
        """
        if self._thread is None:
            return False

        return self._thread.is_alive()

    def stop(self):
        """
        Send stop event to the running WikiWatcher thread and wait for it to terminate
        """
        if self._thread is None:
            return

        logger.debug("stopping")

        # Use CPython API to inject a SystemExit exception into the WikiWatcher thread.
        # Unfortunately, sseclient lib does not provide any way to terminate waiting for
        # the next event, so this is the only way to stop the thread without having
        # to wait for the next event.
        exception = SystemExit
        target_tid = self._thread.ident

        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), ctypes.py_object(exception))
        if ret == 0:
            raise ValueError("Invalid thread ID")
        elif ret > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(target_tid, NULL)
            raise SystemError("PyThreadState_SetAsyncExc failed")

        self._thread.join()
        self._thread = None

    def _thread_task(self):
        while True:
            try:
                self._event_loop()
            except requests.exceptions.ConnectionError:
                if self._retry_count >= self._max_retries:
                    raise RuntimeError(f"failed to re-connect after {self._max_retries} attempts")
                else:
                    self._retry_count += 1
                    logger.warning(f"stream connection failed, retrying {self._retry_count}/{self._max_retries}")

    def _event_loop(self):
        for event in self._client:
            if self._stop_event.is_set():
                return

            self._retry_count = 0
            if event.event == "message":
                try:
                    change = json.loads(event.data)
                except ValueError:
                    continue

                missing_keys = False
                for key in ["namespace", "user", "title_url"]:
                    if key not in change:
                        missing_keys = True
                        break

                if missing_keys:
                    continue

                if self._ignore_log_events:
                    if change["namespace"] == -1:
                        logger.debug("ignoring log event")
                        continue

                if self._on_edit_handler:
                    self._on_edit_handler(change)

                for f in self._filters:
                    if f.check_match(change):
                        f.run_on_match(change)
