import streamlit as st


@st.dialog("Debug App")
def debug_app_viewer():
    st.subheader("AppState:")
    st.write(st.session_state.app_state)
    st.divider()
    st.write(f"Number of OCPP Events: {len(st.session_state.app_state.events)}")
