import psycopg
from psycopg.rows import dict_row

def connect_to_db():
    return psycopg.connect("dbname=traderjoe user=db_user")

def connect_to_db_dict_response():
    return psycopg.connect("dbname=traderjoe user=db_user", row_factory=dict_row)
