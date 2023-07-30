# Example script showing how to use WikiChangeWatcher to filter page edit events
# by a regular expression match in an arbitrary named field from the JSON event
# provided by the SSE stream of wikipedia page edits

import time
from wikichangewatcher import WikiChangeWatcher, FieldRegexSearchFilter

# Callback function to run whenever an edit is made to a page that has a regex match in the page URL
def match_handler(json_data):
    """
    json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
    as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
    """
    print("{user} edited {title_url}".format(**json_data))

# Watch for edits made to any page that has the word "publish" in the page URL
# ("title_url" field in the JSON object)
wc = WikiChangeWatcher(FieldRegexSearchFilter("title_url", r"[Pp]ublish").on_match(match_handler))

wc.run()

# Watch for page edits forever until KeyboardInterrupt
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    wc.stop()

