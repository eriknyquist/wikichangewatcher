WikiChangeWatcher 1.0.0
=======================

.. |tests_badge| image:: https://github.com/eriknyquist/wikichangewatcher/actions/workflows/tests.yml/badge.svg
.. |cov_badge| image:: https://github.com/eriknyquist/wikichangewatcher/actions/workflows/coverage.yml/badge.svg
.. |version_badge| image:: https://badgen.net/pypi/v/wikichangewatcher
.. |license_badge| image:: https://badgen.net/pypi/license/wikichangewatcher

.. image:: https://raw.githubusercontent.com/eriknyquist/wikichangewatcher/5f8e204db0af39d0a0ed00e5884a38544e11321a/images/wikiwatcher_github_banner.png

.. contents:: Table of Contents

|tests_badge| |cov_badge| |version_badge| |license_badge|

Introduction
============

Wikipedia provides an `SSE Stream <https://en.wikipedia.org/wiki/Server-sent_events>`_  of
all edits made to any page across Wikipedia, which allows you to watch all edits made to all wikipedia
pages in real time.

``WikiChangeWatcher`` is an SSE client that watches the SSE stream of wikipedia page edits,
with some filtering features that allow you to watch for page edit events with specific attributes
(e.g. `"anonymous" <https://en.wikipedia.org/wiki/Wikipedia:IP_edits_are_not_anonymous>`_
edits with IP addresses in specific ranges, or edits made to a specific page, or edits made by a wikipedia
user whose username matches a specific regular expression).

This package is inspired by `Tom Scott's WikiParliament project <https://www.tomscott.com/wikiparliament/>`_.

Install
=======

Install using ``pip``.

::

    pip install wikichangewatcher

Examples
========

Some example scripts illustrating how to use ``WikiChangeWatcher`` are presented in
the following sections.


Monitoring "anonymous" page edits made from any IPv4 or IPv6 address
--------------------------------------------------------------------

The following example code watches for edits made by any IPv4 or IPv6 address.

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for "anonymous" edits to any
    # wikipedia page from any IPv4 or IPv6 address

    import time
    from wikichangewatcher import WikiChangeWatcher, IpV4Filter, IpV6Filter

    # Callback function to run whenever an event matching our IPv4 address pattern is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    # Watch for anonymous edits from any IPv4  or IPv6 address
    wc = WikiChangeWatcher((IpV4Filter() | IpV6Filter()).on_match(match_handler))
    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while wc.is_running():
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()


Monitoring "anonymous" page edits made from specific IP address ranges
----------------------------------------------------------------------

The following example code watches for edits made by 3 specific IPv4 address ranges.

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for "anonymous" edits to any
    # wikipedia page from specific IP address ranges

    import time
    from wikichangewatcher import WikiChangeWatcher, IpV4Filter, IpV6Filter

    # Callback function to run whenever an event matching our IPv4 address pattern is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    # Watch for anonymous edits from some specific IP address ranges
    wc = WikiChangeWatcher(IpV4Filter("192.60.38.225-230").on_match(match_handler),
                           IpV6Filter("2601:205:4882:810:5D1D:BC41:61BB:0-ffff").on_match(match_handler))

    # Wildcard '*' character can be used in place of a IPv4 or IP46 address field, to ignore that field entirely.
    # IPV6 filter with some fields ignored: IpV6Filter("*:*:*:810:5D1D:BC41:*:0-ffff")
    # IPV6 filter with some fields ignored: IpV4Filter("192.*.*.225-230")

    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()

Monitoring page edits made by usernames that match a regular expression
-----------------------------------------------------------------------

The following example code watches for edits made by signed-in users with usernames
that contain one or more strings matching a regular expression.

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for NON-"anonymous" edits to any
    # wikipedia page, by usernames that contain a string matching a provided regular expression

    import time
    from wikichangewatcher import WikiChangeWatcher, UsernameRegexSearchFilter

    # Callback function to run whenever an edit by a user with a username containing our regex is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    # Watch for edits made by users with "bot" in their username
    wc = WikiChangeWatcher(UsernameRegexSearchFilter(r"[Bb]ot|BOT").on_match(match_handler))

    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()

