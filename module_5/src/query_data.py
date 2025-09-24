import psycopg


def run_queries(db_name, db_user, db_password, db_host, db_port):
    """Execute the canned analysis queries and print their results.

    :param str db_name: Name of the database containing the ``applicants`` table.
    :param str db_user: Database user that should be authenticated.
    :param str db_password: Password associated with ``db_user``.
    :param str db_host: Hostname or address where the PostgreSQL instance lives.
    :param str db_port: TCP port for the PostgreSQL service.
    :return: ``None``
    :rtype: None
    """
    connection = psycopg.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )

    cursor = connection.cursor()

    # Prepare all the questions
    questions = [
        "1. How many entries applied for Fall 2025?",
        "2. Percentage of entries from international students (to 2 decimal places)",
        "3. Average GPA, GRE, GRE V, GRE AW of applicants who provided them",
        "4. Average GPA of American students in Fall 2025",
        "5. Percent of Fall 2025 entries that are Acceptances",
        "6. Average GPA of Fall 2025 Acceptances",
        "7. How many entries for JHU MS CS applicants",
        "8. How many 2025 PhD CS acceptances at Georgetown",
        # Additional curiosity-driven questions
        "9. Which university has the most applicants overall?",
        "10. What is the most common program applicants apply to?"
    ]

    # Prepare all the sql queries corresponding to the questions
    query1 = """
            SELECT COUNT(*) 
            FROM applicants
            WHERE term ILIKE '%Fall 2025%';
        """
    query2 = """
            SELECT 
                ROUND(
                100.0 * COUNT(*) FILTER (WHERE us_or_international ILIKE '%International%') 
                / NULLIF(COUNT(*), 0), 
                2
            ) AS pct_international
            FROM applicants;
        """
    query3 = """
            SELECT 
                ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
                ROUND(AVG(gre)::numeric, 2) AS avg_gre,
                ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
                ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
            FROM applicants;
        """
    query4 = """
            SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
            FROM applicants
            WHERE term ILIKE '%Fall 2025%'
              AND us_or_international ILIKE '%American%';
        """
    query5 = """
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (WHERE status ILIKE '%Accept%')
                / NULLIF(COUNT(*), 0),
                2
            ) AS pct_acceptances
            FROM applicants
            WHERE term ILIKE '%Fall 2025%';
        """
    query6 = """
            SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
            FROM applicants
            WHERE term ILIKE '%Fall 2025%'
              AND status ILIKE '%Accept%';
        """
    query7 = """
            SELECT COUNT(*)
            FROM applicants
            WHERE llm_generated_university ILIKE '%Johns Hopkins%'
              AND llm_generated_program ILIKE '%Computer Science%'
              AND degree ILIKE '%Master%';
        """
    query8 = """
            SELECT COUNT(*)
            FROM applicants
            WHERE llm_generated_university ILIKE '%Georgetown%'
              AND llm_generated_program ILIKE '%Computer Science%'
              AND degree ILIKE '%PhD%'
              AND term ILIKE '%2025%'
              AND status ILIKE '%Accept%';
        """
    query9 = """
            SELECT llm_generated_university, COUNT(*) AS num_apps
            FROM applicants
            GROUP BY llm_generated_university
            ORDER BY num_apps DESC
            LIMIT 1;
        """
    query10 = """
            SELECT llm_generated_program, COUNT(*) AS num_apps
            FROM applicants
            GROUP BY llm_generated_program
            ORDER BY num_apps DESC
            LIMIT 1;
        """
    
    # Make a list of the queries for easy index reference later
    sql_queries = [
        query1,
        query2,
        query3,
        query4,
        query5,
        query6,
        query7,
        query8,
        query9,
        query10
    ]
    
    # Print question, execute corresponding query, and print query result
    for i in range(len(questions)):
        print(f"\n{questions[i]}")
        cursor.execute(sql_queries[i])
        # print(cursor.fetchall())

        rows = cursor.fetchall()
        if not rows or rows[0][0] is None:
            print("   No results found.")
        
        # if only one row / one colum, print scalar
        if len(rows) == 1 and len(rows[0]) == 1:
            print(f"   {rows[0][0]}")
        else:
            # print rows
            for row in rows:
                print("   " + " | ".join(str(val) if val is not None else "NULL" for val in row))

    cursor.close()
    connection.close()


if __name__ == "__main__":
    DB_NAME = "gradcafe"
    DB_USER = "postgres"
    DB_PASSWORD = "abc123"
    DB_HOST = "localhost"
    DB_PORT = "5432"

    run_queries(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
