import base64
import json
import os
import re
import threading
import time

import streamlit as st
import websocket
from streamlit_ace import st_ace

from state import Event


def on_open(ws):
    st.session_state.app_state.relay_connected = True


def on_message(ws, ws_message_str):
    ws_message = json.loads(ws_message_str)
    if isinstance(ws_message, dict):
        if ws_message.get("charge_point_id", None):
            st.session_state.app_state.charge_point_id = ws_message.get(
                "charge_point_id"
            )
        if ws_message.get("ws_subprotocol", None):
            st.session_state.app_state.ws_subprotocol = ws_message.get("ws_subprotocol")
    else:
        ocpp_message = ws_message
        message_type = ocpp_message[0]
        message_id = ocpp_message[1]
        timestamp = int(time.time())
        if message_type == 2:  # Request
            message_name = ocpp_message[2]
            st.session_state.app_state.events[message_id] = Event(
                timestamp=timestamp, message_name=message_name, request=ws_message_str
            )
        else:
            st.session_state.app_state.events[message_id].response = ws_message_str


def setup_relay(csms_url):
    # TODO This part requires the relay to be already running. TODO reconnection and better life-cycle management
    st.session_state.app_state.relay_configured = True
    csms_url_b64 = base64.b64encode(csms_url.encode("ascii")).decode("ascii")
    relay_listener = f"ws://localhost:8500/streamlit/{csms_url_b64}"

    def start_ws():
        ws = websocket.WebSocketApp(
            relay_listener, on_open=on_open, on_message=on_message
        )
        ws.run_forever()

    thread = threading.Thread(target=start_ws, daemon=True)
    st.runtime.scriptrunner.add_script_run_ctx(thread)
    thread.start()


def show_configuration_component() -> bool:
    def _validate_csms_url(url):
        match = re.match(
            r"wss?:\/\/(?:[a-zA-Z0-9.-]+|\[[a-fA-F0-9:]+\])(?::\d+)?(?:\/[^\s]*)?", url
        )
        return bool(match)

    csms_url = st.text_input(
        "Enter your CSMS base URL (i.e without the CP identifier, such as `wss://example.com/ocpp`):",
        disabled=bool(st.session_state.app_state.csms_url),
    )

    if csms_url:
        if not _validate_csms_url(csms_url):
            st.error("Invalid CSMS URL")
        else:
            st.session_state.app_state.csms_url = csms_url.rstrip("/")
            if not st.session_state.app_state.relay_configured:
                setup_relay(st.session_state.app_state.csms_url)

            if not st.session_state.app_state.relay_connected:
                st.markdown(
                    f":blue-background[Configure ChargePoint with the following CSMS (Relay) URL: `{st.session_state.app_state.relay_url}`]"
                )
                with st.spinner("Configuring relay..."):
                    time.sleep(3)
                    st.rerun()
            elif not bool(st.session_state.app_state.charge_point_id):
                st.markdown(
                    f":blue-background[Configure ChargePoint with the following CSMS (Relay) URL: `{st.session_state.app_state.relay_url}`]"
                )
                with st.spinner("Waiting for a ChargePoint to connect to relay..."):
                    time.sleep(3)
                    st.rerun()
            else:
                st.success(
                    f"OCPP-Relay is now actively relaying messages on behalf of {st.session_state.app_state.charge_point_id}",
                    icon="✅",
                )
                return True