Monitoring page edit events based on regular expression match on arbitary JSON fields
-------------------------------------------------------------------------------------

The following example code watches for any page edit events where the specified JSON
field matches contains one or more matches of a regular expression (available
JSON fields and their descriptions can be found `here <https://www.mediawiki.org/wiki/Manual:RCFeed>`_).

.. code:: python

    # Example script showing how to use WikiChangeWatcher to filter page edit events
    # by a regular expression match in an arbitrary named field from the JSON event
    # provided by the SSE stream of wikipedia page edits

    import time
    from wikichangewatcher import WikiChangeWatcher, FieldRegexSearchFilter

    # Callback function to run whenever an edit is made to a page that has a regex match in the page URL
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    # Watch for edits made to any page that has the word "publish" in the page URL
    # ("title_url" field in the JSON object)
    wc = WikiChangeWatcher(FieldRegexSearchFilter("title_url", r"[Pp]ublish").on_match(match_handler))

    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()


Combining multiple filter classes with the ``FilterCollection`` class
---------------------------------------------------------------------

The following example watches for anonymous page edits to a specific page URL.

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for "anonymous" edits to
    # a specific wikipedia page

    import time
    from wikichangewatcher import WikiChangeWatcher, FilterCollection, IpV4Filter, PageUrlFilter

    # Callback function to run whenever an event matching our filters is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    # Default match type is is MatchType.ALL
    filters = FilterCollection(
        # Filter for any edits to a specific wikipedia page URL
        PageUrlFilter("https://es.wikipedia.org/wiki/Reclus_(La_Rioja)"),

        # Filter for any IP address (any anonymous edit)
        IpV4Filter("*.*.*.*"),
    ).on_match(match_handler)


    wc = WikiChangeWatcher(filters)

    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()

Combining/nesting multiple ``FilterCollection`` classes
-------------------------------------------------------

The following example watches for page edits to several specific page URLs made by
user with the word "bot" in their username.

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for edit to specific
    # wikipedia page URLs by users with the word "bot" in their name

    import time
    from wikichangewatcher import WikiChangeWatcher, FilterCollection, UsernameRegexSearchFilter, PageUrlFilter, MatchType

    # Callback function to run whenever an event matching our filters is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    # Make a filter collection that matches any one of several wikipedia pages
    page_urls = FilterCollection(
        # Filters for any edits to multiple specific wikipedia page URLs
        PageUrlFilter("https://en.wikipedia.org/wiki/Python_(programming_language)"),
        PageUrlFilter("https://en.wikipedia.org/wiki/CPython"),
        PageUrlFilter("https://en.wikipedia.org/wiki/Server-sent_events"),
    ).set_match_type(MatchType.ANY)

    # Make a filter collection that matches one of the page URLs, *and* a specific username regex
    main_filter = FilterCollection(
        page_urls,
        UsernameRegexSearchFilter(r"[Bb][Oo][Tt]")
    ).set_match_type(MatchType.ALL).on_match(match_handler)

    wc = WikiChangeWatcher(main_filter)

    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()

Using bitwise AND/OR operators to create ``FilterCollection`` classes
---------------------------------------------------------------------

Instead of creating FilterCollection classes directly, you can instead use bitwise AND ``&``
and bitwise OR ``|`` to combine filter objects.

For example, this code uses the bitwise OR operator to create a filter that matches any
IPv4 address, *or* any IPv6 address:

.. code:: python

    from wikichangewatcher import IpV4Filter, IpV6Filter

    # Callback function to run whenever an event matching our filters is seen
    def match_handler(json_data):
        print("{user} edited {title_url}".format(**json_data))

    filter_collection = (IpV4Filter() | IpV6Filter()).on_match(match_handler)

