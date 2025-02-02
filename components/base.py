import streamlit as st

from components.debug import debug_app_viewer


def display_base_ui():
    st.markdown(
        """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 0rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        div[data-testid="stDialog"] div[role="dialog"] {
            width: 80vw;
            height: 80vh;
        }
        .stDeployButton {
            visibility: hidden;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("OCPP Relay")
    st.divider()
    if st.sidebar.button("Debug App", icon=":material/integration_instructions:"):
        debug_app_viewer()
    st.sidebar.divider()
