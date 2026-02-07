import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage
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

# ******************************** utility functions ***********************************

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    add_thread(thread_id)

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        st.session_state['thread_titles'].setdefault(thread_id, "New Chat")

def load_conversation(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )
    if not state or 'messages' not in state.values:
        return []
    return state.values['messages']

# ******************************** session setup ***********************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

if 'thread_titles' not in st.session_state:
    st.session_state['thread_titles'] = {}

add_thread(st.session_state['thread_id'])

# ******************************** sidebar ui ***********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()
    st.rerun()

st.sidebar.header('My conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    title = st.session_state['thread_titles'].get(thread_id, "New Chat")

    if st.sidebar.button(title, key=f"thread_{thread_id}"):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages
        st.rerun()

# ******************************** Main UI ***********************************

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(_format_content(message['content']))

user_input = st.chat_input('Type here')

if user_input:

    tid = st.session_state['thread_id']
    if tid not in st.session_state['thread_titles']:
        st.session_state['thread_titles'][tid] = user_input[:30]

    st.session_state['message_history'].append(
        {'role': 'user', 'content': user_input}
    )

    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('assistant'):
        collected_chunks = []

        for message_chunk, metadata in chatbot.stream(
            {'messages': [HumanMessage(content=user_input)]},
            config={'configurable': {'thread_id': st.session_state['thread_id']}},
            stream_mode='messages'
        ):
            text = _format_content(message_chunk.content)
            collected_chunks.append(text)
            st.write(text)

    final_answer = ''.join(collected_chunks)

    st.session_state['message_history'].append(
        {'role': 'assistant', 'content': final_answer}
    )