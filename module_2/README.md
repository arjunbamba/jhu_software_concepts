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

##### Overall Implementation:
I implemented main.py as my central hub/program processor which initializes the necessary Scraper + Cleaner classes and calls the core relevant methods i.e. scrape_data() and clean_data(). One core piece of logic important to note here is that the Cleaner class is initialized with the raw_data outputed by scrape_data() - so it can clean raw_data that was scraped.

I have two core files: scrape.py and clean.py. Each file has its own class with its own methods. 

Within Scraper in scrape.py:
* get_html() fetches the html content using urllib3.
* extract_raw_data() uses BeautifulSoup and html/css/string selectors to extract the core pieces of each applicant row. This is done by referring to Inspect Element/Show Page Source html. 
    * Note: I was not too sure whether to refer to Inspect Element/Show Page Source for the extraction of the raw data because some of the classes seem dynamically generated, but I got it to work by referring to those classes/elements within Inspect Element/Show Page Source and going through each page one by one in scrape_data (so at least when it's processing it after it's been loaded, it should be static). 

Within Cleaner in clean.py:
* clean_data() contains core driver logic of cleaning.
    * Processing each raw data row one by one
    * Calling various private helper methods to extract each of the required/relevant fields
    * Note: I used online tools to help make regex commands/pattern matching syntax with examples, so there may be some minor issues/mismatches (but I feel I've mostly worked it out). Also used HTML/JSON formatters to help see the table data in a neater way.
* Initialized with the raw_data output from scrape_data()

applicant_data.json contains the 30,000 minimum required entries.
llm_extend_applicant_data.json contains the processed json after running the llm model.


#### **TO RUN THE PROJECT:**
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
