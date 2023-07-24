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

# You can also use the wildcard '*' character within IP addresses; the following line
# sets up a watcher that triggers on any IP address (all anonymous edits)
# wc = WikiChangeWatcher([IpV4Watcher(on_match, "*.*.*.*")])

wc.run()

# Watch for page edits forever until KeyboardInterrupt
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    wc.stop()

