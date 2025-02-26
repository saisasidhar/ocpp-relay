import json

import streamlit as st
import websocket
from streamlit_ace import st_ace


def show_message_injection_component():
    st.divider()
    st.markdown("#### OCPP Message Injection")
    options = {"CSMS → CP": "csms-cp", "CP → CSMS": "cp-csms"}
    with st.form("injection"):
        left, right = st.columns([1, 4])
        with left:
            direction = st.segmented_control(
                "Select Message Direction:", options.keys(), selection_mode="single"
            )

        with right:
            json_input = st_ace(
                language="json",
                theme="github",
                placeholder="Enter JSON PDU here",
                height=180,
                key="json_input",
                auto_update=True,
            )

        if st.form_submit_button(
            "Inject OCPP Message",
            disabled=not st.session_state.app_state.charge_point_id,
        ):
            if not direction:
                st.error("Select a message direction before injecting a message")
            else:
                try:
                    json_message = json.loads(json_input)
                    if json_message[0] != 2:
                        st.error(
                            "Injected OCPP Message should be a CALL Message i.e Request (2)"
                        )
                    elif type(json_message[1]) != str:
                        st.error("Please make sure message ID is a string")
                    elif (
                        json_message[1]
                        in st.session_state.app_state.injected_message_ids
                    ):
                        st.error(
                            f"The message ID {json_message[1]} is already used. Please use a unique ID"
                        )
                    else:
                        st.session_state.app_state.injected_message_ids.append(
                            json_message[1]
                        )
                        ws = websocket.WebSocket()
                        ws.connect(
                            f"{st.session_state.app_state.relay_url}/inject/{options[direction]}"
                        )
                        ws.send(json_input)
                        ws.close()
                        st.success(
                            f"OCPP Message injected successfully for direction {direction}"
                        )
                except json.JSONDecodeError:
                    st.error("Invalid JSON!")
