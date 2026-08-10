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


def generate_sql_query(history: list, db_schema: str):
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
        Your only job is to convert user requests in natural language to SQL queries (dialect T-SQL / Azure SQL).

        DATABASE SCHEMA:
        {db_schema}

        STRICT RULES:
        1. Generate ONLY read-only queries (SELECT).
        2. Return EXCLUSIVELY clean and correct SQL code.
        3. Do NOT include Markdown formatting (no ```sql ... ```), explanations, or introductory text.
    '''
    # LLMs APIs are totally stateless (without any memory)
    # simulation of a fluid conversation appending the messages to a list to create a messages history

    # definition of messages as the system_prompt + the saved conversation history
    messages = [{"role": "system", "content": system_prompt}] + history

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



