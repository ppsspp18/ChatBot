import streamlit as st
from views import chat

st.set_page_config(
    page_title="Custom Chatbot",
    layout="centered"
)

def main():
    chat.render()

if __name__ == "__main__":
    main()