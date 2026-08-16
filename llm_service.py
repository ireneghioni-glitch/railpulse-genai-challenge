'''
===============
llm_service.py: 
===============
'''

# Imports
# -------

import os
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
from langchain_groq import ChatGroq


# helper function
def _format_history(history: list) -> list:
    """
    TODO
    """

    clean_history = []
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        
        # if "content" is the dictionary {"text": ..., "df": ...}, we extract only the value for "text"
        if isinstance(content, dict) and "text" in content:
            content = content["text"]
            
        clean_history.append({"role": role, "content": str(content)})
    return clean_history


# Functions
# ---------

load_dotenv()

def get_llm_client() -> OpenAI:
    '''
    TODO
    '''

    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    api_key = os.getenv("LLM_API_KEY")

    return OpenAI(base_url=base_url, api_key=api_key)

'''
Modern LLM APIs use a **conversation format** or chat format — a list of messages with roles:

- `system`: Sets the context, persona, or rules for the assistant
- `user`: The human's input
- `assistant`: The model's response (used in multi-turn conversations)

**Note**: The Groq SDK is intentionally identical to the OpenAI SDK — same method names, same response structure, same messages format. 
This is deliberate: any code written for OpenAI works on Groq with two changes: the `client import` and the `model name`.


Example:
-------

response = client_groq.chat.completions.create(
    model="llama-3.3-70b-versatile",                                                                # this is stored in .env
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain what a large language model is in 3 sentences."}
    ],
    temperature=0.7,                                                                                # the nearer to 0, the less the creativity, the more accurate the SQL query code
    max_tokens=300
)
print(response.choices[0].message.content)
'''


def generate_sql_query(history: list, db_dialect: str = "SQLite") -> str:
    '''
    TODO
    '''
    # get llm client
    client = get_llm_client()
    # define model (from .env)
    model_name = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    backup_model_name = os.getenv("BACKUP_LLM_MODEL", "llama-3.1-8b-instant")

    # define system prompt (persona)
    # Rileva la regola di limitazione direttamente in Python
    if "SQLite" in db_dialect:
        limit_instruction = "Use 'LIMIT N' at the very end of the query (e.g., ORDER BY count DESC LIMIT 5)."
    else:
        limit_instruction = "STRICTLY use 'SELECT TOP N' right after SELECT (e.g., SELECT TOP 5 s.stop_name...). DO NOT use the word 'LIMIT' anywhere in the query!"

    system_prompt = f'''
            You are an expert Transport Data Analyst specializing in the RailPulse GTFS database.
            Your job is to convert natural language requests into ultra-optimized SQL queries strictly using the {db_dialect} dialect.

            DATABASE SCHEMA & COLUMNS:
            - stops (stop_id, stop_name, stop_lat, stop_lon)
            - stop_times (trip_id, arrival_time, departure_time, stop_id, stop_sequence)  -- NO service_id, NO stop_name
            - trips (trip_id, route_id, service_id, trip_headsign, direction_id)          -- HAS service_id
            - routes (route_id, route_short_name, route_long_name, route_type)
            - calendar_dates (service_id, date, exception_type)

            CRITICAL RESULT LIMITATION RULE:
            {limit_instruction}

            STRICT QUERY RULES FOR MAXIMUM PERFORMANCE:

            1. MANDATORY `day_services` CTE FOR DAYS OF THE WEEK (CRITICAL FOR SPEED):
            Whenever a day of the week is requested, you MUST define `day_services` CTE at the top of the query.
            NEVER calculate `strftime` inside main queries or subqueries.
            
            Template:
            WITH day_services AS (
                SELECT DISTINCT service_id 
                FROM calendar_dates 
                WHERE exception_type = 1 
                    AND strftime('%w', substr(date, 1, 4) || '-' || substr(date, 5, 2) || '-' || substr(date, 7, 2)) = 'X'
            )
            Day mapping 'X': '0'=Sunday, '1'=Monday, '2'=Tuesday, '3'=Wednesday, '4'=Thursday, '5'=Friday, '6'=Saturday.

            2. MANDATORY `station_ids` CTE WHEN A STATION IS MENTIONED:
            WITH station_ids AS (
                SELECT stop_id FROM stops WHERE LOWER(stop_name) LIKE '%term%'
            )

            3. STRICT STRING LITERAL CLEANLINESS:
            - ALWAYS write string search terms clearly with single quotes, e.g. LIKE '%anvers%' or LIKE '%bruxelles-midi%'.
            - NEVER prefix search terms with table aliases or random letters.

            4. BELGIAN STATION NAME MAPPING (EN / FR / NL -> GTFS NAMES):
            - "Antwerp" (EN) / "Antwerpen" (NL) / "Antwerpen-Centraal" (NL) -> LIKE '%anvers%'
            - "Ghent" (EN) / "Gent" (NL) / "Gent-Sint-Pieters" (NL) -> LIKE '%gand%'
            - "Bruges" (EN/FR) / "Brugge" (NL) -> LIKE '%bruges%'
            - "Brussels Midi" / "Brussels South" (EN) / "Brussel-Zuid" (NL) -> LIKE '%bruxelles-midi%'
            - "Brussels Central" (EN) / "Brussel-Centraal" (NL) -> LIKE '%bruxelles-central%'
            - "Brussels North" (EN) / "Brussel-Noord" (NL) -> LIKE '%bruxelles-nord%'
            - "Liège" / "Liege" (EN/FR) / "Luik" / "Luik-Guillemins" (NL) -> LIKE '%liege%'
            - "Namur" (EN/FR) / "Namen" (NL) -> LIKE '%namur%'
            - "Leuven" (EN/NL) / "Louvain" (FR) -> LIKE '%leuven%'

            5. COLUMN ACCURACY & LOGIC:
            - `service_id` belongs ONLY to `trips` and `calendar_dates`. NEVER query `stop_times.service_id` or `st.service_id`.
            - `stop_name` belongs ONLY to `stops`.
            - "Originate" / "Depart from start" -> Add `st.stop_sequence = 1`.
            - "Serve" / "Pass through" / "Stop at" -> DO NOT filter by `stop_sequence`.

            6. OUTPUT FORMAT:
            - Return ONLY the executable SQL query string.
            - Do NOT use markdown code blocks, backticks (```), or explanatory text.
    '''
    # LLMs APIs are totally stateless (without any memory)
    # simulation of a fluid conversation appending the messages to a list to create a messages history

    # definition of messages as the system_prompt + the saved conversation history
    messages = [{"role": "system", "content": system_prompt}] + _format_history(history)

    try:
        # API call
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,  # type: ignore
            temperature=0,      # 0 for ensuring determinism in the generated SQL code
            max_tokens=500      # ideal between 300 and 500 for railpulse objective
        )

    except Exception as e:
        # Check if error is Rate Limit (429)
        if "429" in str(e) or "rate_limit" in str(e).lower():
            print(f"⚠️ Rate limit reached on '{model_name}'. Switching to backup model: '{backup_model_name}'...")
            # Second attempt: Backup model (8B)
            response = client.chat.completions.create(
                model=backup_model_name,
                messages=messages,  # type: ignore
                temperature=0,
                max_tokens=500
            )
        else:
            # If it's a different error (e.g., network issue), raise it
            raise e

    # save llm's answer and append it in history for next turns
    reply = response.choices[0].message.content or ""

    return reply.strip()

