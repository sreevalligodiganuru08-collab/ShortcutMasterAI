try:
    from .collector import ProductivityEventCollector, anonymize_event
except ImportError:
    from collector import ProductivityEventCollector, anonymize_event


class DesktopMonitor:
    def __init__(self, collector=None):
        self.collector = collector or ProductivityEventCollector()

    def snapshot(self):
        payload = self.collector.collect_snapshot()
        payload["events"] = [anonymize_event(event) for event in payload.get("events", [])]
        return payload
