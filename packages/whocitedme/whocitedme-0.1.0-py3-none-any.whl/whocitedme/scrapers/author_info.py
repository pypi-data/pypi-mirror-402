"""Author info fetcher for WhoCitedMe.

This module provides the AuthorInfoFetcher class for fetching detailed
information about Google Scholar authors, including citation counts,
affiliations, and Fellow status.
"""

import csv
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Optional

import pandas as pd
from scholarly import ProxyGenerator, scholarly


class AuthorInfoFetcher:
    """
    Fetcher for Google Scholar author information.

    This class extracts Scholar IDs from citation data and fetches detailed
    information for each author including:
    - Name
    - Total citation count
    - Affiliation
    - Inferred Fellow status (IEEE Fellow, ACM Fellow, etc.)

    Example:
        >>> fetcher = AuthorInfoFetcher(
        ...     input_file="citations_enriched.csv",
        ...     output_file="scholar_database.csv",
        ... )
        >>> fetcher.run(max_workers=16)
    """

    DEFAULT_FELLOW_KEYWORDS = [
        "IEEE Fellow",
        "ACM Fellow",
        "AAAS Fellow",
        "AAAI Fellow",
        "IAPR Fellow",
        "ACL Fellow",
        "ISCA Fellow",
        "CAAI Fellow",
        "CCF Fellow",
        "Life Fellow",
        "Fellow of the",
        "Fellow of",
        "Distinguished Professor",
        "Distinguished Scientist",
        "Distinguished Researcher",
        "FWAST",
        "FAIIA",
        "FNAE",
        "FAAIA",
        "FIAPR",
        "FIEEE",
        "FACM",
        "Fellow",  # Keep generic Fellow last as fallback, relying on exclusions
    ]

    FIELDNAMES = [
        "Scholar_ID",
        "Name",
        "Total_Citations",
        "Affiliation",
        "Is_Fellow",
        "Inferred_Title",
        "Scrape_Time",
        "Fellowship"
    ]

    def __init__(
        self,
        input_file: str = "output/citations_enriched.csv",
        output_file: str = "output/scholar_database.csv",
        use_proxy: bool = False,
        proxy_address: str = "http://127.0.0.1:7890",
        fellow_keywords: Optional[list[str]] = None,
    ):
        """
        Initialize the AuthorInfoFetcher.

        Args:
            input_file: Path to input CSV with citation data containing author IDs.
            output_file: Path to output CSV for author information.
            use_proxy: Whether to use a proxy for requests.
            proxy_address: Proxy address (e.g., "http://127.0.0.1:7890").
            fellow_keywords: Keywords to detect Fellow status in affiliations.
        """
        self.input_file = input_file
        self.output_file = output_file
        self.use_proxy = use_proxy
        self.proxy_address = proxy_address
        self.fellow_keywords = fellow_keywords or self.DEFAULT_FELLOW_KEYWORDS

    def _setup_proxy(self) -> None:
        """Configure proxy for scholarly library."""
        if self.use_proxy:
            pg = ProxyGenerator()
            try:
                success = pg.SingleProxy(http=self.proxy_address, https=self.proxy_address)
                scholarly.use_proxy(pg)
                print(f"[Info] Proxy configured: {self.proxy_address}")
            except Exception as e:
                print(f"[Error] Proxy configuration failed: {e}")
                print("[Warning] Will use local network (higher risk of blocking)")

    def _get_all_ids_from_source(self) -> list[str]:
        """Extract all unique Scholar IDs from the input CSV."""
        try:
            df = pd.read_csv(self.input_file)
        except Exception as e:
            print(f"[Error] Cannot read input file: {e}")
            return []

        target_col = "Citing_Author_IDs"
        if target_col not in df.columns:
            print(f"[Error] Column {target_col} not found")
            return []

        id_list: set[str] = set()
        for row in df[target_col].dropna():
            entries = str(row).split(";")
            for entry in entries:
                entry = entry.strip()
                if ":" in entry:
                    parts = entry.split(":")
                    sid = parts[-1].strip()
                    if sid and sid != "WAITING_FOR_ID" and sid != "NO_GS_ID":
                        id_list.add(sid)

        print(f"[Info] Found {len(id_list)} unique valid Scholar IDs")
        return list(id_list)

    def _get_processed_ids(self) -> set[str]:
        """Get already processed IDs from output file for resumption."""
        if not os.path.exists(self.output_file):
            return set()

        try:
            df = pd.read_csv(self.output_file)
            if "Scholar_ID" in df.columns:
                return set(df["Scholar_ID"].astype(str).tolist())
        except Exception:
            pass
        return set()

    def _infer_fellow(self, affiliation_text: str) -> tuple[str, str]:
        """Infer Fellow status from affiliation text."""
        if not affiliation_text:
            return "No", ""

        # Normalize text: lower case and replace slashes with spaces for "IEEE/AAAS" cases
        text = affiliation_text.lower().replace("/", " ")

        # Exclude common false positives for "Fellow"
        # "Research Fellow", "Postdoctoral Fellow", "Visiting Fellow" should not trigger "Fellow"
        exclusions = [
            "research fellow",
            "postdoctoral fellow",
            "post-doctoral fellow",
            "visiting fellow",
            "teaching fellow",
        ]
        for exc in exclusions:
            text = text.replace(exc, "")

        for kw in self.fellow_keywords:
            # Handle the case where the keyword might match part of a word (e.g. "Fellow" in "Fellowship")
            # But simple inclusion is usually fine given the exclusions above.
            if kw.lower() in text:
                return "Yes", kw
        return "No", ""

    def _fetch_info(self, scholar_id: str) -> Optional[dict[str, Any]]:
        """Fetch information for a single scholar."""
        try:
            author = scholarly.search_author_id(scholar_id)

            name = author.get("name", "")
            aff = author.get("affiliation", "")
            is_fellow, fellow_title = self._infer_fellow(f"{name} {aff}")

            return {
                "Scholar_ID": scholar_id,
                "Name": name,
                "Total_Citations": author.get("citedby", 0),
                "Affiliation": aff,
                "Is_Fellow": is_fellow,
                "Inferred_Title": fellow_title,
                "Scrape_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception as e:
            print(f" [Error] Failed to fetch {scholar_id}: {e}", flush=True)
            return None

    def _process_single_author(self, sid: str) -> Optional[dict[str, Any]]:
        """Process a single author with rate limiting."""
        result = self._fetch_info(sid)

        sleep_sec = random.uniform(1.5, 2.5)
        time.sleep(sleep_sec)

        return result

    def run(self, max_workers: int = 16) -> None:
        """
        Run the author info fetching process.

        Args:
            max_workers: Number of parallel workers for fetching.
        """
        self._setup_proxy()

        all_ids = self._get_all_ids_from_source()

        processed_ids = self._get_processed_ids()
        todo_ids = [x for x in all_ids if x not in processed_ids]
        total_tasks = len(todo_ids)

        print(f"[Info] Completed: {len(processed_ids)}, Remaining: {total_tasks}")

        if not todo_ids:
            print("All tasks completed!")
            return

        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file) if os.path.dirname(self.output_file) else ".", exist_ok=True)

        file_exists = os.path.exists(self.output_file)

        with open(self.output_file, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)

            if not file_exists:
                writer.writeheader()

            print(f"[Info] Starting parallel fetch with {max_workers} workers")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_sid = {
                    executor.submit(self._process_single_author, sid): sid
                    for sid in todo_ids
                }

                completed_count = 0
                for future in as_completed(future_to_sid):
                    sid = future_to_sid[future]
                    completed_count += 1
                    try:
                        data = future.result()
                        if data:
                            writer.writerow(data)
                            f.flush()
                            print(
                                f"[{completed_count}/{total_tasks}] Success | "
                                f"ID: {sid} | Citations: {data['Total_Citations']} | {data['Name']}"
                            )
                        else:
                            print(f"[{completed_count}/{total_tasks}] Failed | ID: {sid} (no data)")

                    except Exception as exc:
                        print(f"[{completed_count}/{total_tasks}] Exception | ID: {sid} | Error: {exc}")

        print("\n[Done] All tasks completed.")
