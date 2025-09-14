import re
# from urllib.request import urlopen
import urllib3
from bs4 import BeautifulSoup

class Scraper:
    def __init__(
            self, 
            url="https://www.thegradcafe.com/survey/", 
            max_entries=30000
    ):
        self.base = url

        self.http = urllib3.PoolManager()
        # self.browser = mechanicalsoup.Browser()
        # self.browser = mechanicalsoup.StatefulBrowser()

        self.max_entries = max_entries
        # self.entries = []


    def scrape_data(self, existing_urls=None):
        # Pulls data from grad cafe.
        existing_urls = existing_urls or set()
        new_entries = []
        page = 1
        stop_scraping = False

        while len(new_entries) < self.max_entries and not stop_scraping:
            url = f"{self.base}?page={page}"
            print(f"Scraping page {page}: {url} (collected {len(new_entries)}/{self.max_entries})")

            html = self._get_html(url)
            if not html:
                print("No HTML returned for URL, stopping.")
                break

            page_entries = self._extract_raw_data(html)
            if not page_entries:
                print("No entries parsed on this page, stopping.")
                break

            # Append and check count
            for e in page_entries:
                if e["url_raw"] in existing_urls:
                    print("Encountered previously-seen entry. Stopping scrape.")
                    stop_scraping = True
                    break
                new_entries.append(e)
                if len(new_entries) >= self.max_entries:
                    break

            page += 1
        
        print(f"Finished scraping. Collected {len(new_entries)} NEW raw entries.")
        print("")
        return new_entries         
    

    def _get_html(self, url):
        # Fetch HTML from the URL

        # lecture reading: using urllib (not compatible with urllib3)
        # page = urlopen(self.url)
        # html_bytes = page.read()
        # html = html_bytes.decode("utf-8")

        # Using urllib3
        response = self.http.request("GET", url)
        html = response.data.decode("utf-8")    # maybe remove decode

        return html

    
    def _extract_raw_data(self, html):
        # NOTE: I used online tools to make regex commands with examples so there may be some issues/mismatches
        # Extract table rows with applicants from current page into list of raw entry dicts
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tbody tr")
        if not rows:
            return []
        
        parsed_entries = []
        i = 0
        while i < len(rows):
            row = rows[i]

            # detect main row by presence of university - td with div class tw-font-medium
            uni_tag = row.select_one("td .tw-font-medium")

            # if missing/class name differs, try backup approach - university name will often be 1st td
            if not uni_tag and row.select_one("td"):
                first_td = row.select_one("td")
                if first_td and first_td.get_text(strip=True):
                    uni_tag = first_td

            if uni_tag:
                # Extract columns for main row (some pages use 5 tds but some fewer)
                tds = row.find_all("td")

                # university = 1st td
                university = ""
                if len(tds) >= 1:
                    university = tds[0].get_text(" ", strip=True)

                # program + degree = 2nd td (often uses <span>)
                program = ""
                degree = ""
                if len(tds) >= 2:
                    # get all spans in 2nd td
                    spans = tds[1].select("span")

                    # program = 1st span
                    if len(spans) >= 1:
                        program = spans[0].get_text(strip=True)

                    # degree = last span text (ex: "Masters"/"PhD") OR maybe 2nd span with class tw-text-gray-500
                    if len(spans) >= 2:
                        degree = spans[-1].get_text(strip=True)
                    else:
                        possible_degree = tds[1].get_text(" ", strip=True)

                        # remove program part if it's there
                        if program and possible_degree.startswith(program):
                            d = possible_degree[len(program):].strip()
                            if d:
                                degree = d

                # date added = 3rd td
                date_added = ""
                if len(tds) >= 3:
                    date_added = tds[2].get_text(" ", strip=True)

                # status = 4th td
                status_raw = ""
                if len(tds) >= 4:
                    status_raw = tds[3].get_text(" ", strip=True)

                # result url = find anchor in curr row with href containing /result/
                url = ""
                a = row.find("a", href=True)
                if a and "/result/" in a["href"]:
                    href = a["href"]
                    if href.startswith("http"):
                        url = href
                    else:
                        url = "https://www.thegradcafe.com" + href

                # Prepare raw entry
                raw_entry = {
                    "university_raw": university or "",
                    "program_raw": program or "",
                    "degree_raw": degree or "",
                    "date_added_raw": date_added or "",
                    "status_raw": status_raw or "",
                    "url_raw": url or "",
                    "meta_raw": "",
                    "comments_raw": ""
                }

                # Look ahead for metadata / comments rows (usually next 1-2 rows)

                # metadata rows often contain small inline-flex divs (term, origin, GPA)
                if i + 1 < len(rows):
                    next_row = rows[i + 1]

                    # metadata row often has colspan or class 'tw-border-none'
                    meta_text = next_row.get_text(" | ", strip=True)

                    # If meta_text contains term or GPA or American/International, take it
                    if re.search(r"Fall\s*\d{4}|Spring\s*\d{4}|GPA\s*\d|American|International", meta_text, re.I):
                        raw_entry["meta_raw"] = meta_text
                        i += 1  # consume metadata row

                # another look ahead for a commet row that contains <p class="tw-text-gray-500">
                if i + 1 < len(rows):
                    maybe_comment = rows[i + 1]
                    p = maybe_comment.find("p")
                    if p and p.get_text(strip=True):
                        raw_entry["comments_raw"] = p.get_text(" ", strip=True)
                        i += 1  # consume comment row

                parsed_entries.append(raw_entry)

            # move to next row
            i += 1

        return parsed_entries