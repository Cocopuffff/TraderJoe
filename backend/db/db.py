import psycopg


def connect_to_db():
    return psycopg.connect("dbname=traderjoe user=db_user")