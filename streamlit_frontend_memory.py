import streamlit as st
from langgraph_database_backend import chatbot , retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# ******************************** structured output formatting ***********************************
def _format_content(content):
    if isinstance(content, dict):
        if 'text' in content:
            return content['text']
        if 'content' in content:
            return content['content']
        for v in content.values():
            if isinstance(v, str):
                return v
        return str(content)
    if isinstance(content, (list, tuple)):
        return _format_content(content[0]) if content else ''
    return str(content)

# **************************************** utility functions *************************

def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = retrieve_all_threads()

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )
    if not state or 'messages' not in state.values:
        return []
    return state.values['messages']

# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])

# **************************************** Sidebar UI *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()
    st.rerun()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(
        str(thread_id),
        key=f"thread_{thread_id}"
    ):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages
        st.rerun()

# **************************************** Main UI ************************************

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(_format_content(message['content']))

user_input = st.chat_input('Type here')

if user_input:

    st.session_state['message_history'].append(
        {'role': 'user', 'content': user_input}
    )

    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message("assistant"):
        collected_chunks = []

        for message_chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode="messages"
        ):
            if isinstance(message_chunk, AIMessage):
                text = _format_content(message_chunk.content)
                collected_chunks.append(text)
                st.write(text)

    final_answer = "".join(collected_chunks)

    st.session_state['message_history'].append(
        {'role': 'assistant', 'content': final_answer}
    )