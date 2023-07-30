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
