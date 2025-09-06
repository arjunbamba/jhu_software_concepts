from bs4 import BeautifulSoup
import re

class Cleaner:
    def __init__(self, raw_data):
        # Initializing class with passed in list of raw entry dicts originally from Scraper.scrape_data()
        self.raw_data = raw_data

    def _clean_text(self, s):
        # Remove newlines and extra spaces, strip
        if not s:
            return ""
        return " ".join(s.split()).strip()
    

    def _parse_status(self, status_raw):
        # NOTE: I used online tools to make regex commands with examples so there may be some issues/mismatches
        # Extract status/date if possible + return it structurd like (status string, date string)
        # "Accepted on 11 Apr" = ("Accepted", "11 Apr")
        # "Rejected on 20 Apr" = ("Rejected", "20 Apr")
        # "Wait listed on 17 Apr" = ("Waitlisted", "17 Apr")
        # "Interview on 15 Apr" = ("Interview", "15 Apr")

        s = ""
        if status_raw and type(status_raw) == str:
            s = status_raw.strip()

        if not s:
            return "", ""
        
        # unify "Wait listed" to be "Waitlisted"
        s = re.sub(r"wait\s*listed", "Waitlisted", s, flags=re.I)

        # separate into status and status_date
        # look for known status's
        status_match = re.search(r"\b(Accepted|Rejected|Wait listed|Interview|Waitlisted|Withdrawn)\b", s, re.I)
        status = s
        if status_match:
            status = status_match.group(1).title()

        # extract the date after "on"
        date_match = re.search(r"on\s*([\w\d\s,]+)", s, re.I)
        status_date = ""
        if date_match:
            status_date = date_match.group(1).strip()

        # clean up
        status = status.strip()
        status_date = status_date.strip()

        return status, status_date



    def clean_data(self):
        cleaned = []
        
        # Extract raw fields for cleaning
        for raw in self.raw_data:

            # REQUIRED FIELDS 
            program = self._clean_text(raw.get("program_raw", ""))
            university = self._clean_text(raw.get("university_raw", ""))
            date_added = self._clean_text(raw.get("date_added_raw", ""))
            url = self._clean_text(raw.get("url_raw", ""))
            
            status_raw = raw.get("status_raw", "")
            status, status_date = self._parse_status(status_raw)

            # OPTIONAL - aka only if availabe
            comments = self._clean_text(raw.get("comments_raw", ""))
            
            # parse metadata
            meta = raw.get("meta_raw", "")


            # extract deg, but if its empty, check program_raw for any deg at the end like "Computer Science Masters"
            degree = self._clean_text(raw.get("degree_raw", ""))
            if not degree:
                match_deg = re.search(r"(Masters|PhD|MFA|MS|MA)\b", raw.get("program_raw", ""), re.I)
                if match_deg:
                    degree = match_deg.group(1).title()

            # making the capitalzation consistent b/c so both "masters" and "MASTERS" are "Masters"
            degree_clean = ""
            if degree:
                degree_clean = degree.title()

            cleaned_entry = {
                "program": program or "",
                "university": university or "",
                "comments": comments or "",
                "date_added": date_added or "",
                "url": url or "",
                "status": status or "",
                "status_date": status_date or "",
                "Degree": degree_clean or ""
            }

            cleaned.append(cleaned_entry)

        return cleaned
