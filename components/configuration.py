import base64
import json
import logging
import os
import re
import threading
import time

import streamlit as st
import websocket
from streamlit_ace import st_ace

from state import Event


class RelayConnectionManager:
    def __init__(self, connection_url):
        self.connection_url = connection_url
        self.connected_event = threading.Event()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.logger = logging.getLogger(RelayConnectionManager.__qualname__)
        self.logger.info("Starting RelayConnectionManager's thread")
        self.thread.start()

    def run(self):
        while not self.stop_event.is_set():
            ws = websocket.WebSocketApp(
                self.connection_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_close=self.on_close,
                on_error=self.on_error,
            )
            self.logger.info(
                f"Trying to open a connection to the relay at {self.connection_url}"
            )
            ws.run_forever()
            if not self.connected_event.is_set():
                self.logger.info(
                    "Opening a connection to relay failed. Retrying in 3 seconds"
                )
                time.sleep(3)

        self.logger.info("Closing websocket connection to the relay")
        ws.close()

    def stop(self):
        self.stop_event.set()
        self.logger.info("Stop event set, waiting for thread it join")
        self.thread.join(timeout=10)
        self.logger.info("RelayConnectionManager's Thread join complete")

    def on_open(self, ws):
        self.connected_event.set()
        st.session_state.app_state.relay_connected = True

    def on_message(self, ws, ws_message_str):
        ws_message = json.loads(ws_message_str)
        if isinstance(ws_message, dict):
            event = ws_message.get("event", None)
            if event == "Connection":
                ts = ws_message.get("timestamp")
                cp_id = ws_message.get("payload").get("charge_point_id")
                ws_subp = ws_message.get("payload").get("ws_subprotocol")
                st.session_state.app_state.charge_point_id = cp_id
                st.session_state.app_state.latest_event = f"OCPP-Relay is now actively relaying {ws_subp} messages on behalf of **{cp_id}** since {ts}"
            elif event == "Disconnection":
                ts = ws_message.get("timestamp")
                cp_id = st.session_state.app_state.charge_point_id
                st.session_state.app_state.charge_point_id = ""
                st.session_state.app_state.latest_event = (
                    f"**{cp_id}** disconnected from OCPP-Relay at {ts}"
                )
        else:
            ocpp_message = ws_message
            message_type = ocpp_message[0]
            message_id = ocpp_message[1]
            timestamp = int(time.time())
            if message_type == 2:  # Request
                message_name = ocpp_message[2]
                st.session_state.app_state.events[message_id] = Event(
                    timestamp=timestamp,
                    message_name=message_name,
                    request=ws_message_str,
                )
            else:
                st.session_state.app_state.events[message_id].response = ws_message_str

    def on_close(self, ws, sc, msg):
        self.connected_event.clear()

    def on_error(self, ws, error):
        self.connected_event.clear()
        time.sleep(3)


def setup_relay(csms_info):
    csms_info_b64 = base64.b64encode(json.dumps(csms_info).encode("ascii")).decode(
        "ascii"
    )
    connection_url = f"{st.session_state.app_state.relay_url}/streamlit/{csms_info_b64}"
    rcm = RelayConnectionManager(connection_url)
    st.session_state.app_state.relay_connection_manager = rcm
    st.runtime.scriptrunner.add_script_run_ctx(rcm.thread)
    st.session_state.app_state.relay_configured = True


def show_configuration_component() -> bool:
    def _validate_csms_url(url):
        match = re.match(
            r"wss?:\/\/(?:[a-zA-Z0-9.-]+|\[[a-fA-F0-9:]+\])(?::\d+)?(?:\/[^\s]*)?", url
        )
        return bool(match)

    with st.form("configuration"):
        url_col, id_col, pass_col = st.columns([3, 1, 1])
        with url_col:
            csms_url = st.text_input(
                "Enter your CSMS base URL (i.e without the CP identifier, such as `wss://example.com/ocpp`):",
                disabled=bool(st.session_state.app_state.csms_info),
            )
        with id_col:
            csms_id = st.text_input(
                "Enter your BasicAuth ID:",
                disabled=bool(st.session_state.app_state.csms_info),
            )
        with pass_col:
            csms_pass = st.text_input(
                "Enter your BasicAuth Password:",
                disabled=bool(st.session_state.app_state.csms_info),
                type="password",
            )
        submitted = st.form_submit_button(
            "Submit", disabled=bool(st.session_state.app_state.csms_info)
        )
        if submitted:
            if not _validate_csms_url(csms_url):
                st.error("Invalid CSMS URL")
            else:
                st.session_state.app_state.csms_info = {
                    "url": csms_url.rstrip("/"),
                    "id": csms_id,
                    "pass": csms_pass,
                }
                st.rerun()

        if st.session_state.app_state.csms_info:
            if not st.session_state.app_state.relay_configured:
                setup_relay(st.session_state.app_state.csms_info)

            if not st.session_state.app_state.relay_connected:
                with st.spinner("Configuring relay..."):
                    time.sleep(3)
                    st.rerun()
            elif not bool(st.session_state.app_state.latest_event):
                st.markdown(
                    f":blue-background[Configure ChargePoint with the following CSMS (Relay) URL: `{st.session_state.app_state.relay_url}`]"
                )
                with st.spinner("Waiting for a ChargePoint to connect to relay..."):
                    time.sleep(3)
                    st.rerun()
            else:
                if bool(st.session_state.app_state.charge_point_id):
                    st.success(st.session_state.app_state.latest_event, icon="🚀")
                else:
                    st.error(st.session_state.app_state.latest_event, icon="🚨")
                return True
