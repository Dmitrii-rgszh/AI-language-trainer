from __future__ import annotations

from aiortc import RTCConfiguration, RTCIceServer

from app.core.config import settings


def build_rtc_configuration() -> RTCConfiguration:
    ice_servers: list[RTCIceServer] = []

    if settings.webrtc_stun_urls:
        ice_servers.append(RTCIceServer(urls=settings.webrtc_stun_urls))

    if settings.webrtc_turn_urls:
        ice_servers.append(
            RTCIceServer(
                urls=settings.webrtc_turn_urls,
                username=settings.webrtc_turn_username or None,
                credential=settings.webrtc_turn_password or None,
            )
        )

    return RTCConfiguration(iceServers=ice_servers)
