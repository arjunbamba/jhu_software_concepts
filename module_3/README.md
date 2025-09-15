# About
### Author
Arjun Bamba <br>
JHED ID: abamba1

### Module Info
Module 3 Assignment - SQL Data Analysis <br>
September 14, 2025 <br>

# Setup and Run Project
## 1. Clone repository
```
git clone git@github.com:arjunbamba/jhu_software_concepts.git
```
## 2. Install dependencies
### Python
In terminal, navigate to within module_3 directory in cloned repo.

Through terminal, recreate the virtual environment (venv) and install dependencies:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### PostgreSQL (via Homebrew on macOS)
Install (if needed):
```
brew install postgresql
```
Start PostgreSQL:
```
brew services start postgresql
```
## 3. Ensure postgres Role Exists (only first time)
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
## 4. Run Project
### Run Database Setup + Data Load
```
python load_data.py
```
![load_data](/module_3/Screenshot_Load_Data.jpg)

### Run Queries (to view data analysis)
```
python query_data.py
```
![query_data](/module_3/Screenshot_Query_Data.jpg)

### Run Flask Web App
In terminal, navigate to: `jhu_software_concepts/module_3/homework_sample_code/course_app`

Now run the app locally via: `python app.py`

#### Data Analysis Webpage
In your browser, go to `localhost:8080`, and you should see the following data analysis:

![data_analysis](/module_3/Screenshot_Data_Analysis.jpg)

#### Pull Data
After pulling new data, you should see the following (webpage showing success message and terminal showing total applicants going from 30,000 to 30,003 (in my case)):

![data_pull](/module_3/Screenshot_Data_Pull.jpg)

#### Update Analysis
After updating analysis, you should see the following (webpage showing success message and (in my case) some minor changes to the analysis' answers compared to the answers before pulling in picture 1 above):

![data_update](/module_3/Screenshot_Data_Update.jpg)

#### Update Analysis (with Pull Data in progress)
If you click pull data and immediately click update analysis before the pull data request completes, you should see the following (webpage stopping refresh and showing cannot refresh message because pull data is currently in progress):

![data_update_stop](/module_3/Screenshot_Data_Update_Stop.jpg)

### Notes:

- Code from module 2 modified for scraping/cleaning only new entries is in `homework_sample_code/course_app/` directory - i.e., `main.py`, `scrape.py`, and `clean.py`. 
- Ignore/disregard `database.py` which is given sample code that I have not utilized.
