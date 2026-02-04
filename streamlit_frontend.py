import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

# st.session_state -> dict -> 
CONFIG = {'configurable': {'thread_id': 'thread-1'}}


def _format_content(content):
    """Return only the human-readable text from a message content blob.
    Handles dicts with 'text'/'content', lists, and plain strings.
    """
    if isinstance(content, dict):
        if 'text' in content:
            return content['text']
        if 'content' in content:
            return content['content']
        # fallback: try to find any string value
        for v in content.values():
            if isinstance(v, str):
                return v
        return str(content)
    if isinstance(content, (list, tuple)):
        return _format_content(content[0]) if content else ''
    return str(content)

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(_format_content(message['content']))

#{'role': 'user', 'content': 'Hi'}
#{'role': 'assistant', 'content': 'Hi=ello'}

user_input = st.chat_input('Type here')

if user_input:

    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]}, config=CONFIG)
    content = response['messages'][-1].content
    formatted = _format_content(content)
    # store only the human-readable text in history
    st.session_state['message_history'].append({'role': 'assistant', 'content': formatted})
    with st.chat_message('assistant'):
        st.text(formatted)