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


def generate_sql_query(history: list, db_schema: str, db_dialect: str = "SQLite") -> str:
    '''
    TODO
    '''
    # get llm client
    client = get_llm_client()
    # define model (from .env)
    model_name = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    # define system prompt (persona)
    system_prompt = f'''
        You are a Transport Data Analyst specialized in the RailPulse database.
        Your only job is to convert user requests in natural language to valid SQL queries using {db_dialect} dialect.

        DATABASE SCHEMA:
        {db_schema}

        STRICT RULES:
        1. Generate ONLY read-only queries (SELECT).
        2. Use strictly syntax compatible with {db_dialect}.
            - If dialect is SQLite: Use LOWER() and LIKE '%term%' for text matching, and strftime() for dates.
            - If dialect is T-SQL / Azure SQL: Use standard SQL Server syntax and date functions.
        3. Schema Relationships & Calendar Logic:
            - `stop_name` exists ONLY in the `stops` table.
            - You MUST JOIN `stop_times` with `stops` ON `stop_times.stop_id = stops.stop_id`.
            - To filter by day of the week, JOIN `trips` with `calendar` ON `trips.service_id = calendar.service_id` and check the day column (e.g. `calendar.friday = 1` or `calendar.friday = '1'`).
            - Do NOT restrict queries with `stop_sequence = 1` unless the user explicitly asks for "origin" or "starting station" (trains departing from a station include intermediate departures).
            - For counting records, use `COUNT(DISTINCT trips.trip_id)` or `COUNT(*)`.
            - ALWAYS use `calendar_dates` (NOT `calendar`) for dates and schedule filtering.
            - `calendar_dates.date` is formatted as 'YYYYMMDD' (text/string, e.g. '20260514').
            - To check day of the week in SQLite from 'YYYYMMDD' string:
                * Convert to 'YYYY-MM-DD': `substr(date, 1, 4) || '-' || substr(date, 5, 2) || '-' || substr(date, 7, 2)`
                * Use `strftime('%w', ...)` to get the day of week:
                  - '0' = Sunday, '1' = Monday, '2' = Tuesday, '3' = Wednesday, '4' = Thursday, '5' = Friday, '6' = Saturday.
                * Example for Friday: `strftime('%w', substr(cd.date, 1, 4) || '-' || substr(cd.date, 5, 2) || '-' || substr(cd.date, 7, 2)) = '5'`
            - Filter active services using `calendar_dates.exception_type = 1`.
            - NEVER filter `stop_sequence = 1` unless the user explicitly asks for origin/starting station.
            - To count trains, use `COUNT(DISTINCT trips.trip_id)`.
        4. Belgian Station Names Mapping & Filtering:
            - Users will write station names in English, but the database uses official French/Dutch GTFS names.
            - Always map English names to official database names when filtering `stop_name`:
                * "Brussels Midi" / "Brussels South" -> 'Bruxelles-Midi'
                * "Brussels Central" -> 'Bruxelles-Central'
                * "Brussels North" -> 'Bruxelles-Nord'
                * "Ghent" -> 'Gent%'
                * "Antwerp" -> 'Antwerpen%'
                * "Bruges" -> 'Brugge%'
            - For safer matching, use `LOWER(stop_name) LIKE '%bruxelles-midi%'` or `LOWER(stop_name) LIKE '%midi%'`.
        5. Return EXCLUSIVELY clean SQL code without Markdown formatting (no ```sql).
    '''
    # LLMs APIs are totally stateless (without any memory)
    # simulation of a fluid conversation appending the messages to a list to create a messages history

    # definition of messages as the system_prompt + the saved conversation history
    messages = [{"role": "system", "content": system_prompt}] + _format_history(history)

    # API call
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,  # type: ignore
        temperature=0,      # 0 for ensuring determinism in the generated SQL code
        max_tokens=500      # ideal between 300 and 500 for railpulse objective
    )

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