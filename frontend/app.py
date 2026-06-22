import streamlit as st

from state import init_state
from sidebar import render_sidebar
from chat_page import render_chat_page
from modes_page import render_modes_page

st.set_page_config(page_title="ChatBot", page_icon="💬", layout="centered")

init_state()
render_sidebar()

if st.session_state.page == "modes":
    render_modes_page()
else:
    render_chat_page()
