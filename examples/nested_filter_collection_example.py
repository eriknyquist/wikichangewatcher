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