And this code creates an equivalent filter, but uses the ``FilterCollection`` class
directly instead:

.. code:: python

    from wikichangewatcher import IpV4Filter, IpV6Filter, FilterCollection, MatchType

    # Callback function to run whenever an event matching our filters is seen
    def match_handler(json_data):
        print("{user} edited {title_url}".format(**json_data))

    filter_collection = FilterCollection(
        IpV4Filter(), IpV6Filter()
    ).set_match_type(MatchType.ANY).on_match(match_handler)

Finally, here is a slightly more complex example, which uses both bitwise AND / OR
operators together to create a filter that matches any IPv4 or IPv6 address, *and* a specific
page URL:

.. code:: python

    from wikichangewatcher import IpV4Filter, IpV6Filter, PageUrlFilter

    PAGE_URL = "https://en.wikipedia.org/wiki/Hayaguchi_Station"

    # Callback function to run whenever an event matching our filters is seen
    def match_handler(json_data):
        print("{user} edited {title_url}".format(**json_data))

    filter_collection = ((IpV4Filter() | IpV6Filter()) & PageUrlFilter(PAGE_URL)).on_match(match_handler)

Monitoring "anonymous" edits made from IP address ranges owned by US government depts./agencies
-----------------------------------------------------------------------------------------------

The following example watches for anonymous page edits to *any* wikipedia page,
from IP address ranges that were found to be publicly listed as owned by various
US government department and agencies (mostly California, some federal).

If you want to look up some IP addresses owned by your local governments, or companies, it's pretty easy,
I just went to ``https://ip-netblocks.whoisxmlapi.com/`` and searched for "california department of"
as the company name.

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for "anonymous" edits to any
    # wikipedia page from IP address ranges that are publicly listed as being owned by various US government departments

    import time
    from wikichangewatcher import WikiChangeWatcher, FilterCollection, IpV4Filter, IpV6Filter, MatchType

    # Callback function to run whenever an event matching one of our IPv4 address ranges is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))


    filter_collection = FilterCollection(
        IpV4Filter("136.200.0-255.0-255"),                                    # IP4 range #1 assigned to CA dept. of water resources
        IpV4Filter("151.143.0-255.0-255"),                                    # IP4 range assigned to CA dept. of technology
        IpV4Filter("160.88.0-255.0-255"),                                     # IP4 range assigned to CA dept. of insurance
        IpV4Filter("192.56.110.0-255"),                                       # IP4 range #1 assigned to CA dept. of corrections
        IpV4Filter("153.48.0-255.0-255"),                                     # IP4 range #2 assigned to CA dept. of corrections
        IpV4Filter("149.136.0-255.0-255"),                                    # IP4 range assigned to CA dept. of transportation
        IpV6Filter("2602:814:5000-5fff:0-ffff:0-ffff:0-ffff:0-ffff:0-ffff"),  # IP6 range assigned CA dept. of transportation
        IpV4Filter("192.251.92.0-255"),                                       # IP4 range #1 assigned to CA dept. of general services
        IpV4Filter("198.22.115.0-255"),                                       # IP4 range #2 assigned to CA dept. of general services
        IpV4Filter("198.22.114.0-255"),                                       # IP4 range #3 assigned to CA dept. of general services
        IpV4Filter("192.251.92.0-255"),                                       # IP4 range #4 assigned to CA dept. of general services
        IpV4Filter("159.145.0-255.0-255"),                                    # IP4 range assigned to CA dept. of consumer affairs
        IpV4Filter("167.10.0-255.0-255"),                                     # IP4 range assigned to CA dept. of justice
        IpV4Filter("192.58.200-203.0-255"),                                   # IP4 range assigned to Bureau of Justice Statistics in WA
        IpV6Filter("2607:f330:0-ffff:0-ffff:0-ffff:0-ffff:0-ffff:0-ffff"),    # IP6 range assigned to the US dept. of justice in WA
        IpV4Filter("64.183.62.236-239"),                                      # IP4 range #1 assigned to CA dept. of food and agriculture
        IpV4Filter("71.74.161.12-15"),                                        # IP4 range #2 assigned to CA dept. of food and agriculture
        IpV4Filter("128.92.251.208-215"),                                     # IP4 range #3 assigned to CA dept. of food and agriculture
        IpV4Filter("69.75.155.212-215"),                                      # IP4 range #4 assigned to CA dept. of food and agriculture
        IpV6Filter("2600:5801:34a:0-ffff:0-ffff:0-ffff:0-ffff:0-ffff"),       # IP6 range #1 assigned to CA dept. of food and agriculture
        IpV6Filter("2600:5801:c129:0-ffff:0-ffff:0-ffff:0-ffff:0-ffff"),      # IP6 range #2 assigned to CA dept. of food and agriculture
        IpV6Filter("2600:5c00:30f5:0-ffff:0-ffff:0-ffff:0-ffff:0-ffff"),      # IP6 range #3 assigned to CA dept. of food and agriculture
        IpV6Filter("2600:5c00:4e3b:0-ffff:0-ffff:0-ffff:0-ffff:0-ffff"),      # IP6 range #4 assigned to CA dept. of food and agriculture
        IpV6Filter("2600:6c2e:eb3:0-ffff:0-ffff:0-ffff:0-ffff:0-ffff"),       # IP6 range #5 assigned to CA dept. of food and agriculture
    ).set_match_type(MatchType.ANY).on_match(match_handler)

    print(f"Using filters: {filter_collection}")
    wc = WikiChangeWatcher(filter_collection)
    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while wc.is_running():
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()

