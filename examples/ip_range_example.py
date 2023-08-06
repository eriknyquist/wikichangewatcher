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
    while wc.is_running():
        time.sleep(0.1)
except KeyboardInterrupt:
    wc.stop()
