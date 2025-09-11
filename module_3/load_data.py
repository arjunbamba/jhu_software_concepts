import psycopg
from psycopg import OperationalError

# make a connection with your PostgreSQL database:
def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        # use psycopg.connect() to connect to a PostgreSQL server from within your Python application.
        connection = psycopg.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


# create a new database (gradcafe) in the PostgreSQL database server
def create_database(connection, query):
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")


def execute_query(connection, query):
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")


def load_data():
    # Create a connection to a PostgreSQL database
    # Make a connection with the default database postgres
    connection = create_connection(
        # "postgres", "postgres", "abc123", "127.0.0.1", "5432"
        "postgres", "postgres", "abc123", "localhost", "5432"
    )

    create_database_query = "CREATE DATABASE gradcafe"
    create_database(connection, create_database_query)

    # Before we execute queries on the gradcafe database, we need to connect to it
    # Establish a connection with the gradcafe database located in the postgres database server
    connection = create_connection(
        "gradcafe", "postgres", "abc123", "localhost", "5432"
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
        degree FLOAT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    """
    execute_query(connection, create_applicants_table)
    