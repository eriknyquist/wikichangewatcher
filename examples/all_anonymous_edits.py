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
wc = WikiChangeWatcher(None, (IpV4Filter() | IpV6Filter()).on_match(match_handler))
wc.run()

# Watch for page edits forever until KeyboardInterrupt
try:
    while wc.is_running():
        time.sleep(0.1)
except KeyboardInterrupt:
    wc.stop()
