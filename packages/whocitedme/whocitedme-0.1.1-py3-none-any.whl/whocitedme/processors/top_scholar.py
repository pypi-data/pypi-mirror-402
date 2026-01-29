"""Top scholar processor for WhoCitedMe.

This module provides the TopScholarProcessor class for identifying
the highest-cited author among all citing authors for each citation.
"""

import os
from typing import Any, Optional

import pandas as pd


class TopScholarProcessor:
    """
    Processor for finding the top (highest-cited) scholar among citing authors.

    For each citation record, this class identifies the author with the highest
    citation count and adds their information to the output.

    Example:
        >>> processor = TopScholarProcessor(
        ...     main_file="citations_verified.csv",
        ...     scholar_file="scholar_database.csv",
        ...     output_file="citations_with_top_scholar.csv",
        ... )
        >>> processor.run()
    """

    def __init__(
        self,
        main_file: str = "output/citations_verified.csv",
        scholar_file: str = "output/scholar_database.csv",
        output_file: str = "output/citations_with_top_scholar.csv",
        top_venue_names: list[str] = ["Nature", "Cell", "Science"],
        exclude_venue_names: list[str] = ["sciencedirect", "springer", "elsevier", "neuroscience", "ieee", "koreascience", "mdpi"], 
    ):
        """
        Initialize the TopScholarProcessor.

        Args:
            main_file: Path to input CSV with citation data.
            scholar_file: Path to scholar database CSV.
            output_file: Path to output CSV with top scholar info.
        """
        self.main_file = main_file
        self.scholar_file = scholar_file
        self.output_file = output_file
        self.top_venue_names = [x.lower() for x in top_venue_names]
        self.exclude_venue_names = [x.lower() for x in exclude_venue_names]

    def _is_top_venue(self, link: Any, journal_conf: Any) -> str:
        link_str = str(link).lower() if pd.notna(link) else ""
        venue_str = str(journal_conf).strip() if pd.notna(journal_conf) else ""
        venue_lower = venue_str.lower()

        # Check excludes first
        if any(x in link_str for x in self.exclude_venue_names):
            return "No"
        if any(x in venue_lower for x in self.exclude_venue_names):
            return "No"

        for name in self.top_venue_names:
            # Check link (keep simple substring)
            if name in link_str:
                return "Yes"
            
            # Check venue name (stricter: exact match or starts with name followed by space)
            if venue_lower == name or venue_lower.startswith(f"{name} "):
                return "Yes"
        
        return "No"

    def run(self) -> None:
        """Run the top scholar extraction process."""
        print("Reading data...")

        try:
            df_main = pd.read_csv(self.main_file)
            df_db = pd.read_csv(self.scholar_file)
        except FileNotFoundError as e:
            print(f"Error: File not found - {e}")
            return

        # Preprocess scholar database
        df_db["Total_Citations"] = pd.to_numeric(
            df_db["Total_Citations"], errors="coerce"
        ).fillna(0)

        # Deduplicate by ID, keeping highest citation count
        df_db = df_db.sort_values("Total_Citations", ascending=False).drop_duplicates(
            "Scholar_ID"
        )

        # Create lookup dictionary: {ID: {'Name': ..., 'Total_Citations': ..., 'Affiliation': ...}}
        scholar_lookup = df_db.set_index("Scholar_ID")[
            ["Name", "Total_Citations", "Affiliation", "Is_Fellow", "Inferred_Title"]
        ].to_dict("index")

        print("Processing each row to find top scholar...")

        def find_top_scholar(author_ids_str: Any) -> pd.Series:
            """Find the scholar with highest citations among authors."""
            best_id = None
            best_name = None
            best_citations = -1
            best_affiliation = None
            best_is_fellow = None
            best_inferred_title = None

            if pd.isna(author_ids_str) or str(author_ids_str).strip() == "":
                return pd.Series([None, None, None, None, None, None])

            authors = str(author_ids_str).split(";")

            for author_entry in authors:
                parts = author_entry.strip().split(":")

                if len(parts) >= 2:
                    current_id = parts[-1].strip()

                    if current_id in ("NO_GS_ID", "WAITING_FOR_ID"):
                        continue

                    if current_id in scholar_lookup:
                        info = scholar_lookup[current_id]
                        citations = info["Total_Citations"]

                        if citations > best_citations:
                            best_citations = citations
                            best_id = current_id
                            best_name = info["Name"]
                            best_affiliation = info["Affiliation"]
                            best_is_fellow = info.get("Is_Fellow")
                            best_inferred_title = info.get("Inferred_Title")

            if best_citations == -1:
                return pd.Series([None, None, None, None, None, None])

            return pd.Series(
                [
                    best_id,
                    best_name,
                    best_citations,
                    best_affiliation,
                    best_is_fellow,
                    best_inferred_title,
                ]
            )

        new_cols = df_main["Citing_Author_IDs"].apply(find_top_scholar)
        new_cols.columns = [
            "Top_Scholar_ID",
            "Top_Scholar_Name",
            "Top_Scholar_Citations",
            "Top_Scholar_Affiliation",
            "Top_Scholar_Is_Fellow",
            "Top_Scholar_Inferred_Title",
        ]

        # Identify top venues
        print("Identifying top venues...")
        df_main["Is_Top_Venue"] = df_main.apply(
            lambda row: self._is_top_venue(row.get("Citing_Link"), row.get("Citing_Journal_Conf")),
            axis=1
        )

        df_final = pd.concat([df_main, new_cols], axis=1)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file) if os.path.dirname(self.output_file) else ".", exist_ok=True)

        print(f"Processing complete. Saving to {self.output_file}...")
        df_final.to_csv(self.output_file, index=False, encoding="utf-8-sig")
        print("Done!")
