from bs4 import BeautifulSoup
import re

class Cleaner:
    def __init__(self, raw_data):
        """Initialise the cleaner with raw entries emitted by the scraper.

        :param list[dict] raw_data: Unnormalised GradCafe rows captured by
            :class:`~homework_sample_code.course_app.scrape.Scraper`.
        """
        self.raw_data = raw_data

    def _clean_text(self, s):
        """Collapse whitespace and normalise simple text blocks.

        :param str s: Raw text segment.
        :return: Whitespace-normalised variant of ``s``.
        :rtype: str
        """
        if not s:
            return ""
        return " ".join(s.split()).strip()
    

    def _parse_status(self, status_raw):
        """Split status strings into state and date components.

        :param str status_raw: Raw status cell pulled from the GradCafe table.
        :return: Tuple of normalised status and optional date text.
        :rtype: tuple[str, str]
        """

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


    def _extract_term(self, meta_text):
        """Read the admission term from the metadata block when present.

        :param str meta_text: Concatenated metadata text for the row.
        :return: Normalised term such as ``"Fall 2025"`` or an empty string.
        :rtype: str
        """

        if not meta_text:
            return ""
        
        match = re.search(r"(Fall|Spring|Summer|Winter)\s*(\d{4})", meta_text, re.I)
        if match:
            return f"{match.group(1).title()} {match.group(2)}"
        
        return ""


    def _extract_origin(self, meta_text):
        """Identify whether an applicant is domestic or international.

        :param str meta_text: Concatenated metadata text for the row.
        :return: ``"American"``, ``"International"``, or ``""`` when
            unavailable.
        :rtype: str
        """

        if not meta_text:
            return ""
        
        if re.search(r"\bAmerican\b", meta_text, re.I):
            return "American"
        elif re.search(r"\bInternational\b", meta_text, re.I):
            return "International"
        
        return ""


    def _extract_gpa(self, meta_text):
        """Extract a GPA token from metadata or comment text.

        :param str meta_text: Raw metadata string associated with the row.
        :return: GPA string (e.g., ``"3.80"``) or ``""`` when absent.
        :rtype: str
        """

        if not meta_text:
            return ""
        
        match = re.search(r"GPA\s*[:]*\s*([0-9]\.\d{1,2})", meta_text, re.I)
        if match:
            return match.group(1)
        
        # sometimes it shows GPA 3.50 without punctuation
        match2 = re.search(r"GPA\s*([0-9]\.\d{1,2})", meta_text, re.I)
        if match2:
            return match2.group(1)
        
        return ""


    def _extract_gre(self, text):
        """Extract GRE overall, verbal, and writing scores from free text.

        :param str text: Combined comments and metadata text.
        :return: Tuple of overall GRE, verbal, and analytical writing values as
            strings; each component may be ``""`` when not detected.
        :rtype: tuple[str, str, str]
        """
        if not text:
            return "", "", ""

        # GRE
        gre_overall = ""
        match1 = re.search(r"\bGRE[:\s]*([0-9]{3})\b", text, re.I)
        if match1:
            gre_overall = match1.group(1)

        # GRE V
        gre_v = ""
        match2 = re.search(r"(?:V[:\s]*|Verbal[:\s]*)([0-9]{2,3})", text, re.I)
        if match2:
            gre_v = match2.group(1)
        else:
            # sometimes shown like "165 V"
            match2b = re.search(r"\b([0-9]{2,3})\s*V\b", text, re.I)
            if match2b:
                gre_v = match2b.group(1)

        # GRE AW
        gre_aw = ""
        match3 = re.search(r"(?:AW|AWA|Analytical Writing)[:\s]*([0-9]\.?\d?)", text, re.I)
        if match3:
            gre_aw = match3.group(1)

        return gre_overall, gre_v, gre_aw


    def clean_data(self):
        """Normalise the raw GradCafe entries into the application schema.

        :return: Cleaned applicant records suitable for persistence.
        :rtype: list[dict]
        """
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

            # gpa likely inside meta but can be in comment also
            term = self._extract_term(meta)
            origin = self._extract_origin(meta)
            gpa = self._extract_gpa(meta) or self._extract_gpa(comments)

            # extract GRE from comments + meta (comments likely)
            gre_overall, gre_v, gre_aw = self._extract_gre(comments + " " + meta)

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
                "term": term or "",
                "US/International": origin or "",
                "GRE": gre_overall or "",
                "GRE V": gre_v or "",
                "GRE AW": gre_aw or "",
                "GPA": gpa or "",
                "Degree": degree_clean or "",
                # ensure consistency with existing llm_extend_applicant_data.json
                "llm-generated-program": "",
                "llm-generated-university": ""
            }

            cleaned.append(cleaned_entry)

        return cleaned
