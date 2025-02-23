import collections
import dataclasses
import logging
import threading
import time
import uuid
from typing import Dict, Optional

import streamlit as st


@dataclasses.dataclass
class Event:
    timestamp: int
    message_name: str
    request: str
    response: Optional[str] = None


@dataclasses.dataclass
class AppState:
    """..."""

    csms_info: str = ""
    relay_configured: bool = False
    relay_connected: bool = False
    relay_url: str = "ws://localhost:8500"
    relay_connection_manager = None
    charge_point_id: Optional[str] = ""
    latest_event: Optional[str] = ""
    events = collections.OrderedDict()
    injected_message_ids = []


def introduce_statefulness():
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()
