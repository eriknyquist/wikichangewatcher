# Example script showing how to use WikiChangeWatcher to plot the average number
# of wikipedia page edits over time

import time
import statistics
import queue
from datetime import datetime

from wikichangewatcher import WikiChangeWatcher
import matplotlib.pyplot as plt

# Max. number of samples in the averaging window
MAX_WINDOW_LEN = 10

# Interval between new samples for the averaging window, in seconds
INTERVAL_SECS = 10


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
            self._queue.put((time.time(), self._add_to_window(edits_per_min), edits_per_min, self._edit_count))
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

timestamps = []
avg_rates = []
raw_rates = []

# Watch for page edits forever until KeyboardInterrupt
try:
    while wc.is_running():
        ratecounter.run()
        new_rate = ratecounter.get_rate()
        if new_rate:
            ts, avg_rate, raw_rate, since_last = new_rate
            timestamps.append(datetime.fromtimestamp(ts))
            avg_rates.append(avg_rate)
            raw_rates.append(raw_rate)
            print(f"edits_per_min_avg={avg_rate:.2f} edits_per_min_raw={raw_rate:.2f} edits_since_last={since_last}")
except KeyboardInterrupt:
    wc.stop()

    # Make plot
    plt.title("Number of Wikipedia page edits per minute vs. UTC time")
    plt.plot(timestamps, raw_rates, label="Raw page edit rate", linestyle='--')
    plt.plot(timestamps, avg_rates, label="Avg. page edit rate")
    plt.ylabel("Page edits per minute")
    plt.xlabel("UTC time")
    plt.legend()
    plt.show()
