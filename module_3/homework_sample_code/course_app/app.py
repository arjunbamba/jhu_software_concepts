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

def get_db_connection(db_name, db_user, db_password, db_host, db_port):
	"""A function to connect to the database"""
	conn = psycopg.connect(
		dbname=db_name,
		user=db_user,
		password=db_password,
		host=db_host,
		port=db_port,
	)
	return conn

def get_queries():
	"""
	Much of this is a copy of my code from query_data.py.
	This sets up the questions and queries, and then proceeds to one-by-one execute the sql suery and the question and sql query result in a dictionary.
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
	DB_NAME = "gradcafe"
	DB_USER = "postgres"
	DB_PASSWORD = "abc123"
	DB_HOST = "localhost"
	DB_PORT = "5432" 
	
	question_answer = get_queries()
	
	if request.method == 'POST':
		# Scrape new data and merge it with existing llm_extend_applicant_data.json
		main()

		# Load JSON data
		load_json_to_db(data_file, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

		conn = get_db_connection(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT COUNT(*) FROM applicants;
			"""
		)
		print("Total applicants in DB:", cur.fetchone()[0])
		# print(cur.fetchall())
		cur.close()
		conn.close()

	
	return render_template('index.html', question_answer=question_answer)


@app.route('/create/', methods=('GET', 'POST'))
def create():
	"""A function to create a new course and add to database"""
	if request.method == 'POST':
		id = request.form['id']
		name = request.form['name']
		instructor = request.form['instructor']
		room_number = request.form['room_number']
		print(id, name, instructor, room_number)

		conn = get_db_connection()
		cur = conn.cursor()
		cur.execute("""
			INSERT INTO courses(id, name, instructor, room_number)
			VALUES (%s, %s, %s, %s)""",
			(id, name, instructor, room_number)
			)
		conn.commit()
		cur.close()
		conn.close()
		return redirect(url_for('index'))
	return render_template('create.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080, debug=True)