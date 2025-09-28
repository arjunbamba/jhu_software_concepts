## Table of Contents
- [About](#about)
  - [Author](#author)
  - [Module Info](#module-info)
- [Setup and Run Project](#setup-and-run-project)
  - [1. Clone repository](#1-clone-repository)
  - [2. Install dependencies](#2-install-dependencies)
    - [Python](#python)
    - [PostgreSQL (via Homebrew on macOS) - Optional (from Module 3)](#postgresql-via-homebrew-on-macos---optional-from-module-3)
    - [Ensure `postgres` Role Exists (only first time) - Optional (from Module 3)](#ensure-postgres-role-exists-only-first-time---optional-from-module-3)
  - [3. Linting, Testing, Snyk Analysis (Module 5)](#3-linting-testing-snyk-analysis-module-5)
    - [Run Linting](#run-linting)
    - [Run Coverage Test](#run-coverage-test)
    - [Run Complete Test Suite](#run-complete-test-suite)
    - [Snyk Analysis Verification](#snyk-analysis-verification)
    - [Verify Flask/Analysis Webpage Working](#verify-flaskanalysis-webpage-working)
  - [4. Run Project (guidelines from module 3)](#4-run-project-guidelines-from-module-3)
    - [Run Database Setup + Data Load](#run-database-setup--data-load)
    - [Run Queries (to view data analysis)](#run-queries-to-view-data-analysis)
    - [Run Flask Web App](#run-flask-web-app)
    - [Data Analysis Webpage](#data-analysis-webpage)
      - [Pull Data](#pull-data)
      - [Update Analysis](#update-analysis)
      - [Update Analysis (with Pull Data in progress)](#update-analysis-with-pull-data-in-progress)

## About
### Author
Arjun Bamba <br>
JHED ID: abamba1

### Module Info
Module 5 Assignment - Software Assurance, Static Code Analysis, and SQL Injections <br>
September 28, 2025 <br>

## Setup and Run Project
### 1. Clone repository
```
git clone git@github.com:arjunbamba/jhu_software_concepts.git
```

### 2. Install dependencies
#### Python
In terminal, navigate to within module_5 directory in cloned repo.

Through terminal, recreate the virtual environment (venv) and install dependencies:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
#### PostgreSQL (via Homebrew on macOS) - Optional (from Module 3)
Install (if needed):
```
brew install postgresql
```
Start PostgreSQL:
```
brew services start postgresql
```

#### Ensure `postgres` Role Exists (only first time) - Optional (from Module 3)
By default, Homebrew sets your macOS username as the superuser role. For portability, we’ll create a standard postgres role that matches what the code expects.

In terminal:
```
psql -U $(whoami) -d postgres
```
This will open the psql shell. Inside the psql shell, run:
```
CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'abc123';
```
Exit psql:
```
\q
```

### 3. Linting, Testing, Snyk Analysis (Module 5)
Navigate to root directory (`/module_5/`) and run the following:

#### Run Linting
```
pylint src/
```
![pylint_src](/module_5/Screenshots/module_5/pylint_src.jpg)

```
pylint tests/
```
![pylint_tests](/module_5/Screenshots/module_5/pylint_tests.jpg)

#### Run Coverage Test
```
pytest --cov-report term-missing --cov=src
```
![coverage_summary](/module_5/Screenshots/module_5/coverage_summary.jpg)

#### Run Complete Test Suite
```
pytest -m "web or buttons or analysis or db or integration"
```
![all_tests_summary](/module_5/Screenshots/module_5/all_tests_summary.jpg)

#### Snyk Analysis Verification
Run the following (macOS) commands to run Snyk analysis. See my test analysis below.
```
curl https://static.snyk.io/cli/latest/snyk-macos -o snyk
chmod +x ./snyk
mv ./snyk /usr/local/bin
snyk auth # authorize with your snyk account
snyk test
```
![snyk-analysis](/module_5/snyk-analysis.png)
- There were no vulnerabilities found in my Snyk test run, so my project is free from any malicious packages.

#### Verify Flask/Analysis Webpage Working
Navigate to `module_5/src/homework_sample_code/course_app/`.

Now run the app locally via: `python app.py`. In your browser, go to `localhost:8080`, and you should see the following webpage:

![working_flask](/module_5/Screenshots/module_5/working_flask.jpg)

### 4. Run Project (guidelines from module 3)

#### Run Database Setup + Data Load
Navigate to `module_5/src/` and run the following:
```
python load_data.py
```
![load_data](/module_5/Screenshots/module_3/Screenshot_Load_Data.jpg)

#### Run Queries (to view data analysis)
Navigate to `module_5/src/` and run the following:
```
python query_data.py
```
![query_data](/module_5/Screenshots/module_3/Screenshot_Query_Data.jpg)

#### Run Flask Web App
Navigate to `module_5/src/homework_sample_code/course_app/`.

Now run the app locally via: `python app.py`

#### Data Analysis Webpage
In your browser, go to `localhost:8080`, and you should see the following data analysis:

![data_analysis](/module_5/Screenshots/module_3/Screenshot_Data_Analysis.jpg)

##### Pull Data
After pulling new data, you should see the following (webpage showing success message and terminal showing total applicants going from 30,000 to 30,003 (in my case)):

![data_pull](/module_5/Screenshots/module_3/Screenshot_Data_Pull.jpg)

##### Update Analysis
After updating analysis, you should see the following (webpage showing success message and (in my case) some minor changes to the analysis' answers compared to the answers before pulling in picture 1 above):

![data_update](/module_5/Screenshots/module_3/Screenshot_Data_Update.jpg)

##### Update Analysis (with Pull Data in progress)
If you click pull data and immediately click update analysis before the pull data request completes, you should see the following (webpage stopping refresh and showing cannot refresh message because pull data is currently in progress):

![data_update_stop](/module_5/Screenshots/module_3/Screenshot_Data_Update_Stop.jpg)
