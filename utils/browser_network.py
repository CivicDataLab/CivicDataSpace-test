# utils/browser_network.py
#
# Counting requests the browser actually issued, read from Chrome's performance
# log. Used to assert that the app does not issue runaway request loops - a
# thing that cannot be seen from the DOM and does not fail any ordinary test.

import json
from collections import Counter


def count_requests(driver, substring):
    """Count requests whose URL contains *substring*, grouped by path.

    Reads Network.requestWillBeSent, so it counts what the browser *sent* rather
    than what succeeded - which is the point: a loop that is being rate-limited
    is still sending, and counting only successful responses would hide it.

    The performance log drains when read, so call this once per page load.
    """
    counts = Counter()
    for entry in driver.get_log("performance"):
        try:
            message = json.loads(entry["message"])["message"]
        except (KeyError, ValueError):
            continue
        if message.get("method") != "Network.requestWillBeSent":
            continue
        url = message.get("params", {}).get("request", {}).get("url", "")
        if substring in url:
            path = url.split(substring, 1)[1].split("?")[0]
            counts[path or "/"] += 1
    return counts
