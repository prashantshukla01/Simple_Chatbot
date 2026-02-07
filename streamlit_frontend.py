import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

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
        for v in content.values():
            if isinstance(v, str):
                return v
        return str(content)
    if isinstance(content, (list, tuple)):
        return _format_content(content[0]) if content else ''
    return str(content)


if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# load conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(_format_content(message['content']))

user_input = st.chat_input('Type here')

if user_input:

    # add user message
    st.session_state['message_history'].append(
        {'role': 'user', 'content': user_input}
    )

    with st.chat_message('user'):
        st.text(user_input)

    # stream assistant response 
    with st.chat_message('assistant'):
        collected_chunks = []

        for message_chunk, metadata in chatbot.stream(
            {'messages': [HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode='messages'
        ):
            text = _format_content(message_chunk.content)
            collected_chunks.append(text)
            st.write(text)

    final_answer = ''.join(collected_chunks)

    # store assistant message
    st.session_state['message_history'].append(
        {'role': 'assistant', 'content': final_answer}
    )