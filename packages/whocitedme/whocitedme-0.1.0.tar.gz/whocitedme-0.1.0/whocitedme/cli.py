"""Command-line interface for WhoCitedMe.

This module provides CLI commands for running the various WhoCitedMe
scraping and processing pipelines.
"""

import argparse
import sys
from typing import Optional


def cmd_scrape(args: argparse.Namespace) -> int:
    """Run the citing papers scraper."""
    from whocitedme.scrapers.citing_papers import CitingPapersScraper

    print(f"Scraping citations for user: {args.user_id}")
    print(f"Year range: {args.start_year} - {args.end_year}")
    print(f"Output file: {args.output}")

    scraper = CitingPapersScraper(
        user_id=args.user_id,
        start_year=args.start_year,
        end_year=args.end_year,
        output_file=args.output,
        headless=args.headless,
    )

    try:
        scraper.run()
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        scraper.close()
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        scraper.close()
        return 1


def cmd_enrich(args: argparse.Namespace) -> int:
    """Run the author enricher."""
    from whocitedme.scrapers.author_enricher import AuthorEnricher

    print(f"Enriching authors from: {args.input}")
    print(f"Output file: {args.output}")

    enricher = AuthorEnricher(
        input_file=args.input,
        output_file=args.output,
        headless=args.headless,
    )

    try:
        enricher.run(resume=not args.no_resume)
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        enricher.close()
        return 1


def cmd_fetch_authors(args: argparse.Namespace) -> int:
    """Run the author info fetcher."""
    from whocitedme.scrapers.author_info import AuthorInfoFetcher

    print(f"Fetching author info from: {args.input}")
    print(f"Output file: {args.output}")
    print(f"Workers: {args.workers}")

    fetcher = AuthorInfoFetcher(
        input_file=args.input,
        output_file=args.output,
        use_proxy=args.proxy is not None,
        proxy_address=args.proxy or "",
    )

    fetcher.run(max_workers=args.workers)
    return 0


def cmd_match_ids(args: argparse.Namespace) -> int:
    """Run the ID matcher."""
    from whocitedme.processors.id_matcher import IDMatcher

    print(f"Matching IDs...")
    print(f"Citing file: {args.citing}")
    print(f"Scholar file: {args.scholars}")
    print(f"Output file: {args.output}")

    matcher = IDMatcher(
        citing_file=args.citing,
        scholar_file=args.scholars,
        output_file=args.output,
        match_threshold=args.threshold,
    )

    matcher.run()
    return 0


