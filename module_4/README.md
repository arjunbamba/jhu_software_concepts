# About
### Author
Arjun Bamba <br>
JHED ID: abamba1

### Module Info
Module 4 Assignment - Testing and Documentation (Pytest and Sphinx) <br>
September 22, 2025 <br>

# Setup and Run Project
## 1. Clone repository
```
git clone git@github.com:arjunbamba/jhu_software_concepts.git
```

## 2. Install dependencies
### Python
In terminal, navigate to within module_4 directory in cloned repo.

Through terminal, recreate the virtual environment (venv) and install dependencies:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### PostgreSQL (via Homebrew on macOS) - Optional (from module 3)
Install (if needed):
```
brew install postgresql
```
Start PostgreSQL:
```
brew services start postgresql
```

## 3. Ensure postgres Role Exists (only first time) - Optional (from module 3)
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

## 4. Tests and Docs (Module 4) - see (5) for running guidelines (from module 3)
### Run Coverage Test
Navigate to root directory: `/module_4/` and run the following:
```
pytest --cov-report term-missing --cov=src
```
![coverage_summary](/module_4/Screenshots/module_4/coverage_summary.jpg)

### Run all tests
Because my coverage is not exactly 100%, the following line of code in `pytest.ini` blocks the normal test results from showing.
```
addopts = -q --cov=module_4/src --cov-report=term-missing --cov-fail-under=100
```

If you comment out the above line of code in `pytest.ini`, then you can navigate to `tests/` and run the complete test suite via:
```
pytest -m "web or buttons or analysis or db or integration"
```
![all_tests_summary](/module_4/Screenshots/module_4/all_tests_summary.jpg)

### Generate Documentation
I have already generated, but to regenerate documentation from scratch, navigate to `docs/` and run:
```
make html
```

### View Documentation
LINK TO RTD DOC: https://jhu-software-concepts-arjun-bamba.readthedocs.io/en/latest/api_reference.html

Navigate to `docs/build/html` to view `api_reference.html` source file.

Screenshots locally:
![Sphinx_RTD_1_DB](/module_4/Screenshots/module_4/Sphinx_RTD_1_DB.jpg)
![Sphinx_RTD_2_Analysis](/module_4/Screenshots/module_4/Sphinx_RTD_2_Analysis.jpg)
![Sphinx_RTD_3_App](/module_4/Screenshots/module_4/Sphinx_RTD_3_App.jpg)

## 5. Run Project (guidelines from module 3)
### Run Database Setup + Data Load
```
python load_data.py
```
![load_data](/module_4/Screenshots/module_3/Screenshot_Load_Data.jpg)

### Run Queries (to view data analysis)
```
python query_data.py
```
![query_data](/module_4/Screenshots/module_3/Screenshot_Query_Data.jpg)

### Run Flask Web App
In terminal, navigate to: `jhu_software_concepts/module_4/src/homework_sample_code/course_app`

Now run the app locally via: `python app.py`

#### Data Analysis Webpage
In your browser, go to `localhost:8080`, and you should see the following data analysis:

![data_analysis](/module_4/Screenshots/module_3/Screenshot_Data_Analysis.jpg)

#### Pull Data
After pulling new data, you should see the following (webpage showing success message and terminal showing total applicants going from 30,000 to 30,003 (in my case)):

![data_pull](/module_4/Screenshots/module_3/Screenshot_Data_Pull.jpg)

#### Update Analysis
After updating analysis, you should see the following (webpage showing success message and (in my case) some minor changes to the analysis' answers compared to the answers before pulling in picture 1 above):

![data_update](/module_4/Screenshots/module_3/Screenshot_Data_Update.jpg)

#### Update Analysis (with Pull Data in progress)
If you click pull data and immediately click update analysis before the pull data request completes, you should see the following (webpage stopping refresh and showing cannot refresh message because pull data is currently in progress):

![data_update_stop](/module_4/Screenshots/module_3/Screenshot_Data_Update_Stop.jpg)

### Notes:

- Code from module 2 modified for scraping/cleaning only new entries is in `homework_sample_code/course_app/` directory - i.e., `main.py`, `scrape.py`, and `clean.py`. 
- Ignore/disregard `database.py` which is given sample code that I have not utilized.
