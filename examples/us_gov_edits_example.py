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
