from discord_self._vendor.discord.errors import ConnectionClosed
from discord_self._vendor.discord.gateway import (
    DiscordVoiceWebSocket,
    DiscordWebSocket,
    KeepAliveHandler,
    ReconnectWebSocket,
    VoiceKeepAliveHandler,
)

__all__ = [
    "ConnectionClosed",
    "DiscordVoiceWebSocket",
    "DiscordWebSocket",
    "KeepAliveHandler",
    "ReconnectWebSocket",
    "VoiceKeepAliveHandler",
]
