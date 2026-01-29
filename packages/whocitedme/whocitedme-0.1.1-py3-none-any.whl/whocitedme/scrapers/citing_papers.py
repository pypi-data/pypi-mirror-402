"""Citing papers scraper for WhoCitedMe.

This module provides the CitingPapersScraper class for scraping all papers
that cite a given Google Scholar author's publications.
"""

import json
import os
import re
import time
import urllib.parse
from typing import Optional

import pandas as pd
from selenium.webdriver.common.by import By

from whocitedme.utils.browser import create_undetected_chrome_driver, create_chrome_driver
from whocitedme.utils.captcha import check_and_wait_captcha, random_sleep


class CitingPapersScraper:
    """
    Scraper for extracting papers that cite a Google Scholar author's publications.

    This scraper navigates Google Scholar, retrieves all papers by a given author,
    and for each paper, collects all citing papers with their metadata including
    title, authors, author IDs, venue, and year.

    Features:
    - Recursive time-based and keyword-based splitting to handle >1000 results
    - Resumable scraping with progress logging
    - Duplicate detection based on title
    - CAPTCHA detection with manual resolution support

    Example:
        >>> scraper = CitingPapersScraper(
        ...     user_id="5RF4ia8AAAAJ",  # Yann LeCun's Google Scholar ID
        ...     start_year=2020,
        ...     end_year=2024,
        ... )
        >>> scraper.run()
    """

    COLUMNS = [
        "Source_Paper",
        "Citing_Title",
        "Citing_Link",
        "Citing_Year",
        "Citing_Journal_Conf",
        "Citing_Authors",
        "Citing_Author_IDs",
        "Is_Authors_Truncated",
        "Query_Tag",
    ]

    def __init__(
        self,
        user_id: str,
        start_year: int,
        end_year: int,
        output_file: str = "output/citations.csv",
        headless: bool = False,
        undetected_chrome_driver: Optional[bool] = False,
    ):
        """
        Initialize the CitingPapersScraper.

        Args:
            user_id: Google Scholar author ID (found in profile URL after "user=").
            start_year: Start year for filtering citations.
            end_year: End year for filtering citations.
            output_file: Path to output CSV file.
            headless: Run browser in headless mode (not recommended for CAPTCHA).
        """
        self.user_id = user_id
        self.base_url = "https://scholar.google.com/scholar"
        self.user_profile_base = f"https://scholar.google.com/citations?user={user_id}&hl=en"
        self.start_year = int(start_year)
        self.end_year = int(end_year)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        self.output_file = output_file

        # Initialize browser
        if undetected_chrome_driver:
            self.driver = create_undetected_chrome_driver(
                headless=headless,
                incognito=True,
            )
        else:
            self.driver = create_chrome_driver(
                headless=headless,
                incognito=True,
            )

        # Initialize or load existing CSV
        if not os.path.exists(self.output_file):
            pd.DataFrame(columns=self.COLUMNS).to_csv(
                self.output_file, index=False, encoding="utf_8_sig"
            )

        # Deduplication set based on titles
        self.scraped_titles: set[str] = set()
        if os.path.exists(self.output_file):
            try:
                df = pd.read_csv(self.output_file)
                self.scraped_titles = set(
                    [title.lower().strip() for title in df["Citing_Title"].dropna().tolist()]
                )
            except Exception:
                pass

        # Resumption: completed paper IDs
        self.completed_log = self.output_file.replace(".csv", ".completed")
        self.completed_ids: set[str] = set()
        if os.path.exists(self.completed_log):
            with open(self.completed_log, "r") as f:
                self.completed_ids = set(line.strip() for line in f if line.strip())
            print(f"Found checkpoint: {len(self.completed_ids)} papers already completed")

        # Fine-grained pagination progress
        self.progress_file = self.output_file.replace(".csv", "_progress.json")
        self.progress_data: dict[str, int] = {}
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r") as f:
                    self.progress_data = json.load(f)
                print(f"Found pagination progress: {len(self.progress_data)} entries")
            except Exception:
                pass

    def _get_result_count(self) -> int:
        """Parse the approximate result count from the search page."""
        try:
            ele = self.driver.find_element(By.ID, "gs_ab_md")
            txt = ele.text
            match = re.search(r"(?:About\s+)?([\d,]+)\s+results", txt)
            if match:
                return int(match.group(1).replace(",", ""))

            match_small = re.search(r"^([\d,]+)\s+results", txt)
            if match_small:
                return int(match_small.group(1).replace(",", ""))
        except Exception:
            results = self.driver.find_elements(By.CLASS_NAME, "gs_r")
            if results:
                return len(results)
        return 0

    def _parse_metadata_row(
        self, element, source_paper_title: str, query_tag: str
    ) -> Optional[dict]:
        """Parse a single search result row into metadata dict."""
        try:
            title_tag = element.find_element(By.CLASS_NAME, "gs_rt")
            title = title_tag.text.strip()

            link = ""
            if title_tag.find_elements(By.TAG_NAME, "a"):
                link = title_tag.find_element(By.TAG_NAME, "a").get_attribute("href")

            meta_div = element.find_element(By.CLASS_NAME, "gs_a")
            meta_text = meta_div.text

            # Extract author IDs from Scholar profile links
            author_ids = []
            for a in meta_div.find_elements(By.TAG_NAME, "a"):
                href = a.get_attribute("href")
                if href and "user=" in href:
                    uid = re.search(r"user=([^&]+)", href)
                    if uid:
                        author_ids.append(f"{a.text}:{uid.group(1)}")

            # Extract year
            year_match = re.search(r"\b(19|20)\d{2}\b", meta_text)
            year = year_match.group(0) if year_match else ""

            # Split author and venue
            parts = meta_text.split(" - ")
            author_part = parts[0] if parts else ""
            journal_conf = parts[1].replace(f", {year}", "").strip() if len(parts) > 1 else ""

            return {
                "Source_Paper": source_paper_title,
                "Citing_Title": title,
                "Citing_Link": link,
                "Citing_Year": year,
                "Citing_Journal_Conf": journal_conf,
                "Citing_Authors": author_part,
                "Citing_Author_IDs": "; ".join(author_ids),
                "Is_Authors_Truncated": "…" in author_part,
                "Query_Tag": query_tag,
            }
        except Exception as e:
            print(f"Parse error: {e}")
            return None

    def _construct_citation_url(
        self,
        cites_id: str,
        y_start: int,
        y_end: int,
        keywords: Optional[str] = None,
    ) -> str:
        """Construct URL for citation search with filters."""
        params = {
            "cites": cites_id,
            "as_ylo": y_start,
            "as_yhi": y_end,
            "hl": "en",
            "scipsc": 1,
        }
        if keywords:
            params["q"] = keywords

        return f"{self.base_url}?{urllib.parse.urlencode(params)}"

    def _crawl_recursive(
        self,
        cites_id: str,
        source_title: str,
        y_start: int,
        y_end: int,
        keyword_filter: Optional[str] = None,
    ) -> None:
        """
        Recursively crawl citations with time/keyword splitting strategy.

        Google Scholar limits results to 1000 per query. This method splits
        queries by year range and keywords to capture all results.
        """
        target_url = self._construct_citation_url(cites_id, y_start, y_end, keyword_filter)

        tag_info = f"[{y_start}-{y_end}]"
        if keyword_filter:
            tag_info += f" q='{keyword_filter}'"
        print(f"🔍 Checking: {tag_info}")

        self.driver.get(target_url)
        check_and_wait_captcha(self.driver)
        random_sleep(2, 4)

        count = self._get_result_count()
        print(f"   -> Count: {count}")

        # Strategy branching
        if count <= 1000:
            if count > 0:
                self._crawl_pagination(target_url, source_title, tag_info)
            else:
                print("   -> No results, skipping.")
            return

        # Strategy 1: Year splitting
        if y_start < y_end:
            mid = (y_start + y_end) // 2
            print(f"   ✂️  Too many results ({count}), splitting by year: {y_start}-{mid} and {mid+1}-{y_end}")
            self._crawl_recursive(cites_id, source_title, y_start, mid, keyword_filter)
            self._crawl_recursive(cites_id, source_title, mid + 1, y_end, keyword_filter)
            return

        # Strategy 2: Keyword splitting (for single year)
        if y_start == y_end:
            if keyword_filter is None or keyword_filter == "":
                print(f"   ✂️  Single year too large ({count}), splitting by keyword: 'CVPR' vs '-CVPR'")
                self._crawl_recursive(cites_id, source_title, y_start, y_end, keyword_filter="CVPR")
                self._crawl_recursive(cites_id, source_title, y_start, y_end, keyword_filter="-CVPR")
                return

            # Edge case: still >1000 after keyword split
            print(f"   ⚠️ Warning: Still {count} results after keyword split. Will scrape first 1000 only.")
            self._crawl_pagination(target_url, source_title, tag_info)

    def _crawl_pagination(self, url: str, source_title: str, query_tag: str) -> None:
        """Crawl through paginated results."""
        # Generate unique progress key
        cites_id_match = re.search(r"cites=(\d+)", url)
        cites_id = cites_id_match.group(1) if cites_id_match else "unknown"
        ylo_match = re.search(r"as_ylo=(\d+)", url)
        yhi_match = re.search(r"as_yhi=(\d+)", url)
        q_match = re.search(r"q=([^&]+)", url)

        ylo = ylo_match.group(1) if ylo_match else "any"
        yhi = yhi_match.group(1) if yhi_match else "any"
        q_val = q_match.group(1) if q_match else "none"

        progress_key = f"{cites_id}_{ylo}_{yhi}_{q_val}"

        start = self.progress_data.get(progress_key, 0)
        if start > 0:
            print(f"      🔄 Resuming from: {progress_key} -> start={start}")

        while True:
            # Construct pagination URL
            if "start=" in url:
                page_url = re.sub(r"start=\d+", f"start={start}", url)
            else:
                page_url = f"{url}&start={start}"

            self.driver.get(page_url)
            check_and_wait_captcha(self.driver)
            random_sleep(1.5, 3)

            results = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_r.gs_or[data-did]")

            if not results:
                break

            batch_data = []
            for res in results:
                # Class check is implicit in the selector
                data = self._parse_metadata_row(res, source_title, query_tag)
                if data:
                    title_norm = data["Citing_Title"].lower().strip()
                    if title_norm and title_norm in self.scraped_titles:
                        print(f"      - Skipping duplicate: {title_norm[:50]}...")
                        continue

                    batch_data.append(data)
                    if title_norm:
                        self.scraped_titles.add(title_norm)

            if batch_data:
                pd.DataFrame(batch_data).to_csv(
                    self.output_file, mode="a", header=False, index=False, encoding="utf_8_sig"
                )
                print(f"      + Saved {len(batch_data)} records (start={start})")
            else:
                print(f"      + No new data on this page (start={start})")

            # Save progress
            next_start = start + 10
            self.progress_data[progress_key] = next_start
            with open(self.progress_file, "w") as f:
                json.dump(self.progress_data, f, indent=4)

            # Check for next page button
            next_btns = self.driver.find_elements(
                By.XPATH, "//span[contains(@class, 'gs_ico_nav_next')]/parent::a"
            )
            if not next_btns or start >= 990:
                break

            start = next_start

    def run(self) -> None:
        """
        Run the full scraping pipeline.

        This method:
        1. Opens the author's Google Scholar profile
        2. Loads all papers by clicking "Show More"
        3. For each cited paper, recursively scrapes all citing papers
        4. Saves results to CSV with resumption support
        """
        print(f"Visiting author profile: {self.user_profile_base}")
        self.driver.get(f"{self.user_profile_base}&pagesize=100")
        random_sleep()

        # Click "Show More" to load all papers
        while True:
            try:
                btn = self.driver.find_element(By.ID, "gsc_bpf_more")
                if not btn.is_enabled():
                    break
                btn.click()
                print("Clicking Show More...")
                random_sleep(2, 4)
            except Exception:
                break

        # Extract papers with citations
        papers = []
        rows = self.driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
        for row in rows:
            try:
                title_ele = row.find_element(By.CLASS_NAME, "gsc_a_at")
                title = title_ele.text
                cites_link_ele = row.find_element(By.CLASS_NAME, "gsc_a_ac")
                cites_link = cites_link_ele.get_attribute("href")
                cites_num_text = cites_link_ele.text

                if not cites_num_text or int(cites_num_text.replace("*", "")) == 0:
                    continue

                cites_id_match = re.search(r"cites=(\d+)", cites_link)
                if cites_id_match:
                    papers.append({
                        "title": title,
                        "id": cites_id_match.group(1),
                        "count": int(cites_num_text.replace("*", "")),
                    })
            except Exception:
                pass

        print(f"Found {len(papers)} papers with citations. Starting detailed scrape...")

        for i, p in enumerate(papers):
            print(f"\n[{i+1}/{len(papers)}] 🚀 Processing: {p['title']} (citations: {p['count']})")

            if p["id"] in self.completed_ids:
                print("   ⚠️ Already completed, skipping.")
                continue

            try:
                self._crawl_recursive(p["id"], p["title"], self.start_year, self.end_year)
                # Mark as completed only if crawling succeeded
                with open(self.completed_log, "a") as f:
                    f.write(f"{p['id']}\n")
                self.completed_ids.add(p["id"])
                print(f"   ✅ Successfully completed: {p['title']}")
            except Exception as e:
                print(f"   ❌ Failed to scrape: {p['title']}")
                print(f"      Error: {type(e).__name__}: {e}")
                print(f"      Paper ID {p['id']} will be retried on next run.")

        print("\n✅ All tasks completed.")
        self.driver.quit()

    def close(self) -> None:
        """Close the browser driver."""
        if hasattr(self, "driver"):
            self.driver.quit()
