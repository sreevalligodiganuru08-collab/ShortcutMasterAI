from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    endpoint_url: str = "https://shortcutmasterai.onrender.com/api/agent/usage/"
    flush_interval_seconds: int = 60
    local_only: bool = True
    app_name: str = "ShortcutMaster Desktop Agent"


DEFAULT_CONFIG = AgentConfig()
