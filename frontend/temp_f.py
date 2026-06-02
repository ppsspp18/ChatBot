import requests
import streamlit as st

BACKEND_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(
    page_title="Simple Chatbot",
    layout="centered"
)

st.title("Simple Chatbot")

prompt = st.text_input("Enter your prompt")

if st.button("Send"):

    if prompt.strip():

        response_container = st.empty()

        full_response = ""

        try:

            with requests.post(
                BACKEND_URL,
                json={"prompt": prompt},
                stream=True,
                timeout=60
            ) as response:

                for chunk in response.iter_content(
                    chunk_size=1,
                    decode_unicode=True
                ):

                    if chunk:

                        full_response += chunk

                        response_container.markdown(full_response)

        except requests.exceptions.RequestException as e:

            st.error(f"Request failed: {e}")

    else:
        st.warning("Please enter a prompt before sending.")
