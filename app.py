'''
=======
app.py: 
=======
'''

# Imports
# -------

import streamlit as st

from llm_service import generate_sql_query
from db_service import get_db_schema



# Functions
# ---------


# load db schema in memory once for all
@st.cache_data
def load_schema() -> str:
    return get_db_schema()

db_schema = load_schema()


# Main Application
# ----------------

def main():
    '''
    TODO
    '''

    # LLMs APIs are totally stateless (without any memory)
    # simulation of a fluid conversation appending the messages to a list to create a messages history

    # 'multi-turn' conversation format (on Streamlit)
    # -----------------------------------------------

    # 1. check for st.session_state & conversation history initialization
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # 2. previous messages rendering (if present)
    for msg in st.session_state.conversation_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 3. setting st.chat_input as condition for the multi-turn iteration
    # activated when the user enters a message
    if (user_prompt := st.chat_input("Chat with the RailPulse train assistant")) is not None: # True when user types and enters a prompt

        # display and save the user msg appending it to history
        st.chat_message("user").write(user_prompt)
        st.session_state.conversation_history.append({"role": "user", "content": user_prompt})

        # generate SQL query with `generate_sql_query` backend function
        sql_query = generate_sql_query(history=st.session_state.conversation_history, db_schema=db_schema)


        # display and save the assistant reply
        st.chat_message("assistant").write(sql_query)
        st.session_state.conversation_history.append({"role": "assistant", "content": sql_query})


# Entrypoint
# ----------
if __name__ == "__main__":
    main()