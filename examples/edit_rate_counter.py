# Example script showing how to use WikiChangeWatcher to watch for "anonymous" edits to any
# wikipedia page from specific IP address ranges

import time
import statistics
import queue

from wikichangewatcher import WikiChangeWatcher


# Max. number of samples in the averaging window
MAX_WINDOW_LEN = 6

# Interval between new samples for the averaging window, in seconds
INTERVAL_SECS = 5


class EditRateCounter():
    """
    Tracks total number of page edits per minute across all of wikipedia,
    using a simple averaging window
    """
    def __init__(self, interval_secs=INTERVAL_SECS):
        self._edit_count = 0
        self._start_time = None
        self._interval_secs = interval_secs
        self._queue = queue.Queue()
        self._window = []

    # Callback function to run whenever an edit event is seen
    def edit_handler(self, json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        self._edit_count += 1

    # Add an edit rate sample to the averaging window, and return the new average
    def _add_to_window(self, edits_per_min):
        self._window.append(edits_per_min)
        if len(self._window) > MAX_WINDOW_LEN:
            self._window.pop(0)

        return statistics.mean(self._window)

    def run(self):
        if self._start_time is None:
            self._start_time = time.time()

        if (time.time() - self._start_time) >= self._interval_secs:
            # interval is up, calculate new rate and put it on the queue
            edits_per_min = float(self._edit_count) * (60.0 / self._interval_secs)
            self._queue.put((self._add_to_window(edits_per_min), self._edit_count))
            self._edit_count = 0
            self._start_time = time.time()

    def get_rate(self):
        ret = None

        try:
            ret = self._queue.get(block=False)
        except queue.Empty:
            pass

        return ret


# Create rate counter class to monitor page edit rate over time
ratecounter = EditRateCounter()

# Create a watcher with no filters-- we want to see every single edit
wc = WikiChangeWatcher().on_edit(ratecounter.edit_handler)

wc.run()

# Watch for page edits forever until KeyboardInterrupt
try:
    while wc.is_running():
        ratecounter.run()
        new_rate = ratecounter.get_rate()
        if new_rate:
            rate, since_last = new_rate
            print(f"{rate:.2f} avg. page edits per min. ({since_last} in the last {INTERVAL_SECS} secs)")
except KeyboardInterrupt:
    wc.stop()
