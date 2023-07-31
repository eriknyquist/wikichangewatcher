WikiChangeWatcher
=================

.. contents:: Table of Contents

.. image:: https://github.com/eriknyquist/wikichangewatcher/raw/master/images/wikichangewatcher_logo.png

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

Monitoring "anonymous" page edits made from specific IP address ranges
----------------------------------------------------------------------

The following example code watches for edits made by 3 specific IPv4 address ranges.

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for "anonymous" edits to any
    # wikipedia page from specific IP address ranges

    import time
    from wikichangewatcher import WikiChangeWatcher, IpV4Filter

    # Callback function to run whenever an event matching our IPv4 address pattern is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    # Watch for anonymous edits from some specific IP address ranges
    wc = WikiChangeWatcher(IpV4Filter("192.60.38.225-230").on_match(match_handler),
                           IpV4Filter("194.60.38.200-205").on_match(match_handler),
                           IpV4Filter("194.60.38.215-219").on_match(match_handler))

    # You can also use the wildcard '*' character within IP addresses; the following line
    # sets up a watcher that triggers on any IP address (all anonymous edits)
    #wc = WikiChangeWatcher(IpV4Filter("*.*.*.*").on_match(match_handler))

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
    from wikichangewatcher import WikiChangeWatcher, IpV4Filter, FilterCollection, MatchType

    # Callback function to run whenever an event matching one of our IPv4 address ranges is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    filters = [
        IpV4Filter("136.200.0-255.0-255").on_match(match_handler),  # IP range assigned to CA dept. of water resources
        IpV4Filter("151.143.0-255.0-255").on_match(match_handler),  # IP range assigned to CA dept. of technology
        IpV4Filter("160.88.0-255.0-255").on_match(match_handler),   # IP range assigned to CA dept. of insurance
        IpV4Filter("192.56.110.0-255").on_match(match_handler),     # IP range #1 assigned to CA dept. of corrections
        IpV4Filter("153.48.0-255.0-255").on_match(match_handler),   # IP range #2 assigned to CA dept. of corrections
        IpV4Filter("149.136.0-255.0-255").on_match(match_handler),  # IP range assigned to CA dept. of transportation
        IpV4Filter("192.251.92.0-255").on_match(match_handler),     # IP range assigned to CA dept. of general services
        IpV4Filter("159.145.0-255.0-255").on_match(match_handler),  # IP range assigned to CA dept. of consumer affairs
        IpV4Filter("167.10.0-255.0-255").on_match(match_handler),   # IP range assigned to CA dept. of justice
        IpV4Filter("192.58.200-203.0-255").on_match(match_handler)  # IP range assigned to Bureau of Justice Statistics in WA
    ]

    wc = WikiChangeWatcher(*filters)

    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()
