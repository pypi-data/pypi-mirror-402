from __future__ import annotations
__all__ = ['WebsocketSignalsBackgroundJob']
import json
from json.decoder import JSONDecodeError
import threading
from typing import TYPE_CHECKING
from websocket import WebSocketConnectionClosedException
from minfx.neptune_v2.attributes.constants import SIGNAL_TYPE_ABORT, SIGNAL_TYPE_STOP, SYSTEM_FAILED_ATTRIBUTE_PATH
from minfx.neptune_v2.internal.background_job import BackgroundJob
from minfx.neptune_v2.internal.threading.daemon import Daemon
from minfx.neptune_v2.internal.utils import process_killer
from minfx.neptune_v2.internal.utils.logger import get_logger
logger = get_logger()

class WebsocketSignalsBackgroundJob(BackgroundJob):

    def __init__(self, ws_factory):
        self._ws_factory = ws_factory
        self._thread = None
        self._started = False

    def start(self, container):
        self._thread = self._ListenerThread(container, self._ws_factory.create())
        self._thread.start()
        self._started = True

    def stop(self):
        if not self._started:
            return
        self._thread.interrupt()
        self._thread.shutdown_ws_client()

    def pause(self):
        pass

    def resume(self):
        pass

    def join(self, seconds=None):
        if not self._started or threading.get_ident() == self._thread.ident:
            return
        self._thread.join(seconds)
        self._thread.shutdown_ws_client()

    class _ListenerThread(Daemon):

        def __init__(self, container, ws_client):
            super().__init__(sleep_time=0, name='NeptuneWebhooks')
            self._container = container
            self._ws_client = ws_client

        def work(self):
            try:
                raw_message = self._ws_client.recv()
                if raw_message is None or self._is_heartbeat(raw_message):
                    return
                self._handler_message(raw_message)
            except WebSocketConnectionClosedException:
                pass

        def _handler_message(self, msg):
            try:
                json_msg = json.loads(msg)
                msg_type = json_msg.get('type')
                msg_body = json_msg.get('body')
                if not msg_type:
                    logger.error('Malformed websocket signal: missing type')
                    return
                if not isinstance(msg_type, str):
                    logger.error('Malformed websocket signal: type is %s, should be str', type(msg_type))
                    return
                if msg_type.lower() == SIGNAL_TYPE_STOP:
                    self._handle_stop(msg_body)
                elif msg_type.lower() == SIGNAL_TYPE_ABORT:
                    self._handle_abort(msg_body)
            except JSONDecodeError as ex:
                logger.error('Malformed websocket signal: %s, message: %s', ex, msg)

        def _handle_stop(self, msg_body):
            msg_body = msg_body or {}
            if not isinstance(msg_body, dict):
                logger.error('Malformed websocket signal: body is %s, should be dict', type(msg_body))
                return
            run_id = self._container['sys/id'].fetch()
            logger.error('Run %s received stop signal. Exiting', run_id)
            seconds = msg_body.get('seconds')
            self._container.stop(seconds=seconds)
            process_killer.kill_me()

        def _handle_abort(self, msg_body):
            msg_body = msg_body or {}
            if not isinstance(msg_body, dict):
                logger.error('Malformed websocket signal: body is %s, should be dict', type(msg_body))
                return
            run_id = self._container['sys/id'].fetch()
            logger.error('Run %s received abort signal. Exiting', run_id)
            seconds = msg_body.get('seconds')
            self._container[SYSTEM_FAILED_ATTRIBUTE_PATH] = True
            self._container.stop(seconds=seconds)
            process_killer.kill_me()

        def shutdown_ws_client(self):
            self._ws_client.shutdown()

        @staticmethod
        def _is_heartbeat(message):
            return message.strip() == ''