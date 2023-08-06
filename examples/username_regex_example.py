# Example script showing how to use WikiChangeWatcher to watch for NON-"anonymous" edits to any
# wikipedia page, by usernames that contain a string matching a provided regular expression

import time
from wikichangewatcher import WikiChangeWatcher, UsernameRegexSearchFilter

# Callback function to run whenever an edit by a user with a username containing our regex is seen
def match_handler(json_data):
    """
    json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
    as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
    """
    print("{user} edited {title_url}".format(**json_data))

# Watch for edits made by users with "bot" in their username
wc = WikiChangeWatcher(UsernameRegexSearchFilter(r"[Bb]ot|BOT").on_match(match_handler))

wc.run()

# Watch for page edits forever until KeyboardInterrupt
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    wc.stop()
