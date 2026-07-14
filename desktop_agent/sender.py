import json
import time
from urllib import request, error


class UsageSender:
    """
    HTTP client for posting telemetry snapshots to Django.
    Includes auto-retry loops to handle transient connection drops.
    """

    def __init__(self, endpoint_url, max_retries=4, backoff_seconds=2):
        self.endpoint_url = endpoint_url
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def send(self, payload):
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.endpoint_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        delay = self.backoff_seconds
        for attempt in range(1, self.max_retries + 1):
            try:
                with request.urlopen(req, timeout=8) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (error.URLError, error.HTTPError) as e:
                if attempt == self.max_retries:
                    # Out of retries, print status and return empty response
                    print(f"[Agent Sender] Error: Max retries reached. Backend failed: {e}")
                    return {"ok": False, "error": str(e)}
                
                print(f"[Agent Sender] Backend unavailable ({e}). Attempt {attempt}/{self.max_retries}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
