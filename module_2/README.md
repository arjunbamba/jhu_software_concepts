#### NAME: <br>
Arjun Bamba; JHED ID: abamba1

#### MODULE INFO: <br>
Module 2 - Web Scraping <br>
Assignment 2 <br>
September 7, 2025 <br>

#### APPROACH: <br>
##### Checking robots.txt: <br>
![robots.txt](/module_2/Screenshot_robots_txt.jpg) <br>

##### Initial Setup: <br>
I have tracked dependencies using requirements.txt via:
1. `pip freeze > requirements.txt` <br>
This file lists all installed packages and their versions.

##### **TO RUN THE PROJECT:**
1. Clone the repo.
2. In terminal, navigate to within module_2 directory in cloned repo.
3. Through terminal, recreate the venv and install dependencies: <br>
    * (a) Create your new venv: `python3 -m venv venv`
    * (b) Activate it: `source venv/bin/activate`
        * For reference, I installed packages in an active venv like this: `python3 -m pip install urllib3`
    * (c) Install dependencies so your environment matches mine exactly: `pip install -r requirements.txt`
4. Run the project: `python main.py`
    * This will show you the scraping progress as it's going on 
        * Scraping 30,000 entries takes roughly 5 minutes based on my experience.
    * After scraping, it will proceed to clean, save, and load.
        * Your end result in terminal should look like this:
        * ![program_run.jpg](/module_2/Screenshot_program_run.jpg) <br>
    * There will be a newly populated applicant_data.json file in the module_2 folder when it has completed.
5. In terminal, after finished running the project, deactivate venv through: `deactivate`

#### KNOWN BUGS <br>
Not Applicable