Calculating a running average of page-edits-per-minute for all of wikipedia
---------------------------------------------------------------------------

The following example watches for any edit to any wikipedia page, and updates a
running average of the rate of page edits per minute, which is printed to stdout
once every 5 seconds.

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for "anonymous" edits to any
    # wikipedia page from specific IP address ranges

    import time
    import statistics
    import queue

    from wikichangewatcher import WikiChangeWatcher


    # Max. number of samples in the averaging window
    MAX_WINDOW_LEN = 6

    # Interval between new samples for the averaging window, in seconds
    INTERVAL_SECS = 5


    class EditRateCounter():
        """
        Tracks total number of page edits per minute across all of wikipedia,
        using a simple averaging window
        """
        def __init__(self, interval_secs=INTERVAL_SECS):
            self._edit_count = 0
            self._start_time = None
            self._interval_secs = interval_secs
            self._queue = queue.Queue()
            self._window = []

        # Callback function to run whenever an edit event is seen
        def edit_handler(self, json_data):
            """
            json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
            as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
            """
            self._edit_count += 1

        # Add an edit rate sample to the averaging window, and return the new average
        def _add_to_window(self, edits_per_min):
            self._window.append(edits_per_min)
            if len(self._window) > MAX_WINDOW_LEN:
                self._window.pop(0)

            return statistics.mean(self._window)

        def run(self):
            if self._start_time is None:
                self._start_time = time.time()

            if (time.time() - self._start_time) >= self._interval_secs:
                # interval is up, calculate new rate and put it on the queue
                edits_per_min = float(self._edit_count) * (60.0 / self._interval_secs)
                self._queue.put((self._add_to_window(edits_per_min), self._edit_count))
                self._edit_count = 0
                self._start_time = time.time()

        def get_rate(self):
            ret = None

            try:
                ret = self._queue.get(block=False)
            except queue.Empty:
                pass

            return ret

    # Create rate counter class to monitor page edit rate over time
    ratecounter = EditRateCounter()

    # Create a watcher with no filters-- we want to see every single edit
    wc = WikiChangeWatcher().on_edit(ratecounter.edit_handler)

    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while True:
            ratecounter.run()
            new_rate = ratecounter.get_rate()
            if new_rate:
                rate, since_last = new_rate
                print(f"{rate:.2f} avg. page edits per min. ({since_last} in the last {INTERVAL_SECS} secs)")
    except KeyboardInterrupt:
        wc.stop()


