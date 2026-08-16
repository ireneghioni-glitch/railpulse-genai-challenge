'''
==============
db_service.py: 
==============
'''



# Imports
# -------

import pyodbc
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError
import os
import time
import re

# reading .env file and loading environments variables
load_dotenv()



# Functions
# ---------

def _get_engine():
    '''
    TODO
    '''
    # connection with SQLAlchemy
    conn_string = os.getenv("DATABASE_CONNECTION_STRING")
    if not conn_string:
        raise ValueError("DATABASE_CONNECTION_STRING not setted as an ambience variable.")
    
    # SQLAlchemy engine creation
    engine = create_engine(conn_string, pool_pre_ping=True)

    # --- COLD START (RETRY LOGIC) ---
    max_retries = 3
    delay_seconds = 15

    for attempt in range(max_retries):
        try:
            # Connection test
            with engine.connect() as conn:
                pass  # connection was successfull, db is finally active
            break     # exit the retry cycle
        except OperationalError as e:
            # last attempts and db hasn't still woken up
            if attempt < max_retries - 1:
                time.sleep(delay_seconds)
            else:
                # if after all the attempts it fails again, finally returns the original error
                raise e

    return engine

def get_db_dialect() -> str:
    '''
    TODO 
    '''
    engine = _get_engine()
    dialect_name = engine.dialect.name.lower()

    if "sqlite" in dialect_name:
        return "SQLite"
    elif "mssql" in dialect_name or "pyodbc" in dialect_name:
        return "T-SQL / Azure SQL"
    else:
        return dialect_name.upper()


def get_db_schema() -> str:
    '''
    TODO
    '''
    engine = _get_engine()

    # add SQLAlchemy inspect module to make function universal (for querying both local and Azure database)
    inspector = inspect(engine)

    # ------ code before including inspect ----------------------------------------------------------------

    # query = '''
    #     SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
    #     FROM INFORMATION_SCHEMA.COLUMNS
    #     WHERE TABLE_SCHEMA = 'dbo'
    #     ORDER BY TABLE_NAME, ORDINAL_POSITION
    # '''
    # We are querying an ANSI SQL standard system view, called INFORMATION_SCHEMA.COLUMNS.
    # INFORMATION_SCHEMA.COLUMNS is a "special" virtual table automatically provided by 
    # SQL Server (and Azure SQL) that contains a map of all the columns in the database.

    # 'dbo' -> Default schema for all user-created tables in Azure SQL. 
    #          Without this filter, the query might also retrieve internal system tables belonging to Azure SQL.

    # ... esecuzione query e formattazione in stringa ...

    # # query execution and loading results in df
    # with engine.connect() as connection:
    #     df_columns = pd.read_sql_query(query, connection)

    # ----------------------------------------------------------------------------------------------------

    # ideal output is like this:
    
    # Table: trains
    #     - train_id (int)
    #     - train_number (varchar)

    # Table: delays
    #     - delay_id (int)
    #     - delay_minutes (int)

    # grouping columns by table and string formatting

    schema_lines = []

    for table_name in inspector.get_table_names():
        schema_lines.append(f"Table: {table_name}")
        # for each table, read columns and data type
        for column in inspector.get_columns(table_name):
            col_name = column['name']
            col_type = str(column['type'])
            schema_lines.append(f"  - {col_name} ({col_type})")
        schema_lines.append("")

    formatted_schema_string = "\n".join(schema_lines).strip()

    return formatted_schema_string


def _clean_sql_for_azure(sql_query: str) -> str:
    """
    Intercepts and automatically converts 'LIMIT N' clauses into 'SELECT TOP N'
    to ensure 100% syntax compatibility with Azure SQL / T-SQL.
    """
    # Search for 'LIMIT N' at the end of the query
    match = re.search(r'\bLIMIT\s+(\d+)\s*;?\s*$', sql_query, re.IGNORECASE)
    if match:
        limit_val = match.group(1)
        # Remove 'LIMIT N'
        sql_query = re.sub(r'\bLIMIT\s+\d+\s*;?\s*$', '', sql_query, flags=re.IGNORECASE).strip()
        
        # Find the main SELECT statement (the last SELECT in case of CTEs)
        select_matches = list(re.finditer(r'\bSELECT\b', sql_query, re.IGNORECASE))
        if select_matches:
            last_select_idx = select_matches[-1].end()
            # Check if DISTINCT follows SELECT
            distinct_match = re.match(r'^\s+DISTINCT\b', sql_query[last_select_idx:], re.IGNORECASE)
            if distinct_match:
                insert_pos = last_select_idx + distinct_match.end()
                sql_query = sql_query[:insert_pos] + f" TOP {limit_val}" + sql_query[insert_pos:]
            else:
                sql_query = sql_query[:last_select_idx] + f" TOP {limit_val}" + sql_query[last_select_idx:]
                
    return sql_query


def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """
    Executes a read-only SQL query, automatically sanitizing syntax based on the active dialect.
    """
    # don't repeat yourself approach
    engine = _get_engine()
    dialect = get_db_dialect()

    # If using Azure SQL / T-SQL, sanitize query syntax prior to execution
    if "SQLite" not in dialect:
        sql_query = _clean_sql_for_azure(sql_query)
    
    # Safe execution of the read-only sql query
    with engine.connect() as connection:
        # when passing an SQL string to a connection or to `pandas.read_sql_query`, 
        # it is good practice to wrap it in SQLAlchemy's `text()` function.
        df = pd.read_sql_query(text(sql_query), connection)
        # avoids deprecation warnings and ensures that SQL queries executed on SQLite or Azure SQL are handled correctly
    
    return df