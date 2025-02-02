import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from state import Event


def load_example_events():
    example_events_dir = Path(__file__).parent.parent / "example_events"
    for example_event_file in example_events_dir.glob("*.json"):
        id = example_event_file.name.replace(".json", "")
        if id not in st.session_state.app_state.events.keys():
            with example_event_file.open() as f:
                st.session_state.app_state.events[id] = Event(**json.load(f))
            break


def get_ocpp_message_direction(message_name: str) -> str:
    # TODO
    ocpp_16_csms_to_cp = {
        "ChangeAvailability",
        "ChangeConfiguration",
        "ClearCache",
        "DataTransfer",
        "GetCompositeSchedule",
        "GetConfiguration",
        "RemoteStartTransaction",
        "RemoteStopTransaction",
        "Reset",
        "UnlockConnector",
        "UpdateFirmware",
        "SetChargingProfile",
        "ClearChargingProfile",
        "GetDiagnostics",
        "TriggerMessage",
    }
    ocpp_16_cp_to_csms = {
        "Authorize",
        "BootNotification",
        "DataTransfer",
        "DiagnosticsStatusNotification",
        "FirmwareStatusNotification",
        "Heartbeat",
        "MeterValues",
        "StartTransaction",
        "StatusNotification",
        "StopTransaction",
    }
    ocpp_201_csms_to_cp = {
        "GetBaseReport",
        "GetLog",
        "GetReport",
        "SetVariables",
    }
    ocpp_201_cp_to_csms = {
        "LogStatusNotification",
        "NotifyChargingLimit",
        "NotifyEvent",
        "NotifyReport",
    }

    if message_name in ocpp_16_csms_to_cp or message_name in ocpp_201_csms_to_cp:
        return "CSMS → CP"
    elif message_name in ocpp_16_cp_to_csms or message_name in ocpp_201_cp_to_csms:
        return "CP → CSMS"
    else:
        return "Unknown"


@st.dialog("OCPP Event Viewer")
def ocpp_event_viewer(selected_event_id):
    if selected_event_id is not None:
        selected_event: Event = st.session_state.app_state.events[selected_event_id]
        st.subheader(selected_event.message_name)
        st.write(
            f"**Request Timestamp**: {datetime.utcfromtimestamp(selected_event.timestamp).strftime('%Y-%m-%d %H:%M:%S')}Z"
        )
        st.write(
            f"**Message Direction**: {get_ocpp_message_direction(selected_event.message_name)}"
        )
        if selected_event_id in st.session_state.app_state.injected_message_ids:
            st.write("💉 **Injected Message** 💉")
        st.divider()
        left, right = st.columns(2)

        with left:
            st.write("Request")
            if selected_event.request:
                st.json(selected_event.request)
            else:
                st.info("JSON is not available yet for display", icon="ℹ️")

        with right:
            st.write("Response")
            if selected_event.response:
                st.json(selected_event.response)
            else:
                st.info("JSON is not available yet for display", icon="ℹ️")
    else:
        st.write("Select an event to view the complete message")


def show_events_component():
    st.sidebar.header("OCPP Events")

    if st.sidebar.button("Refresh", icon=":material/autorenew:"):
        if st.session_state.app_state.development:
            load_example_events()
    if st.session_state.app_state.events:
        for id, event in reversed(st.session_state.app_state.events.items()):
            ts = datetime.utcfromtimestamp(event.timestamp).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if id in st.session_state.app_state.injected_message_ids:
                txt = f"💉 - {ts}Z - {event.message_name} - 🔍"
            else:
                txt = f"✉️ - {ts}Z - {event.message_name} - 🔍"
            if st.sidebar.button(txt, key=str(event.timestamp) + id):
                ocpp_event_viewer(id)
    else:
        st.sidebar.write("*No events yet*")
