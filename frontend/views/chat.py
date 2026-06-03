import streamlit as st
import requests
import api_client
from config import PROVIDERS_MODELS, PROVIDER_BADGE

def render():
    # --- SESSION STATE INITIALIZATION ---
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "conversations" not in st.session_state:
        st.session_state.conversations = []
    
    # Track which conversation is currently being edited
    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None
        
    # Message settings state
    if "provider" not in st.session_state:
        st.session_state.provider = "deepseek"
    if "model" not in st.session_state:
        st.session_state.model = "deepseek-v4-flash"
    if "stream_enabled" not in st.session_state:
        st.session_state.stream_enabled = True

    def load_conversations():
        try:
            st.session_state.conversations = api_client.get_all_conversations()
        except Exception as e:
            st.error(f"Failed to fetch conversations: {e}")

    # Initial data fetch
    if not st.session_state.conversations:
        load_conversations()

    # --- SIDEBAR UI ---
    with st.sidebar:
        st.title("Chats")
        
        if st.button("➕ New Chat", use_container_width=True):
            try:
                new_chat = api_client.create_conversation("NEW CONVERSATION")
                st.session_state.current_session_id = new_chat["session_id"]
                load_conversations()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create conversation: {e}")

        st.divider()
        st.subheader("Recent")
        
        # List all conversations with select, edit & delete capabilities
        for conv in st.session_state.conversations:
            
            # 1. EDIT MODE UI
            if st.session_state.editing_id == conv['session_id']:
                col1, col2, col3 = st.columns([6, 2, 2])
                with col1:
                    new_title = st.text_input(
                        "Edit Title", 
                        value=conv['title'], 
                        label_visibility="collapsed", 
                        key=f"edit_input_{conv['session_id']}"
                    )
                with col2:
                    if st.button("💾", key=f"save_{conv['session_id']}", use_container_width=True):
                        try:
                            api_client.edit_conversation(conv['session_id'], new_title)
                            st.session_state.editing_id = None
                            load_conversations()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to edit: {e}")
                with col3:
                    if st.button("❌", key=f"cancel_{conv['session_id']}", use_container_width=True):
                        st.session_state.editing_id = None
                        st.rerun()
                        
            # 2. STANDARD READ MODE UI (Updated with 3-dot Popover)
            else:
                # Adjusted column ratio to accommodate the popover neatly
                col1, col2 = st.columns([8, 2])
                with col1:
                    is_active = (st.session_state.current_session_id == conv['session_id'])
                    btn_label = f"**{conv['title']}**" if is_active else conv['title']
                    
                    if st.button(btn_label, key=f"sel_{conv['session_id']}", use_container_width=True):
                        st.session_state.current_session_id = conv['session_id']
                        st.session_state.editing_id = None # Reset edit state on switch
                        st.rerun()
                        
                with col2:
                    # 3-dot Popover menu replaces the separate Edit/Delete buttons
                    with st.popover("⋮", use_container_width=True):
                        if st.button("✏️ Rename", key=f"edit_btn_{conv['session_id']}", use_container_width=True):
                            st.session_state.editing_id = conv['session_id']
                            st.rerun()
                            
                        if st.button("🗑️ Delete", key=f"del_{conv['session_id']}", use_container_width=True):
                            try:
                                api_client.delete_conversation(conv['session_id'])
                                if st.session_state.current_session_id == conv['session_id']:
                                    st.session_state.current_session_id = None
                                load_conversations()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete conversation: {e}")

    # --- MAIN CHAT UI ---
    if not st.session_state.current_session_id:
        st.info("👈 Select or create a new chat from the sidebar to begin.")
        return

    # Find active conversation title
    current_chat = next(
        (c for c in st.session_state.conversations if c["session_id"] == st.session_state.current_session_id), 
        None
    )
    if current_chat:
        st.title(current_chat["title"])

    # Fetch and display chat history
    try:
        messages = api_client.get_messages(st.session_state.current_session_id)
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["message"])
    except Exception as e:
        st.error(f"Failed to load messages: {e}")

    st.write("") # Spacer to push it to the bottom
    
    # Pre-calculate combined provider/model options
    combo_options = []
    for prov, models in PROVIDERS_MODELS.items():
        for mod in models:
            combo_options.append((prov, mod))
            
    # Formatter for the Selectbox
    def format_combo(option):
        prov, mod = option
        badge = PROVIDER_BADGE.get(prov, prov.capitalize())
        return f"{badge} {prov.capitalize()} / {mod}"

    # Determine default index based on current session state
    current_selection = (st.session_state.provider, st.session_state.model)
    default_idx = combo_options.index(current_selection) if current_selection in combo_options else 0

    # Cluster settings: Single dropdown and Stream checkbox
    col1, col2 = st.columns([7, 3])
    with col1:
        selected_combo = st.selectbox(
            "Model Selection",
            options=combo_options,
            index=default_idx,
            format_func=format_combo,
            label_visibility="collapsed" # Hides the label for a cleaner inline look
        )
        # Unpack the tuple back into session state
        st.session_state.provider, st.session_state.model = selected_combo
        
    with col2:
        # Padded with a tiny bit of markdown so it aligns nicely with the selectbox
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        st.session_state.stream_enabled = st.checkbox(
            "Enable Streaming", 
            value=st.session_state.stream_enabled
        )

    # Chat Input Box
    prompt = st.chat_input("Enter your prompt...")

    if prompt and prompt.strip():
        # Render user prompt immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""

            try:
                if st.session_state.stream_enabled:
                    # STREAMING BLOCK
                    with api_client.send_message_stream(
                        session_id=st.session_state.current_session_id,
                        message=prompt,
                        provider=st.session_state.provider,
                        model=st.session_state.model
                    ) as response:
                        
                        for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                            if chunk:
                                full_response += chunk
                                # Added a block cursor "▌" for a smoother visual effect, removed at the end
                                response_container.markdown(full_response + "▌") 
                                
                        response_container.markdown(full_response)
                
                else:
                    # NON-STREAMING BLOCK
                    with st.spinner("Generating response..."):
                        response_data = api_client.send_message(
                            session_id=st.session_state.current_session_id,
                            message=prompt,
                            provider=st.session_state.provider,
                            model=st.session_state.model
                        )
                        
                        # Extracts the message string from the API JSON response
                        full_response = response_data.get("message", response_data.get("response", ""))
                        
                        # Fallback in case the backend returns raw text
                        if not full_response and isinstance(response_data, str):
                            full_response = response_data
                            
                        response_container.markdown(full_response)
                        
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")

        if current_chat and current_chat["title"] == "NEW CONVERSATION":
            # backend will automatically update the title based on the first user message. 
            try:
                load_conversations() 
            except Exception:
                pass
        st.rerun()

if __name__ == "__main__":
    render()