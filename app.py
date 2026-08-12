'''
=======
app.py: 
=======
'''

# Imports
# -------

import streamlit as st

from llm_service import generate_sql_query, generate_answer_from_data
from db_service import get_db_schema, execute_sql_query, get_db_dialect



# page configuration
st.set_page_config(page_title="RailPulse AI assistant", page_icon="🚅")
st.title("🚅 RailPulse AI Assistant")


# load db schema in memory once for all
@st.cache_data
def load_db_info():
    schema = get_db_schema()
    dialect = get_db_dialect()
    return schema, dialect




# Main Application
# ----------------

def main():
    '''
    TODO
    '''
    try:
        db_schema, db_dialect = load_db_info()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.stop()


    # LLMs APIs are totally stateless (without any memory)
    # simulation of a fluid conversation appending the messages to a list to create a messages history

    # 'multi-turn' conversation format (on Streamlit)
    # -----------------------------------------------

    # 1. check for st.session_state & conversation history initialization
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # how the reply message from LLM is saved
    # st.session_state.conversation_history.append({
    #     "role": "assistant",
    #     "content": {
    #         "text": "Here are the requested trains...", # <-- "text" key
    #         "df": df_results                            # <-- "df" key
    #     }
    # })
    
    # 2. previous messages rendering (if present)
    for msg in st.session_state.conversation_history:
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], dict) and "text" in msg["content"]:
                # make reply text appear
                st.write(msg["content"]["text"])
                if "df" in msg["content"] and not msg["content"]["df"].empty:
                    # make fetched data appear under the reply text
                    st.dataframe(msg["content"]["df"])
            else:
                st.write(msg["content"])

    # 3. setting st.chat_input as condition for the multi-turn iteration
    # activated when the user enters a message
    if (user_prompt := st.chat_input("Chat with the RailPulse Train Assistant")) is not None: # True when user types and enters a prompt

        # display and save the user msg appending it to history
        st.chat_message("user").write(user_prompt)
        st.session_state.conversation_history.append({"role": "user", "content": user_prompt})

        # Generate and execute
        with st.spinner("I am asking to the SNCB database..."):
            try:
                # --- STEP 1: generate SQL query with `generate_sql_query` backend function ---
                sql_query = generate_sql_query(
                    history=st.session_state.conversation_history, 
                    db_schema=db_schema,
                    db_dialect=db_dialect
                )

                # --- STEP 2: SQL query execution on Azure SQL ---
                df_results = execute_sql_query(sql_query)

                # --- STEP 3: generation of the english response ---
                eng_response = generate_answer_from_data(
                    history=st.session_state.conversation_history,
                    user_prompt=user_prompt,
                    sql_query=sql_query,
                    df=df_results
                )

                # --- STEP 4: rendering UI and saving in history ---
                with st.chat_message("assistant"):
                    st.write(eng_response)
                    # for debugging
                    st.caption(f"**Executed query:** `{sql_query}`")
                    if not df_results.empty:
                        st.dataframe(df_results)

                st.session_state.conversation_history.append({
                    "role": "assistant", 
                    "content": {
                        "text": eng_response,
                        "df": df_results
                    }
                })

            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {e}."
                st.chat_message("assistant").error(error_msg)
                st.session_state.conversation_history.append({
                    "role": "assistant", 
                    "content": error_msg
                })


# Entrypoint
# ----------
if __name__ == "__main__":
    main()