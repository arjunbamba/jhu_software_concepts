import json
import psycopg
from psycopg import OperationalError
from datetime import datetime


# CONNECTION AND QUERY HELPERS
# ---------------------------------

# make a connection with your PostgreSQL database:
def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        # use psycopg.connect() to connect to a PostgreSQL server from within your Python application.
        connection = psycopg.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


# execute a SQL query
def execute_query(connection, query):
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    finally:
        cursor.close()


# SETUP DB + APPLICANTS TABLE
# ---------------------------------

# create a new database (gradcafe) in the PostgreSQL database server
def setup_database(db_user, db_password, db_host, db_port):
    # Create a connection to a PostgreSQL database
    # Make a connection with the default database postgres
    connection = create_connection(
        "postgres", db_user, db_password, db_host, db_port
    )
    create_database_query = "CREATE DATABASE gradcafe"
    try:
        execute_query(connection, create_database_query)
    except Exception as e:
        # Database probably exists already
        print(f"Skipping create database: {e}")
    finally:
        connection.close()

# connect to gradcafe db to create applicants table
def setup_table(db_user, db_password, db_host, db_port):
    # Before we execute queries on the gradcafe database, we need to connect to it
    # Establish a connection with the gradcafe database located in the postgres database server
    connection = create_connection(
        "gradcafe", db_user, db_password, db_host, db_port
    )

    create_applicants_table = """
    CREATE TABLE IF NOT EXISTS applicants (
        p_id SERIAL PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        gpa FLOAT,
        gre FLOAT,
        gre_v FLOAT,
        gre_aw FLOAT,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    """
    execute_query(connection, create_applicants_table)
    connection.close()


# DRIVER FUNCTION
def load_data():
    DB_USER = "postgres"
    DB_PASSWORD = "abc123"
    DB_HOST = "localhost"
    DB_PORT = "5432"

    setup_database(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    setup_table(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)



if __name__ == "__main__":
    load_data()

    