WikiChangeWatcher
=================

Wikipedia provides an `SSE Stream <https://en.wikipedia.org/wiki/Server-sent_events>`_  of
all edits made to any page across Wikipedia, which allows you to watch all edits made to all wikipedia
pages in real time.

``WikiChangeWatcher`` is just a thin wrapper around an SSE client, pointed at the URL for
the SSE stream for wikipedia edits, with some filtering features that allow you to watch for page edit
events with specific attributes (e.g. `"anonymous" <https://en.wikipedia.org/wiki/Wikipedia:IP_edits_are_not_anonymous>`_
edits with IP addresses in specific ranges, or edits made by a wikipedia user whose username matches
a specific regular expression).

Example
=======

The following example code watches for edits made by 3 specific IP address ranges

.. code:: python

    # Example script showing how to use WikiChangeWatcher to watch for "anonymous" edits to any
    # wikipedia page from specific IP address ranges

    import time
    from wikichangewatcher import WikiChangeWatcher, IpV4Watcher

    # Callback function to run whenever an event matching our IPv4 address pattern is seen
    def on_match(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        print("{user} edited {title_url}".format(**json_data))

    # Watch for anonymous edits from some known IP addresses within the UK houses of parliament
    # (taken from https://gist.github.com/Jonty/aabb42ab31d970dfb447, probably old/invalid by now)
    wc = WikiChangeWatcher([IpV4Watcher(on_match, "192.60.38.225-230"),
                            IpV4Watcher(on_match, "194.60.38.200-205"),
                            IpV4Watcher(on_match, "194.60.38.215-219")])
    wc.run()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()

