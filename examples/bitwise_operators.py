# Example script showing how to use bitwise AND/OR operators to quickly/easily create
# FilterCollection objects. This example constructs the same filter as
# "nested_filter_collection_example.py", except it combines filters with bitwise
# operators instead of creating FilterCollection instances directly.

import time
from wikichangewatcher import WikiChangeWatcher, UsernameRegexSearchFilter, PageUrlRegexSearchFilter

# Callback function to run whenever an event matching our filters is seen
def match_handler(json_data):
    """
    json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
    as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
    """
    print("{user} edited {title_url}".format(**json_data))

# Make a filter collection that matches any one of several wikipedia pages
page_urls = (PageUrlRegexSearchFilter("https://en.wikipedia.org/wiki/Python_(programming_language)") |
             PageUrlRegexSearchFilter("https://en.wikipedia.org/wiki/CPython") |
             PageUrlRegexSearchFilter("https://en.wikipedia.org/wiki/Server-sent_events"))

# Make a filter collection that matches one of the page URLs, *and* a specific username regex
main_filter = page_urls & UsernameRegexSearchFilter(r"[Bb][Oo][Tt]")

wc = WikiChangeWatcher(None, main_filter)

wc.run()

# Watch for page edits forever until KeyboardInterrupt
try:
    while wc.is_running():
        time.sleep(0.1)
except KeyboardInterrupt:
    wc.stop()
