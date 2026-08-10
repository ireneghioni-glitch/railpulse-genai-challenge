'''
==============
db_service.py: 
==============
'''



# Imports
# -------

import pyodbc
import sqlalchemy


# Functions
# ---------

def get_db_schema() -> str:
    '''
    TODO
    '''
    # ... codice di connessione con pyodbc/sqlalchemy ...

    query = '''
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
    '''

    # ... esecuzione query e formattazione in stringa ...

    return formatted_schema_string