def cmd_top_scholar(args: argparse.Namespace) -> int:
    """Run the top scholar processor."""
    from whocitedme.processors.top_scholar import TopScholarProcessor

    print(f"Finding top scholars...")
    print(f"Input file: {args.input}")
    print(f"Scholar file: {args.scholars}")
    print(f"Output file: {args.output}")

    processor = TopScholarProcessor(
        main_file=args.input,
        scholar_file=args.scholars,
        output_file=args.output,
    )

    processor.run()
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    """Run the full pipeline."""
    import os

    from whocitedme.processors.id_matcher import IDMatcher
    from whocitedme.processors.top_scholar import TopScholarProcessor
    from whocitedme.scrapers.author_enricher import AuthorEnricher
    from whocitedme.scrapers.author_info import AuthorInfoFetcher
    from whocitedme.scrapers.citing_papers import CitingPapersScraper

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Define file paths
    citations_file = os.path.join(output_dir, "citations.csv")
    enriched_file = os.path.join(output_dir, "citations_enriched.csv")
    scholars_file = os.path.join(output_dir, "scholar_database.csv")
    verified_file = os.path.join(output_dir, "citations_verified.csv")
    final_file = os.path.join(output_dir, "citations_final.csv")

    print("=" * 60)
    print("WhoCitedMe Full Pipeline")
    print("=" * 60)
    print(f"User ID: {args.user_id}")
    print(f"Year range: {args.start_year} - {args.end_year}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)

    # Step 1: Scrape citing papers
    print("\n[Step 1/5] Scraping citing papers...")
    scraper = CitingPapersScraper(
        user_id=args.user_id,
        start_year=args.start_year,
        end_year=args.end_year,
        output_file=citations_file,
        headless=args.headless,
    )
    try:
        scraper.run()
    except KeyboardInterrupt:
        print("Pipeline interrupted at Step 1.")
        return 1
    finally:
        scraper.close()

    # Step 2: Enrich truncated authors
    print("\n[Step 2/5] Enriching truncated authors...")
    enricher = AuthorEnricher(
        input_file=citations_file,
        output_file=enriched_file,
        headless=args.headless,
    )
    try:
        enricher.run()
    except KeyboardInterrupt:
        print("Pipeline interrupted at Step 2.")
        return 1
    finally:
        enricher.close()

    # Step 3: Fetch author info
    print("\n[Step 3/5] Fetching author information...")
    fetcher = AuthorInfoFetcher(
        input_file=enriched_file,
        output_file=scholars_file,
        use_proxy=args.proxy is not None,
        proxy_address=args.proxy or "",
    )
    fetcher.run(max_workers=args.workers)

    # Step 4: Match IDs
    print("\n[Step 4/5] Matching author IDs...")
    matcher = IDMatcher(
        citing_file=enriched_file,
        scholar_file=scholars_file,
        output_file=verified_file,
    )
    matcher.run()

    # Step 5: Find top scholars
    print("\n[Step 5/5] Finding top scholars...")
    processor = TopScholarProcessor(
        main_file=verified_file,
        scholar_file=scholars_file,
        output_file=final_file,
    )
    processor.run()

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print(f"Final output: {final_file}")

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="whocitedme",
        description="Google Scholar citation analysis tool for identifying high-impact citations.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser(
        "scrape",
        help="Scrape all citing papers for a Google Scholar author",
    )
    scrape_parser.add_argument(
        "--user-id", "-u",
        required=True,
        help="Google Scholar author ID",
    )
    scrape_parser.add_argument(
        "--start-year", "-s",
        type=int,
        required=True,
        help="Start year for citation filtering",
    )
    scrape_parser.add_argument(
        "--end-year", "-e",
        type=int,
        required=True,
        help="End year for citation filtering",
    )
    scrape_parser.add_argument(
        "--output", "-o",
        default="output/citations.csv",
        help="Output CSV file path",
    )
    scrape_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
    )
    scrape_parser.set_defaults(func=cmd_scrape)

    # Enrich command
    enrich_parser = subparsers.add_parser(
        "enrich",
        help="Enrich truncated author information",
    )
    enrich_parser.add_argument(
        "--input", "-i",
        default="output/citations.csv",
        help="Input CSV file path",
    )
    enrich_parser.add_argument(
        "--output", "-o",
        default="output/citations_enriched.csv",
        help="Output CSV file path",
    )
    enrich_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
    )
    enrich_parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh instead of resuming",
    )
    enrich_parser.set_defaults(func=cmd_enrich)

    # Fetch authors command
    fetch_parser = subparsers.add_parser(
        "fetch-authors",
        help="Fetch detailed author information from Google Scholar",
    )
    fetch_parser.add_argument(
        "--input", "-i",
        default="output/citations_enriched.csv",
        help="Input CSV file path",
    )
    fetch_parser.add_argument(
        "--output", "-o",
        default="output/scholar_database.csv",
        help="Output CSV file path",
    )
    fetch_parser.add_argument(
        "--workers", "-w",
        type=int,
        default=16,
        help="Number of parallel workers",
    )
    fetch_parser.add_argument(
        "--proxy", "-p",
        help="Proxy address (e.g., http://127.0.0.1:7890)",
    )
    fetch_parser.set_defaults(func=cmd_fetch_authors)

    # Match IDs command
    match_parser = subparsers.add_parser(
        "match-ids",
        help="Match WAITING_FOR_ID placeholders using fuzzy matching",
    )
    match_parser.add_argument(
        "--citing", "-c",
        default="output/citations_enriched.csv",
        help="Citing papers CSV file",
    )
    match_parser.add_argument(
        "--scholars", "-s",
        default="output/scholar_database.csv",
        help="Scholar database CSV file",
    )
    match_parser.add_argument(
        "--output", "-o",
        default="output/citations_verified.csv",
        help="Output CSV file path",
    )
    match_parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.7,
        help="Fuzzy matching threshold (0-1)",
    )
    match_parser.set_defaults(func=cmd_match_ids)

    # Top scholar command
    top_parser = subparsers.add_parser(
        "top-scholar",
        help="Find top (highest-cited) scholar for each citation",
    )
    top_parser.add_argument(
        "--input", "-i",
        default="output/citations_verified.csv",
        help="Input CSV file path",
    )
    top_parser.add_argument(
        "--scholars", "-s",
        default="output/scholar_database.csv",
        help="Scholar database CSV file",
    )
    top_parser.add_argument(
        "--output", "-o",
        default="output/citations_with_top_scholar.csv",
        help="Output CSV file path",
    )
    top_parser.set_defaults(func=cmd_top_scholar)

    # Pipeline command
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run the full pipeline from scraping to final analysis",
    )
    pipeline_parser.add_argument(
        "--user-id", "-u",
        required=True,
        help="Google Scholar author ID",
    )
    pipeline_parser.add_argument(
        "--start-year", "-s",
        type=int,
        required=True,
        help="Start year for citation filtering",
    )
    pipeline_parser.add_argument(
        "--end-year", "-e",
        type=int,
        required=True,
        help="End year for citation filtering",
    )
    pipeline_parser.add_argument(
        "--output-dir", "-o",
        default="output",
        help="Output directory for all files",
    )
    pipeline_parser.add_argument(
        "--workers", "-w",
        type=int,
        default=16,
        help="Number of parallel workers for author fetching",
    )
    pipeline_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
    )
    pipeline_parser.add_argument(
        "--proxy", "-p",
        help="Proxy address for author fetching (e.g., http://127.0.0.1:7890)",
    )
    pipeline_parser.set_defaults(func=cmd_pipeline)

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
