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
import os

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
    engine = create_engine(conn_string)

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


def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """
    TODO
    """
    # don't repeat yourself approach
    engine = _get_engine()
    
    # Safe execution of the read-only sql query
    with engine.connect() as connection:
        # when passing an SQL string to a connection or to `pandas.read_sql_query`, 
        # it is good practice to wrap it in SQLAlchemy's `text()` function.
        df = pd.read_sql_query(text(sql_query), connection)
        # avoids deprecation warnings and ensures that SQL queries executed on SQLite or Azure SQL are handled correctly
    
    return df