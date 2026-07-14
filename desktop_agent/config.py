from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    endpoint_url: str = "http://127.0.0.1:8000/api/agent/usage/"
    flush_interval_seconds: int = 60
    local_only: bool = True
    app_name: str = "ShortcutMaster Desktop Agent"


DEFAULT_CONFIG = AgentConfig()
