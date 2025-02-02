import collections
import dataclasses
import time
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

    development: bool = False
    csms_url: Optional[str] = None
    relay_configured: bool = False
    relay_connected: bool = False
    relay_url: str = "ws://localhost:8500"
    charge_point_id: Optional[str] = ""
    ws_subprotocol: Optional[str] = ""
    events = collections.OrderedDict()


def introduce_statefulness():
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()
