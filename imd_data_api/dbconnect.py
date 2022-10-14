# dbonnect.py

import psycopg2, json, sys, os, time, datetime
from psycopg2 import pool, IntegrityError, extras
import pandas as pd
from pandas.io.sql import DatabaseError

import commonfuncs as cf

# Postgresql multi-threaded connection pool.
# From https://pynative.com/psycopg2-python-postgresql-connection-pooling/#h-create-a-threaded-postgresql-connection-pool-in-python

dbcreds = {
    'host': os.environ.get('DB_SERVER',''),
    'port': os.environ.get('DB_PORT',''),
    'dbname': os.environ.get('DB_DBNAME',''),
    'user': os.environ.get('DB_USER',''),
    'password': os.environ.get('DB_PW','')
}

assert len(dbcreds['password']) > 2, "Invalid DB connection password" 

threaded_postgreSQL_pool = psycopg2.pool.ThreadedConnectionPool(5, 20, user=dbcreds['user'],
    password=dbcreds['password'], host=dbcreds['host'], port=dbcreds['port'], database=dbcreds['dbname'])

assert threaded_postgreSQL_pool, "Could not create DB connection"

cf.logmessage("DB Connected")

def makeQuery(s1, output='df', lowerCaseColumns=False, keepCols=False, fillna=True, engine=None, noprint=False):
    '''
    output choices:
    oneValue : ex: select count(*) from table1 (output will be only one value)
    oneRow : ex: select * from table1 where id='A' (output will be onle one row)
    df: ex: select * from users (output will be a table)
    list: json array, like df.to_dict(orient='records')
    column: first column in output as a list. ex: select username from users
    oneJson: First row, as dict
    '''
    if not isinstance(s1,str):
        cf.logmessage("query needs to be a string")
        return False
    if ';' in s1:
        cf.logmessage("; not allowed")
        return False

    if not noprint:
        # keeping auth check and some other queries out
        skipPrint = ['where token=', '.STArea()', 'STGeomFromText']
        if not any([(x in s1) for x in skipPrint]) : 
            cf.logmessage(f"Query: {' '.join(s1.split())}")
        else: 
            cf.logmessage(f"Query: {' '.join(s1.split())[:20]}")

    ps_connection = threaded_postgreSQL_pool.getconn()

    result = None # default return value

    if output in ('oneValue','oneRow'):
        ps_cursor = ps_connection.cursor()
        ps_cursor.execute(s1)
        row = ps_cursor.fetchone()
        if not row: 
            result = None
        else:
            if output == 'oneValue':
                result = row[0]
            else:
                result = row
        ps_cursor.close()
        
    elif output in ('df','list','oneJson','column'):
        # df
        try:
            if fillna:
                df = pd.read_sql_query(s1, con=ps_connection, coerce_float=False).fillna('') 
            else:
                df = pd.read_sql_query(s1, con=ps_connection, coerce_float=False)
        except DatabaseError as e:
            cf.logmessage("DatabaseError!")
            cf.logmessage(e)
            raise
        # coerce_float : need to ensure mobiles aren't screwed
        
        # make all colunm headers lowercase
        if lowerCaseColumns: df.columns = [x.lower() for x in df.columns] # from https://stackoverflow.com/questions/19726029/how-can-i-make-pandas-dataframe-column-headers-all-lowercase
        
        if output=='df':
            result = df
            if (not len(df)) and (not keepCols):
                result = []
        elif output == 'oneJson': 
            if not len(df):
                result = {}
            else:
                result = df.to_dict(orient='records')[0]

        elif (not len(df)): 
            result = []
        elif output == 'column':
            result = df.iloc[:,0].tolist() # .iloc[:,0] -> first column
        elif output == 'list':
            result = df.to_dict(orient='records')
        else:
            # default - df
            result = df
    else:
        cf.logmessage('invalid output type')
    
    threaded_postgreSQL_pool.putconn(ps_connection) # return threaded connnection back to pool
    return result


def execSQL(s1, noprint=False):
    if not noprint: cf.logmessage(' '.join(s1.split()))
    ps_connection = threaded_postgreSQL_pool.getconn()
    ps_cursor = ps_connection.cursor()
    ps_cursor.execute(s1)
    ps_connection.commit()

    affected = ps_cursor.rowcount
    ps_cursor.close()
    threaded_postgreSQL_pool.putconn(ps_connection)
    return affected


def getColumnsList(tablename, engine):
    statement1 = f"""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = N'{tablename}'
    """
    # sql = db.text(statement1)
    df = pd.read_sql_query(statement1,con=engine)
    # return df['COLUMN_NAME'].str.lower().to_list()
    return df['column_name'].to_list()


def addRow(params,tablename):
    df = pd.DataFrame([params]) 
    return addTable(df, tablename) # heck


def OLD_addTable(df, tablename, lowerCaseColumns=False):
    ps_connection = threaded_postgreSQL_pool.getconn()

    table_cols = getColumnsList(tablename,ps_connection)
    if lowerCaseColumns:
        df.columns = [x.lower() for x in df.columns] # make lowercase
    sending_cols = [x for x in table_cols if x in df.columns]
    discarded_cols = set(df.columns.to_list()) - set(table_cols)
    if len(discarded_cols): cf.logmessage("Dropping {} cols from uploaded data as they're not in the DB: {}".format(len(discarded_cols),', '.join(discarded_cols)))
    
    # ensure only those values go to DB table that have columns there
    # cf.logmessage("Adding {} rows into {} with these columns: {}".format(len(df), tablename, sending_cols))
    CHUNKSIZE = int(os.environ.get('CHUNKSIZE',1))
    try:
        df[sending_cols].to_sql(name=tablename, con=ps_connection, chunksize=CHUNKSIZE, if_exists='append', index=False )
        threaded_postgreSQL_pool.putconn(ps_connection) # return threaded connnection back to pool

    except IntegrityError as e:
        cf.logmessage(e)
        threaded_postgreSQL_pool.putconn(ps_connection) # return threaded connnection back to pool
        return False
    except:
        threaded_postgreSQL_pool.putconn(ps_connection) # return threaded connnection back to pool
        raise
        return False

    return True



def addTable(df, table):
    """
    From https://naysan.ca/2020/05/09/pandas-to-postgresql-using-psycopg2-bulk-insert-performance-benchmark/
    Using psycopg2.extras.execute_values() to insert the dataframe
    """
    # Create a list of tupples from the dataframe values
    tuples = [tuple(x) for x in df.to_numpy()]
    # Comma-separated dataframe columns
    cols = ','.join(list(df.columns))
    # SQL query to execute
    query  = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
    ps_connection = threaded_postgreSQL_pool.getconn()
    cursor = ps_connection.cursor()
    cf.logmessage(f"Adding {len(df)} rows to {table}")
    try:
        extras.execute_values(cursor, query, tuples)
        ps_connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        cf.logmessage("Error: %s" % error)
        ps_connection.rollback()
        cursor.close()
        threaded_postgreSQL_pool.putconn(ps_connection) # return threaded connnection back to pool
        return False
    cursor.close()
    threaded_postgreSQL_pool.putconn(ps_connection) # return threaded connnection back to pool
    return True