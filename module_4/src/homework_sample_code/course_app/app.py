import os
import psycopg
from flask import Flask, render_template, request, url_for, redirect
from main import main

import sys
import os
# Get path 2 levels up from current file
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(parent_dir)
# Now import
from load_data import load_json_to_db
data_file = os.path.join(parent_dir, "llm_extend_applicant_data.json")

app = Flask(__name__)

# Global flag to track if scraping is running
is_scraping = False
# Cache last analysis payload so the page can render without re-querying when busy
# latest_analysis = {}


def get_db_connection(db_name, db_user, db_password, db_host, db_port):
	"""Create a psycopg connection using the provided credentials.

	:param str db_name: Target database name.
	:param str db_user: Database user name.
	:param str db_password: Password for ``db_user``.
	:param str db_host: Hostname of the database server.
	:param str db_port: Port of the database service.
	:return: Open database connection.
	:rtype: psycopg.Connection
	"""
	conn = psycopg.connect(
		dbname=db_name,
		user=db_user,
		password=db_password,
		host=db_host,
		port=db_port,
	)
	return conn

def get_queries():
	"""Compute the application analysis answers from the ``applicants`` table.

	:return: Mapping of formatted question text to the associated answer string.
	:rtype: dict[str, str]
	"""
	DB_NAME = "gradcafe"
	DB_USER = "postgres"
	DB_PASSWORD = "abc123"
	DB_HOST = "localhost"
	DB_PORT = "5432"
	
	conn = get_db_connection(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
	cur = conn.cursor()
	
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

	# Execute queries one by one, and store question and corresponding answer in a dictionary to give to frontend pg
	question_answer = {}
	for i in range(len(questions)):
		cur.execute(sql_queries[i])
		
		rows = cur.fetchall()
		if not rows or rows[0][0] is None:
			question_answer[questions[i]] = "No results found."
			# print("   No results found.")
		
		# If only one row and one column, print scalar
		if len(rows) == 1 and len(rows[0]) == 1:
			answer = f"{rows[0][0]}"
			question_answer[questions[i]] = answer
			# print(f"   {rows[0][0]}")
		else:
			# Print rows
			question_answer[questions[i]] = ""
			for row in rows:
				answer = " | ".join(str(val) if val is not None else "NULL" for val in row)
				question_answer[questions[i]] += answer
				# print("   " + " | ".join(str(val) if val is not None else "NULL" for val in row))
	
	cur.close()
	conn.close()
	
	return question_answer


@app.route('/', methods=('GET', 'POST'))
def index():
	"""Handle both GET and POST requests for the dashboard view.

	GET requests render the latest cached or freshly computed analysis. POST
	requests process ``Pull Data`` (``scrape``) or ``Update Analysis`` (``refresh``)
	actions.

	:return: Rendered template and HTTP status code tuple.
	:rtype: tuple[flask.Response, int]
	"""
	global is_scraping #, latest_analysis
	DB_NAME = "gradcafe"
	DB_USER = "postgres"
	DB_PASSWORD = "abc123"
	DB_HOST = "localhost"
	DB_PORT = "5432" 

	msg = None
	question_answer = {}
	status_code = 200

	# When user clicks pull data, this will fetch the latest data and then save it in the DB's applicants table
	if request.method == 'POST':
		action = request.form.get("action")

		if action == "scrape":
			if is_scraping:
				msg = "Scraping already in progress. Please wait."
				status_code = 409
				# question_answer = latest_analysis or {}
			else:
				is_scraping = True
				conn = None
				cur = None
				try:
					# Scrape and update database

					# Using modified main.py from module 2 to scrape/clean new data + merge it with existing
					main()

					# Load JSON data with new entries into applicants table
					load_json_to_db(data_file, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

					# Check if count of entries increased
					conn = get_db_connection(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
					cur = conn.cursor()
					cur.execute(
						"""
						SELECT COUNT(*) FROM applicants;
						"""
					)
					print("Total applicants in DB:", cur.fetchone()[0])

					# question_answer = get_queries()
					# latest_analysis = question_answer
					msg = "Data pulled successfully!"
				finally:
					is_scraping = False
					if cur is not None:
						cur.close()
					if conn is not None:
						conn.close()

		elif action == "refresh":
			if is_scraping:
				msg = "Cannot update analysis: Pull Data is running."
				status_code = 409
				# question_answer = latest_analysis or {}
			else:
				question_answer = get_queries()  # re-run queries only
				# latest_analysis = question_answer
				msg = "Analysis refreshed with latest database results."
	
	# If no queries have been run yet (initial GET or after scrape), fetch them
	# Do analysis for what's in the database and pass the returned question_answer dict to render_template below
	if not question_answer and status_code == 200:
		question_answer = get_queries()
		# latest_analysis = question_answer
	# elif not question_answer:
		# question_answer = latest_analysis or {}

	return render_template('index.html', question_answer=question_answer, msg=msg), status_code


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080, debug=True)
