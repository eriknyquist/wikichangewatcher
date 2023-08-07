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

wc = WikiChangeWatcher(filter_collection)
wc.run()

# Watch for page edits forever until KeyboardInterrupt
try:
    while wc.is_running():
        time.sleep(0.1)
except KeyboardInterrupt:
    wc.stop()