def generate_answer_from_data(history: list, user_prompt: str, sql_query: str, df: pd.DataFrame) -> str:
    '''
    '''    
    # get llm client
    client = get_llm_client()
    # define model (from .env)
    model_name = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    # convert data from database to text for the prompt
    data_text = df.to_string(index=False) if not df.empty else "No records were found."

    system_prompt = f"""You are an English-speaking Transport Data Analyst for RailPulse.
    Your task is to answer the user's request based ONLY on the database query results below.

    Executed SQL Query:
    {sql_query}

    Database Query Output:
    {data_text}

    STRICT RULES:
    1. Respond EXCLUSIVELY in English.
    2. Be concise, professional, and clear.
    3. Do NOT show raw SQL syntax in your answer unless the user explicitly requested it.
    """

    # conversation history allignment
    messages = [{"role": "system", "content": system_prompt}] + _format_history(history)

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,  # type: ignore
        temperature=0.3,
        max_tokens=400
    )

    reply = response.choices[0].message.content or ""

    return reply.strip()


# ========================= API CALL TEST =========================

if __name__ == "__main__":
    print("--- Testing LLM API Call ---")
    
    # Schema fittizio di prova
    dummy_schema = """
    Table: trains
      - train_id (int)
      - train_number (varchar)
      - origin (varchar)
      - destination (varchar)
    """
    
    dummy_history = [{"role": "user", "content": "Show all trains departing from Ghent"}]
    
    try:
        # Test 1: Generazione SQL
        generated_sql = generate_sql_query(dummy_history, dummy_schema)
        print("\n Generated SQL Query:")
        print(generated_sql)
        
        # Test 2: Generazione Risposta da Dati Fittizi
        dummy_df = pd.DataFrame([{
            "train_id": 1, 
            "train_number": "FR9601", 
            "origin": "Gand-Saint-Pierre", 
            "destination": "Bruxelles-Midi"
        }])
        
        answer = generate_answer_from_data(
            history=dummy_history,
            user_prompt="Show all trains departing from Ghent",
            sql_query=generated_sql,
            df=dummy_df
        )
        
        print("\n Generated English Answer:")
        print(answer)
        print("\n LLM Service test successful!")

    except Exception as e:
        print(f"\n Error during LLM test: {e}")

# =================================================================

'''
=================================== TEST OUTPUT ===================================

--- Testing LLM API Call ---

Generated SQL Query:
SELECT * FROM trains WHERE origin = 'Ghent'

Generated English Answer:
There is one train departing from Ghent:
- Train Number: FR9601
- Destination: Bruxelles-Midi

LLM Service test successful!

===================================================================================
'''