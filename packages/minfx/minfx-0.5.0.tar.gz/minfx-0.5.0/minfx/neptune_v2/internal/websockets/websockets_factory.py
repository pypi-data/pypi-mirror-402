from __future__ import annotations
__all__ = ['WebsocketsFactory']
import threading
from typing import TYPE_CHECKING
from minfx.neptune_v2.common.websockets.reconnecting_websocket import ReconnectingWebsocket

class WebsocketsFactory:

    def __init__(self, url, session, proxies=None):
        self._url = url
        self._session = session
        self._proxies = proxies

    def create(self):
        return ReconnectingWebsocket(url=self._url, oauth2_session=self._session, shutdown_event=threading.Event(), proxies=self._proxies)