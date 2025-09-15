import json
import psycopg
from psycopg import OperationalError
from datetime import datetime


# CONNECTION AND QUERY HELPERS
# ---------------------------------

def create_connection(db_name, db_user, db_password, db_host, db_port):
    '''
    Make a connection with the PostgreSQL database
    '''

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


def execute_query(connection, query):
    '''
    Execute a SQL Query
    '''

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

def setup_database(db_user, db_password, db_host, db_port):
    '''
    Create a new database (gradcafe) in the PostgreSQL database server
    '''

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


def setup_table(db_user, db_password, db_host, db_port):
    '''
    Connect to gradcafe db to create applicants table
    '''

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


# LOAD JSON DATA INTO APPLICANTS TABLE
# ------------------------------------------------

def load_json_to_db(json_path, db_user, db_password, db_host, db_port):
    '''
    Load cleaned applicant JSON entries into applicants table
    '''

    connection = create_connection("gradcafe", db_user, db_password, db_host, db_port)

    insert_query = """
    INSERT INTO applicants (
        program, comments, date_added, url, status, term, us_or_international, gpa, gre, gre_v, gre_aw, degree,
        llm_generated_program, llm_generated_university
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    cursor = connection.cursor()

    # Empty the table first
    cursor.execute("TRUNCATE TABLE applicants RESTART IDENTITY;")

    with open(json_path, "r") as f:
        applicants = json.load(f)

    for app in applicants:
        # Required from mod 2: program, university, date_added, url, status
        program = app.get("program")
        university = app.get("university")
        url = app.get("url")
        status = app.get("status")

        # Handle empty strings/date parsing
        date_added = None
        if app.get("date_added"):
            try:
                date_added = datetime.strptime(app["date_added"], "%B %d, %Y").date()
            except ValueError:
                date_added = None

        # Optional from mod 2: comments, term, origin, gpa, gre, gre_v, gre_aw, degree
        # Handle empty strings/date parsing as needed
        comments = app.get("comments")
        term = app.get("term")
        origin = app.get("US/International")

        gpa = None
        if app.get("GPA") and app["GPA"]:
            gpa = float(app["GPA"])
        
        gre, gre_v, gre_aw = None, None, None
        if app.get("GRE") and app["GRE"]:
            gre = float(app["GRE"])
        if app.get("GRE V") and app["GRE V"]:
            gre_v = float(app["GRE V"])
        if app.get("GRE AW") and app["GRE AW"]:
            gre_aw = float(app["GRE AW"])
        
        degree = app.get("Degree")

        llm_program, llm_uni = "", ""
        if app.get("llm-generated-program") and app["llm-generated-program"]:
            llm_program = app.get("llm-generated-program")
        if app.get("llm-generated-university") and app["llm-generated-university"]:
            llm_uni = app.get("llm-generated-university")

        cursor.execute(
            insert_query,
            (
                program,
                comments,
                date_added,
                url,
                status,
                term,
                origin,
                gpa,
                gre,
                gre_v,
                gre_aw,
                degree,
                llm_program,
                llm_uni,
            ),
        )

    connection.commit()
    cursor.close()
    connection.close()
    print("JSON data loaded from scratch into empty applicants table.")


def load_data():
    """
    This is the driver function that runs when you execute this script via `python load_data.py`
    """
    DB_USER = "postgres"
    DB_PASSWORD = "abc123"
    DB_HOST = "localhost"
    DB_PORT = "5432"

    setup_database(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    setup_table(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

    # Load JSON data
    load_json_to_db("llm_extend_applicant_data.json", DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

    connection = create_connection("gradcafe", DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM applicants;
            """
        )
        print("Total applicants in DB:", cur.fetchone()[0])
        # print(cur.fetchall())
    connection.close()


if __name__ == "__main__":
    load_data()

    