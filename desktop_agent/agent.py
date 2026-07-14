import time
import sys

try:
    from .config import DEFAULT_CONFIG
    from .monitor import DesktopMonitor
    from .sender import UsageSender
except ImportError:
    from config import DEFAULT_CONFIG
    from monitor import DesktopMonitor
    from sender import UsageSender


def run_once(config=DEFAULT_CONFIG):
    monitor = DesktopMonitor()
    sender = UsageSender(config.endpoint_url)
    return sender.send(monitor.snapshot())


def run_loop(config=DEFAULT_CONFIG):
    monitor = DesktopMonitor()
    sender = UsageSender(config.endpoint_url)
    print(f"[Agent] Starting {config.app_name} background daemon...")
    print(f"[Agent] Target Endpoint: {config.endpoint_url}")
    print(f"[Agent] Flush Interval: {config.flush_interval_seconds} seconds")
    print("[Agent] Capturing modifier key combos and mouse counts. Press Ctrl+C to terminate.")
    
    try:
        while True:
            time.sleep(config.flush_interval_seconds)
            snapshot = monitor.snapshot()
            
            if snapshot.get("applications") or snapshot.get("events"):
                print(f"[Agent] Flushing telemetry snapshot: {len(snapshot['applications'])} applications, {len(snapshot['events'])} events")
                response = sender.send(snapshot)
                print(f"[Agent] Backend response: {response}")
            else:
                print("[Agent] No activity recorded in this period. Skipping flush.")
    except KeyboardInterrupt:
        print("\n[Agent] Terminating listeners and exiting daemon...")
        if hasattr(monitor.collector, 'running'):
            monitor.collector.running = False
        if hasattr(monitor.collector, 'keyboard_listener'):
            monitor.collector.keyboard_listener.stop()
        if hasattr(monitor.collector, 'mouse_listener'):
            monitor.collector.mouse_listener.stop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        print(run_once())
    else:
        run_loop()