``wikiwatch`` CLI tool
======================

A CLI program called ``wikiwatch`` is provided, which uses the ``wikichangewatcher``
package to provide some monitoring capabilities at the command line:

::

    usage: wikiwatch [-h] [-a ADDRESS] [-u USERNAME_REGEX] [-f FIELD_NAME VALUE_RGX]
                     [-s FORMAT_STRING] [--version]

    Real-time monitoring of global Wikipedia page edits, with flexible filtering
    features.

    options:
      -h, --help            show this help message and exit
      -a ADDRESS, --address ADDRESS
                            Adds an IPv4 or Ipv6 address range to look for. Any
                            anonymous edits made by IP addresses in this range
                            will be displayed. Each dot-separated field (for IPv4
                            addresses) or colon-separated field (for IPv6 addresses)
                            may be optionally replaced with with an asterisk (which
                            acts as a wildcard, matching any value), or a range of
                            values. For example, the address range "*.22.33.0-55"
                            would match all IPv4 addresses in the range 0.22.33.0
                            through 255.22.33.50. This option can be used multiple
                            times to add multiple IP address filters.
      -u USERNAME_REGEX, --username-regex USERNAME_REGEX
                            Adds a username regex to look for. Any edits made by
                            logged-in users with a username that matches this
                            regular expression will be displayed. This option can be
                            used multiple times to add multiple username filters.
      -f FIELD_NAME VALUE_RGX, --field FIELD_NAME VALUE_RGX
                            Adds a regex to look for in a specific named field in
                            the JSON event provided by the wikimedia recent changes
                            stream (described here
                            https://www.mediawiki.org/wiki/Manual:RCFeed). Any edit
                            events which have a value matching the VALUE_RGX regular
                            expression stored in the FIELD_NAME field will be
                            displayed. This option can be used multiple times to add
                            multiple named field filters.
      -s FORMAT_STRING, --format-string FORMAT_STRING
                            Define a custom format string to control how filtered
                            results are displayed. Format tokens may be used to
                            display data from any named field in the JSON event
                            described at
                            https://www.mediawiki.org/wiki/Manual:RCFeed. Format
                            tokens must be in the form "{field_name}", where
                            "field_name" is the name of any field from the JSON
                            event. This option can only be used once (Default:
                            "{user} edited {title_url}").
      --version             Show version and exit.

    NOTE: if run without arguments, then all anonymous edits (any IPv4 or IPv6
    address) will be shown.

    EXAMPLES:

    Show only edits made by one of two specific IP addresses:

        wikiwatch -a 89.44.33.22 -a 2001:0db8:85a3:0000:0000:8a2e:0370:7334

    Show only edits made by IPv4 addresses in the range 88.44.0-33.0-22:

        wikiwatch -a 88.44.0-33.0-22

    Show only edits made by IPv4 addresses in the range 232.22.0-255.0-255:

        wikiwatch -a 232.22.*.*

    Show only edits made by usernames that contain the word "Bot" or "bot":

        wikiwatch -f user "[Bb]ot"

Contributions
=============

Contributions are welcome, please open a pull request at `<https://github.com/eriknyquist/wikichangewatcher/pulls>`_.
You will need to install packages required for development by doing ``pip install -r dev_requirements.txt``.

Please ensure that all existing tests pass, new test(s) are added if required, and the code coverage
check passes.

* Run tests with ``python setup.py test``.
* Run tests and and generate code coverage report with ``python code_coverage.py``
  (this script will report an error if coverage is below 90%)

If you have any questions about / need help with contributions or tests, please
contact Erik at eknyquist@gmail.com.
