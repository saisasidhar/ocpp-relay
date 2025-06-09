import collections
import dataclasses
import logging
import threading
import time
import uuid
from typing import Dict, Optional

import redis
import streamlit as st


@dataclasses.dataclass
class Event:
    timestamp: int
    message_name: str
    request: str
    response: Optional[str] = None


_redis = redis.Redis(decode_responses=True)


class RedisBackedAttr:
    def __init__(self, key, data_type, default=None):
        self.key = f"ocpp-relay:{key}"
        self.data_type = data_type
        self.default = default

    def __get__(self, instance, owner):
        val = _redis.get(self.key)
        # if val is None and self.default is not None:
        #     self.__set__(instance, self.default)
        #     return self.default
        return eval(val) if val is not None else self.default

    def __set__(self, instance, value):
        current = _redis.get(self.key)
        if current is None or eval(current) != value:
            _redis.set(self.key, repr(value))


class AppState:
    """..."""

    csms_info: str = RedisBackedAttr("csms_info", data_type=str, default="")
    relay_configured: bool = RedisBackedAttr(
        "relay_configured", data_type=bool, default=False
    )
    relay_connected: bool = RedisBackedAttr(
        "relay_connected", data_type=bool, default=False
    )
    relay_url: str = RedisBackedAttr(
        "relay_url", data_type=str, default="ws://localhost:8500"
    )
    charge_point_id: Optional[str] = RedisBackedAttr(
        "charge_point_id", data_type=str, default=""
    )
    latest_event: Optional[str] = RedisBackedAttr(
        "latest_event", data_type=str, default=""
    )
    relay_connection_manager = None
    events = collections.OrderedDict()
    injected_message_ids = []
    _instance = None

    @classmethod
    def instantiate(cls):
        # singleton
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def introduce_statefulness():
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState.instantiate()
