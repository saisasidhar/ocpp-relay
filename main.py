import logging
import sys

import streamlit as st

from components.base import display_base_ui
from components.configuration import show_configuration_component
from components.events import ocpp_event_viewer, show_events_component
from components.injection import show_message_injection_component
from state import Event, introduce_statefulness

st.set_page_config(page_title="OCPP Relay", layout="wide")


def main():
    display_base_ui()
    introduce_statefulness()
    configured_successfully = show_configuration_component()
    if configured_successfully:
        show_events_component()
        show_message_injection_component()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)-4.4s] - [%(threadName)-9.9s] - [%(name)-20.20s] - %(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main()
