"""Author enricher for WhoCitedMe.

This module provides the AuthorEnricher class for enriching truncated author
information in citation data by fetching full author details from Google Scholar.
"""

import os
import re
import time
import urllib.parse
from typing import Any, Optional

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from whocitedme.utils.browser import create_chrome_driver
from whocitedme.utils.captcha import check_and_wait_captcha, random_sleep


class AuthorEnricher:
    """
    Enricher for completing truncated author information in citation data.

    When Google Scholar search results show truncated author lists (with "..."),
    this class fetches the full author information by:
    1. Searching for the paper on Google Scholar
    2. Extracting visible author names and IDs from the result
    3. Clicking "Cite" to get the Chicago format citation with full author names
    4. Merging visible ID mappings with full Chicago names

    Example:
        >>> enricher = AuthorEnricher(
        ...     input_file="citations.csv",
        ...     output_file="citations_enriched.csv",
        ... )
        >>> enricher.run()
    """

    def __init__(
        self,
        input_file: str = "output/citations.csv",
        output_file: str = "output/citations_enriched.csv",
        headless: bool = False,
    ):
        """
        Initialize the AuthorEnricher.

        Args:
            input_file: Path to input CSV with citation data.
            output_file: Path to output CSV for enriched data.
            headless: Run browser in headless mode (not recommended for CAPTCHA).
        """
        self.input_file = input_file
        self.output_file = output_file

        print("Starting Chrome for Author Enrichment...")
        self.driver = create_chrome_driver(headless=headless, incognito=True)
        print("Chrome started successfully")

    def _parse_chicago_authors(self, citation_text: str) -> dict[str, Any]:
        """Parse Chicago citation format to extract full author names."""
        data: dict[str, Any] = {}

        first_quote_idx = citation_text.find('"')

        if first_quote_idx != -1:
            author_str = citation_text[:first_quote_idx].replace(".", "").strip()
        else:
            return {}

        data["raw_authors"] = author_str
        author_str_clean = author_str.replace(", and ", ", ").replace(" and ", ", ")
        parts = [p.strip() for p in author_str_clean.split(",")]

        final_authors = []
        if not parts:
            return data

        if len(parts) >= 2:
            first_author_fl = f"{parts[1]} {parts[0]}"
            final_authors.append(first_author_fl)
            final_authors.extend(parts[2:])
        else:
            final_authors.append(parts[0])

        data["authors"] = "; ".join(final_authors)
        return data

    def _parse_google_scholar_metadata(self, result_element) -> dict[str, Any]:
        """
        Parse metadata from a Google Scholar search result element.

        Extracts:
        - visible_authors_list: List of dicts with 'name' and 'id'
        - venue: Publication venue
        - year: Publication year
        - is_truncated: Whether author list is truncated
        """
        data: dict[str, Any] = {
            "visible_authors_list": [],
            "venue": "",
            "year": "",
            "is_truncated": False,
        }

        try:
            # Locate outer container
            try:
                meta_div = result_element.find_element(By.CSS_SELECTOR, ".gs_a.gs_fma_p")
            except Exception:
                gs_as = result_element.find_elements(By.CLASS_NAME, "gs_a")
                if gs_as:
                    meta_div = gs_as[-1]
                else:
                    return data

            # Process author container
            try:
                author_div = meta_div.find_element(By.CLASS_NAME, "gs_fmaa")

                author_text_raw = author_div.get_attribute("textContent")
                if "…" in author_text_raw or "..." in author_text_raw:
                    data["is_truncated"] = True

                author_text_clean = author_text_raw.replace("…", "").replace("...", "")

                # Build ID mapping
                link_map = {}
                links = author_div.find_elements(By.TAG_NAME, "a")
                for link in links:
                    name = link.get_attribute("textContent").strip()
                    href = link.get_attribute("href")
                    if name and href and "user=" in href:
                        uid_match = re.search(r"user=([^&]+)", href)
                        if uid_match:
                            link_map[name] = uid_match.group(1)

                # Split and match IDs
                author_names = [n.strip() for n in author_text_clean.split(",") if n.strip()]
                for name in author_names:
                    uid = link_map.get(name, "NO_GS_ID")
                    data["visible_authors_list"].append({"name": name, "id": uid})

                print(f"   + Extracted {len(data['visible_authors_list'])} authors from gs_fmaa")

            except Exception as e:
                print(f"   ! gs_fmaa not found or error: {e}")
                return data

            # Extract Venue and Year
            full_text = meta_div.get_attribute("textContent")
            rest_text = full_text.replace(author_div.get_attribute("textContent"), "")

            if rest_text:
                year_match = re.search(r"\b(19|20)\d{2}\b", rest_text)
                if year_match:
                    data["year"] = year_match.group(0)

                venue_clean = rest_text
                if data["year"]:
                    venue_clean = venue_clean.split(data["year"])[0]

                data["venue"] = venue_clean.split(",")[0].strip()

        except Exception as e:
            print(f"   ! Error parsing metadata: {e}")

        return data

    def _merge_authors(
        self, visible_data: list[dict], chicago_full_authors_str: str
    ) -> Optional[dict[str, Any]]:
        """Merge visible author IDs with full author names from Chicago format."""
        if not chicago_full_authors_str:
            return None

        full_list = [x.strip() for x in chicago_full_authors_str.split(";")]
        final_ids = []
        final_names = []
        is_still_truncated = False

        # Track which visible authors have been matched
        matched_visible_indices = set()

        for full_name in full_list:
            if "et al" in full_name.lower() or "and others" in full_name.lower():
                is_still_truncated = True
                full_name = full_name.split("et al")[0].strip()
                if not full_name:
                    continue

            matched_id = None

            for idx, v_auth in enumerate(visible_data):
                if idx in matched_visible_indices:
                    continue

                v_name = v_auth["name"]
                v_id = v_auth["id"]

                v_parts = v_name.split()
                v_last = v_parts[-1] if v_parts else ""

                if v_last.lower() in full_name.lower():
                    if v_parts[0][0].lower() in full_name.lower():
                        if v_id:
                            matched_id = v_id
                            matched_visible_indices.add(idx)
                        break

            final_names.append(full_name)
            if matched_id:
                final_ids.append(f"{full_name}:{matched_id}")
            else:
                final_ids.append(f"{full_name}:WAITING_FOR_ID")

        # Handle case where visible_data has more authors than Chicago list
        if visible_data:
            max_matched_idx = max(matched_visible_indices) if matched_visible_indices else -1

            if max_matched_idx < len(visible_data) - 1:
                # Append remaining visible authors
                for idx in range(max_matched_idx + 1, len(visible_data)):
                    v_auth = visible_data[idx]
                    v_name = v_auth["name"]
                    v_id = v_auth["id"]

                    final_names.append(v_name)
                    if v_id:
                        final_ids.append(f"{v_name}:{v_id}")
                    else:
                        final_ids.append(f"{v_name}:WAITING_FOR_ID")

        return {
            "authors": "; ".join(final_names),
            "ids": "; ".join(final_ids),
            "truncated": is_still_truncated,
        }

    def _fallback_to_visible(self, visible_authors: list[dict]) -> dict[str, Any]:
        """Create output from visible authors when enrichment fails."""
        names = []
        ids = []
        for auth in visible_authors:
            names.append(auth["name"])
            if auth["id"]:
                ids.append(f"{auth['name']}:{auth['id']}")
            else:
                ids.append(f"{auth['name']}:WAITING_FOR_ID")

        return {
            "authors": "; ".join(names),
            "author_ids": "; ".join(ids),
            "is_truncated": False,
        }

    def _enrich_row(self, row: pd.Series) -> Optional[dict[str, Any]]:
        """Enrich a single row with full author information."""
        title = row["Citing_Title"]
        print(f"Processing: {title}")

        search_term = title + " " + row["Citing_Authors"].split(",")[0]
        query = urllib.parse.quote(search_term)
        url = f"https://scholar.google.com/scholar?q={query}&hl=en&as_vis=1"

        self.driver.get(url)
        check_and_wait_captcha(self.driver)
        random_sleep(1.5, 3)

        try:
            results = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_r.gs_or[data-did]")
            if not results:
                print("   - No results found.")
                return None

            if len(results) > 1:
                domain = urllib.parse.urlparse(row["Citing_Link"]).netloc
                search_term = search_term + " site:" + domain
                query = urllib.parse.quote(search_term)
                url = f"https://scholar.google.com/scholar?q={query}&hl=en&as_vis=1"
                self.driver.get(url)
                check_and_wait_captcha(self.driver)
                random_sleep(1.5, 3)
                results = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_r.gs_or[data-did]")
                if not results:
                    print("   - No results found.")
                    return None

            if len(results) > 1:
                print("   - Multiple results found, returning None")
                return None

            target_result = results[0]

            metadata = self._parse_google_scholar_metadata(target_result)
            extracted_venue = metadata["venue"]
            extracted_year = metadata["year"]
            visible_authors = metadata["visible_authors_list"]
            is_truncated = metadata["is_truncated"]

            print(f"   + Visible Authors: {len(visible_authors)}")
            print(f"   + Venue: {extracted_venue}, Year: {extracted_year}")

            final_data: dict[str, Any] = {}

            if is_truncated:
                print("   + Authors truncated, clicking Cite...")
                try:
                    cite_btn = target_result.find_element(By.CLASS_NAME, "gs_or_cit")
                    cite_btn.click()
                    time.sleep(2)
                    WebDriverWait(self.driver, 4).until(
                        EC.presence_of_element_located((By.ID, "gs_citt"))
                    )

                    chicago_th = self.driver.find_element(
                        By.XPATH, "//th[contains(text(), 'Chicago')]"
                    )
                    chicago_div = chicago_th.find_element(
                        By.XPATH, "./following-sibling::td/div[@class='gs_citr']"
                    )
                    citation_text = chicago_div.text

                    parsed_chicago = self._parse_chicago_authors(citation_text)
                    full_authors_str = parsed_chicago.get("authors", "")

                    merged = self._merge_authors(visible_authors, full_authors_str)
                    if merged:
                        final_data["authors"] = merged["authors"]
                        final_data["author_ids"] = merged["ids"]
                        final_data["is_truncated"] = merged["truncated"]

                except Exception as e:
                    print(f"   ! Error during Cite click/parse: {e}")
                    final_data = self._fallback_to_visible(visible_authors)
            else:
                print("   + Authors complete, using visible data.")
                final_data = self._fallback_to_visible(visible_authors)

            if extracted_venue:
                final_data["venue"] = extracted_venue
            if extracted_year:
                final_data["year"] = extracted_year


            return final_data

        except Exception as e:
            print(f"   ! Error enriching: {e}")
            return None

    def run(self, resume: bool = True) -> None:
        """
        Run the enrichment process.

        Args:
            resume: If True, resume from existing output file.
        """
        df: Optional[pd.DataFrame] = None

        if resume and os.path.exists(self.output_file):
            print(f"Found existing output file: {self.output_file}")
            print("Resuming from checkpoint...")
            try:
                df = pd.read_csv(self.output_file)
            except Exception as e:
                print(f"Error reading existing output file: {e}")
                print("Falling back to input file...")

        if df is None:
            if not os.path.exists(self.input_file):
                print(f"Input file not found: {self.input_file}")
                return
            print(f"Starting fresh processing from: {self.input_file}")
            df = pd.read_csv(self.input_file)

        df["Citing_Authors"] = df["Citing_Authors"].astype(str)

        mask = (
            (df["Is_Authors_Truncated"] == True)
            | (df["Citing_Authors"].str.contains("…", regex=False))
            | (df["Citing_Authors"].str.contains(r"\.\.\.", regex=True))
        )
        indices = df[mask].index
        print(f"Found {len(indices)} truncated entries to enrich.")

        total_count = len(indices)
        processed_count = 0

        try:
            for i, idx in enumerate(indices):
                print(f"[{i+1}/{total_count}] ", end="")
                row = df.loc[idx]
                enriched_data = self._enrich_row(row)

                if enriched_data:
                    if "authors" in enriched_data:
                        df.at[idx, "Citing_Authors"] = enriched_data["authors"]
                    if "author_ids" in enriched_data:
                        df.at[idx, "Citing_Author_IDs"] = enriched_data["author_ids"]
                    if "is_truncated" in enriched_data:
                        df.at[idx, "Is_Authors_Truncated"] = enriched_data["is_truncated"]
                    if "venue" in enriched_data and enriched_data["venue"]:
                        df.at[idx, "Citing_Journal_Conf"] = enriched_data["venue"]
                    if "year" in enriched_data and enriched_data["year"]:
                        df.at[idx, "Citing_Year"] = enriched_data["year"]

                    print("   -> Done.")

                processed_count += 1
                if processed_count % 3 == 0:
                    df.to_csv(self.output_file, index=False, encoding="utf_8_sig")
                    print("   [Saved progress]")

        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            print("Saving final results...")
            df.to_csv(self.output_file, index=False, encoding="utf_8_sig")
            self.driver.quit()

    def close(self) -> None:
        """Close the browser driver."""
        if hasattr(self, "driver"):
            self.driver.quit()
