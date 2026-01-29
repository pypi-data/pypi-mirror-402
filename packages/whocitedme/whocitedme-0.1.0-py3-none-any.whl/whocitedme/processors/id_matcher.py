"""ID matcher for WhoCitedMe.

This module provides the IDMatcher class for matching WAITING_FOR_ID
placeholders to actual Scholar IDs using fuzzy name matching.
"""

import difflib
import os
from typing import Optional, Tuple

import pandas as pd


class IDMatcher:
    """
    Matcher for resolving WAITING_FOR_ID placeholders to actual Scholar IDs.

    This class uses fuzzy string matching to associate author names that lack
    Scholar IDs with their most likely matches from the scholar database.

    Example:
        >>> matcher = IDMatcher(
        ...     citing_file="citations_enriched.csv",
        ...     scholar_file="scholar_database.csv",
        ...     output_file="citations_verified.csv",
        ... )
        >>> matcher.run()
    """

    def __init__(
        self,
        citing_file: str = "output/citations_enriched.csv",
        scholar_file: str = "output/scholar_database.csv",
        output_file: str = "output/citations_verified.csv",
        match_threshold: float = 0.7,
    ):
        """
        Initialize the IDMatcher.

        Args:
            citing_file: Path to input CSV with citation data.
            scholar_file: Path to scholar database CSV.
            output_file: Path to output CSV for verified data.
            match_threshold: Fuzzy matching similarity threshold (0-1).
        """
        self.citing_file = citing_file
        self.scholar_file = scholar_file
        self.output_file = output_file
        self.match_threshold = match_threshold

    def _load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load citation and scholar data from CSV files."""
        if not os.path.exists(self.citing_file) or not os.path.exists(self.scholar_file):
            raise FileNotFoundError("Input files not found. Please check the paths.")

        df_cite = pd.read_csv(self.citing_file)
        df_scholar = pd.read_csv(self.scholar_file)
        return df_cite, df_scholar

    def _prepare_scholar_lookup(
        self, df_scholar: pd.DataFrame
    ) -> Tuple[dict[str, str], list[str]]:
        """
        Prepare scholar data for efficient lookups.

        Processes scholar database to:
        1. Ensure citation counts are numeric
        2. Sort by citations descending (prefer high-citation matches for duplicates)
        3. Create name -> ID mapping
        """
        df_scholar["Total_Citations"] = pd.to_numeric(
            df_scholar["Total_Citations"], errors="coerce"
        ).fillna(0)

        df_scholar = df_scholar.sort_values(by="Total_Citations", ascending=False)

        df_scholar_unique = df_scholar.dropna(subset=["Name"]).drop_duplicates(
            subset=["Name"], keep="first"
        )

        scholar_map = dict(zip(df_scholar_unique["Name"], df_scholar_unique["Scholar_ID"]))
        scholar_names_list = df_scholar_unique["Name"].tolist()

        return scholar_map, scholar_names_list

    def _get_fuzzy_match(
        self,
        name: str,
        scholar_names_list: list[str],
        scholar_map: dict[str, str],
    ) -> Optional[str]:
        """Find the best fuzzy match for a name in the scholar database."""
        matches = difflib.get_close_matches(
            name, scholar_names_list, n=1, cutoff=self.match_threshold
        )
        if matches:
            matched_name = matches[0]
            return scholar_map.get(matched_name)
        return None

    def _process_author_row(
        self,
        author_ids_str: str,
        scholar_names_list: list[str],
        scholar_map: dict[str, str],
    ) -> str:
        """
        Process a single Citing_Author_IDs string.

        Format: "Name1:ID1; Name2:WAITING_FOR_ID"
        """
        if pd.isna(author_ids_str):
            return author_ids_str

        entries = [e.strip() for e in author_ids_str.split(";") if e.strip()]
        new_entries = []

        for entry in entries:
            if ":" not in entry:
                new_entries.append(entry)
                continue

            name_part, id_part = entry.rsplit(":", 1)
            name = name_part.strip()
            current_id = id_part.strip()

            if current_id == "WAITING_FOR_ID":
                matched_id = self._get_fuzzy_match(name, scholar_names_list, scholar_map)
                if matched_id:
                    new_entries.append(f"{name}:{matched_id}")
                else:
                    new_entries.append(f"{name}:WAITING_FOR_ID")
            else:
                new_entries.append(entry)

        return "; ".join(new_entries)

    def _add_manual_review_flag(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Manual_Review_Required column.

        Flags rows that need manual review:
        1. Still have WAITING_FOR_ID
        2. Authors are truncated AND title doesn't contain [CITATION]
        """
        df["Is_Authors_Truncated"] = (
            df["Is_Authors_Truncated"].astype(str).str.upper() == "TRUE"
        )

        has_waiting_id = df["Citing_Author_IDs"].astype(str).str.contains(
            "WAITING_FOR_ID", na=False
        )

        title_not_citation = ~df["Citing_Title"].astype(str).str.contains(
            "[CITATION]", regex=False, na=False
        )
        is_truncated = df["Is_Authors_Truncated"]

        condition_truncated_review = is_truncated & title_not_citation

        df["Manual_Review_Required"] = has_waiting_id | condition_truncated_review

        return df

    def run(self) -> None:
        """Run the ID matching process."""
        print(">>> Starting ID matching process...")

        try:
            df_cite, df_scholar = self._load_data()
        except Exception as e:
            print(f"Error: {e}")
            return

        print(">>> Building Scholar index (priority matching by citation count)...")
        scholar_map, scholar_names_list = self._prepare_scholar_lookup(df_scholar)

        print(">>> Performing fuzzy ID matching...")
        if "Citing_Author_IDs" in df_cite.columns:
            df_cite["Citing_Author_IDs"] = df_cite["Citing_Author_IDs"].apply(
                lambda x: self._process_author_row(x, scholar_names_list, scholar_map)
            )
        else:
            print("Warning: 'Citing_Author_IDs' column not found in input file")

        print(">>> Generating Manual_Review_Required flags...")
        df_cite = self._add_manual_review_flag(df_cite)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file) if os.path.dirname(self.output_file) else ".", exist_ok=True)
        df_cite.to_csv(self.output_file, index=False, encoding="utf-8-sig")

        review_count = df_cite["Manual_Review_Required"].sum()
        print(f"\n>>> Processing complete!")
        print(f"    Output file: {self.output_file}")
        print(f"    Rows requiring manual review: {review_count}")
