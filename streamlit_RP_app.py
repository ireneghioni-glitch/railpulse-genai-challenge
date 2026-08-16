import base64
import mimetypes
import os
import streamlit as st

from llm_service import generate_sql_query, generate_answer_from_data
from db_service import get_db_schema, execute_sql_query, get_db_dialect


IMAGE_DIR = "assets"


# Page setup
st.set_page_config(
    page_title="RailPulse AI Assistant",
    page_icon="🚅",
    layout="centered"
)


# Function to retrieve the absolute and secure path to the images.
def get_image_path(filename: str) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, IMAGE_DIR, filename)
    if os.path.exists(file_path):
        return file_path
    return filename


# Secure Base64 converter for perfect centering via HTML Flexbox
def get_base64_image(filename: str) -> str:
    file_path = get_image_path(filename)
    if os.path.exists(file_path):
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "image/png"
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime_type};base64,{encoded}"
        except Exception:
            return ""
    return ""


# Personalized CSS
st.markdown("""
    <style>
        /* Sfondo generale dark */
        .stApp {
            background-color: #0b0f17 !important;
            color: #f0f6fc !important;
        }
        
        /* Nasconde la top bar di Streamlit */
        header {visibility: hidden;}
        
        /* Stile dei box messaggi inviati (testo bianco su sfondo scuro) */
        div[data-testid="stChatMessage"] {
            background-color: #161b22 !important;
            border-radius: 12px !important;
            border: 1px solid #30363d !important;
            padding: 12px 16px !important;
            margin-bottom: 12px !important;
        }
        
        /* Testo bianco/chiaro per i messaggi gia inviati in chat */
        div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] span {
            color: #f0f6fc !important;
        }

        /* Codice della query visibile e leggibile */
        div[data-testid="stChatMessage"] code {
            color: #58a6ff !important;
            background-color: #21262d !important;
            padding: 2px 6px !important;
            border-radius: 4px !important;
        }

        /* Styling dell'area di input (Chat Box) */
        div[data-testid="stChatInput"] {
            border: 1px solid #d0d7de !important;
            border-radius: 12px !important;
        }

        /* TESTO SCURO MENTRE SI SCRIVE NELL'INPUT BOX */
        div[data-testid="stChatInput"] textarea {
            color: #0f172a !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
        }

        /* Placeholder grigio ben visibile */
        div[data-testid="stChatInput"] textarea::placeholder {
            color: #6e7681 !important;
        }
    </style>
""", unsafe_allow_html=True)


# Load db schema in memory once for all
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

    # 1. Check for st.session_state & conversation history initialization
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # Early evaluation of chat input
    user_prompt = st.chat_input("Chat with the RailPulse Train Assistant")

    # Centered persistent header (RailPulse logo + Powered by SNCB)
    railpulse_src = get_base64_image("RailPulse_logo.png")
    sncb_src = get_base64_image("SNCB_logo.svg.webp")

    if railpulse_src:
        logo_html = f'<img src="{railpulse_src}" style="max-width: 320px; width: 85%; height: auto; display: block; margin: 0 auto 12px auto;">'
    else:
        logo_html = '<h1 style="text-align: center; color: #f0f6fc; margin: 0 0 12px 0;">🚅 RailPulse</h1>'

    if sncb_src:
        sncb_html = f'<img src="{sncb_src}" style="height: 24px; width: auto; vertical-align: middle;">'
    else:
        sncb_html = '<span style="font-size: 1.2rem;">🚆</span>'

    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
            {logo_html}
            <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                {sncb_html}
                <span style="color: #8b949e; font-size: 1.05rem; font-weight: 500; line-height: 1;">Powered by SNCB</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Welcoming (disappears after the first message is sent)
    if len(st.session_state.conversation_history) == 0 and not user_prompt:
        st.markdown(
            """
            <h2 style="text-align: center; font-weight: 400; color: #f0f6fc; margin-top: 30px; font-size: 1.5rem;">
                How can I help you analyze train data today?
            </h2>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    # 2. Previous messages rendering (if present)
    for msg in st.session_state.conversation_history:
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], dict) and "text" in msg["content"]:
                # Make reply text appear
                st.write(msg["content"]["text"])
                if "df" in msg["content"] and not msg["content"]["df"].empty:
                    # Make fetched data appear under the reply text
                    st.dataframe(msg["content"]["df"])
            else:
                st.write(msg["content"])

    # 3. Setting st.chat_input as condition for the multi-turn iteration
    if user_prompt:

        # Display and save the user msg appending it to history
        st.chat_message("user").write(user_prompt)
        st.session_state.conversation_history.append({"role": "user", "content": user_prompt})

        # Generate and execute
        with st.spinner("I am asking to the SNCB database..."):
            try:
                # --- STEP 1: generate SQL query with `generate_sql_query` backend function ---
                sql_query = generate_sql_query(
                    history=st.session_state.conversation_history,
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
                    # For debugging
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