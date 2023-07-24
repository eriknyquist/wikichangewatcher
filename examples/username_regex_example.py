# Example script showing how to use WikiChangeWatcher to watch for NON-"anonymous" edits to any
# wikipedia page, by usernames that contain a string matching a provided regular expression

import time
from wikichangewatcher import WikiChangeWatcher, UsernameRegexSearchWatcher

# Callback function to run whenever an edit by a user with a username containing our regex is seen
def on_match(json_data):
    """
    json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
    as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
    """
    print("{user} edited {title_url}".format(**json_data))

# Watch for edits made by users with "bot" in their username
wc = WikiChangeWatcher([UsernameRegexSearchWatcher(on_match, r"[Bb]ot|BOT")])

wc.run()

# Watch for page edits forever until KeyboardInterrupt
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    wc.stop()

