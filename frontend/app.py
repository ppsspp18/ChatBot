import streamlit as st

from api_client import (
    create_chat,
    get_chats,
    delete_chat,
    send_message,
    get_messages
)

st.set_page_config(
    page_title="AI Chat System",
    layout="wide"
)

# ----------------------------
# SESSION STATE
# ----------------------------

if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None

# ----------------------------
# PAGE TITLE
# ----------------------------

st.title("🚀 AI Chat System")

# ----------------------------
# PROVIDER SELECTION
# ----------------------------

provider = st.sidebar.selectbox(
    "Select Provider",
    [
        "groq",
        "google"
    ]
)

# ----------------------------
# MODEL SELECTION
# ----------------------------

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b"
]

GOOGLE_MODELS = [
    "gemma-4-31b-it",
    "gemini-3.1-flash-lite"
]

if provider == "groq":

    model = st.sidebar.selectbox(
        "Select Model",
        GROQ_MODELS
    )

else:

    model = st.sidebar.selectbox(
        "Select Model",
        GOOGLE_MODELS
    )

# ----------------------------
# CREATE CHAT
# ----------------------------

st.sidebar.markdown("---")
st.sidebar.subheader("➕ Create New Chat")

chat_title = st.sidebar.text_input(
    "Chat Title"
)

if st.sidebar.button("Create Chat"):

    if chat_title.strip() == "":
        st.sidebar.warning("Please enter chat title")

    else:

        response = create_chat(
            chat_title,
            provider,
            model
        )

        st.success("Chat Created")

        st.rerun()

# ----------------------------
# LIST CHATS
# ----------------------------

st.sidebar.markdown("---")
st.sidebar.subheader("💬 Chats")

chats = get_chats()

if len(chats) == 0:

    st.info("No chats found")

for chat in chats:

    col1, col2 = st.sidebar.columns([5, 1])

    with col1:

        if st.button(
            f"📌 {chat['title']}",
            key=chat["_id"]
        ):

            st.session_state.selected_chat = chat["_id"]

    with col2:

        if st.button(
            "❌",
            key=f"delete_{chat['_id']}"
        ):

            delete_chat(chat["_id"])

            if st.session_state.selected_chat == chat["_id"]:
                st.session_state.selected_chat = None

            st.rerun()

# ----------------------------
# MAIN CHAT AREA
# ----------------------------

selected_chat = st.session_state.selected_chat

if selected_chat:

    st.subheader("Conversation")

    messages = get_messages(selected_chat)

    # Display Messages
    for msg in messages:

        with st.chat_message(msg["role"]):

            st.write(msg["content"])

    # Chat Input
    prompt = st.chat_input(
        "Ask something..."
    )

    if prompt:

        # Show user message instantly
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner("Generating response..."):

            send_message(
                selected_chat,
                provider,
                model,
                prompt
            )

        st.rerun()

else:

    st.markdown(
        """
        ## Welcome 👋

        Create a chat from the sidebar and start talking with AI.

        ### Features
        - Multi Provider Support
        - Groq + Google Models
        - MongoDB Storage
        - Chat CRUD Operations
        - Dockerized Setup
        """
    )
