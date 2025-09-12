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


