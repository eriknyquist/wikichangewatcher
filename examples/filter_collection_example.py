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
