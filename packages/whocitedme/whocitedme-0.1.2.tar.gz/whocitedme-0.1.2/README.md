# WhoCitedMe

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**WhoCitedMe** is a powerful Python library and CLI tool designed for researchers and academics. It automates the process of scraping Google Scholar citations, identifying who is citing your work, and analyzing the impact of those citations.

It goes beyond simple citation counts by enriching author data, matching missing Scholar IDs, and identifying the "top scholar" (highest-cited author) for each citing paper.

## 🚀 Key Features

*   **📄 Citing Papers Scraper**: Automatically scrape all papers citing a specific Google Scholar profile within a given year range.
*   **🧩 Author Enricher**: Handles truncated author lists (e.g., "J Smith, A Doe...") by parsing full citation data.
*   **📊 Author Info Fetcher**: High-performance, parallelized fetching of author metrics (Citation Count, h-index, Fellow status).
*   **🆔 ID Matcher**: Uses fuzzy matching logic to resolve missing Google Scholar IDs for citing authors.
*   **🏆 Top Scholar Finder**: Identifies the most influential author on every citing paper to help you understand *who* is citing you.

## 🎯 Use Cases

*   **Grant Applications**: Demonstrate impact by listing high-profile researchers who cite your work.
*   **Tenure & Promotion**: Provide detailed metrics on the quality of your citations, not just the quantity.
*   **Networking**: Identify potential collaborators who are already building on your research.

## 🛠️ Installation

### Prerequisites
*   **Python 3.8** or higher.
*   **Google Chrome** installed (required for Selenium scraping).

### 📦 From PyPI (Recommended)

```bash
pip install whocitedme
```

### 💻 Local Development (using uv)

We use [uv](https://github.com/astral-sh/uv) for fast dependency management.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/KyanChen/WhoCitedMe.git
    cd WhoCitedMe
    ```

2.  **Setup environment with uv:**
    ```bash
    # Install uv (if not installed)
    pip install uv

    # Create virtual environment
    uv venv

    # Activate virtual environment
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install in editable mode:**
    ```bash
    uv pip install -e .
    ```

## 📖 Usage

You can use **WhoCitedMe** either via the command line interface (CLI) or as a Python library.

### Command Line Interface (CLI)

The easiest way to run the tool is using the `pipeline` command, which runs all steps in order.

```bash
# Run the full analysis pipeline
whocitedme pipeline --user-id "YOUR_SCHOLAR_ID" --start-year 2018 --end-year 2024

# With custom output directory and worker count
whocitedme pipeline -u "YOUR_SCHOLAR_ID" -s 2018 -e 2024 -o my_output --workers 32

# Run in headless mode with proxy support
whocitedme pipeline -u "YOUR_SCHOLAR_ID" -s 2018 -e 2024 --headless --proxy http://127.0.0.1:7890
```

#### Individual Steps

If you prefer to run steps individually:

1.  **Scrape Citing Papers**:
    ```bash
    whocitedme scrape --user-id "YOUR_SCHOLAR_ID" --start-year 2020 --end-year 2024 --output output/citations.csv
    
    # Run in headless mode (no visible browser window)
    whocitedme scrape -u "YOUR_SCHOLAR_ID" -s 2020 -e 2024 --headless
    ```

2.  **Enrich Author Data**:
    ```bash
    whocitedme enrich --input output/citations.csv --output output/citations_enriched.csv
    
    # Start fresh (disable resume from previous run)
    whocitedme enrich -i output/citations.csv -o output/citations_enriched.csv --no-resume
    ```

3.  **Fetch Author Metrics** (Parallelized):
    ```bash
    whocitedme fetch-authors --input output/citations_enriched.csv --output output/scholar_database.csv --workers 16
    
    # With proxy support
    whocitedme fetch-authors -i output/citations_enriched.csv --proxy http://127.0.0.1:7890
    ```

4.  **Match Missing IDs**:
    ```bash
    whocitedme match-ids --citing output/citations_enriched.csv --scholars output/scholar_database.csv --output output/citations_verified.csv
    
    # With custom matching threshold (0-1, default: 0.7)
    whocitedme match-ids -c output/citations_enriched.csv -s output/scholar_database.csv --threshold 0.8
    ```

5.  **Find Top Scholars**:
    ```bash
    whocitedme top-scholar --input output/citations_verified.csv --scholars output/scholar_database.csv --output output/citations_final.csv
    ```

### Python API

For custom workflows, import the classes directly:

```python
from whocitedme import (
    CitingPapersScraper,
    AuthorEnricher,
    AuthorInfoFetcher,
    IDMatcher,
    TopScholarProcessor,
)

# Step 1: Scrape citing papers
scraper = CitingPapersScraper(
    user_id="YOUR_SCHOLAR_ID",
    start_year=2020,
    end_year=2024,
    output_file="output/citations.csv",
    headless=False,  # Set True for headless browser
)
scraper.run()
scraper.close()

# Step 2: Enrich truncated author information
enricher = AuthorEnricher(
    input_file="output/citations.csv",
    output_file="output/citations_enriched.csv",
)
enricher.run(resume=True)  # Resume from previous run if interrupted
enricher.close()

# Step 3: Fetch author metrics (parallelized)
fetcher = AuthorInfoFetcher(
    input_file="output/citations_enriched.csv",
    output_file="output/scholar_database.csv",
)
fetcher.run(max_workers=16)

# Step 4: Match missing Scholar IDs
matcher = IDMatcher(
    citing_file="output/citations_enriched.csv",
    scholar_file="output/scholar_database.csv",
    output_file="output/citations_verified.csv",
    match_threshold=0.7,
)
matcher.run()

# Step 5: Find top scholars for each citation
processor = TopScholarProcessor(
    main_file="output/citations_verified.csv",
    scholar_file="output/scholar_database.csv",
    output_file="output/citations_final.csv",
)
processor.run()
```

See [`examples/basic_usage.py`](examples/basic_usage.py) for a complete runnable script.

## 📂 Project Structure

```text
WhoCitedMe/
├── whocitedme/
│   ├── __init__.py         # Package exports
│   ├── cli.py              # Command-line entry point
│   ├── scrapers/           # Web scrapers using Selenium
│   │   ├── citing_papers.py    # CitingPapersScraper
│   │   ├── author_enricher.py  # AuthorEnricher
│   │   └── author_info.py      # AuthorInfoFetcher
│   ├── processors/         # Data processing logic
│   │   ├── id_matcher.py       # IDMatcher
│   │   └── top_scholar.py      # TopScholarProcessor
│   └── utils/              # Helper utilities
│       ├── browser.py          # Browser driver creation
│       └── captcha.py          # CAPTCHA handling & random sleep
├── examples/               # Usage examples
│   └── basic_usage.py
├── output/                 # Default output directory (git-ignored)
├── pyproject.toml          # Project configuration and dependencies
├── LICENSE                 # MIT License
└── README.md               # This file
```

## ⚠️ Troubleshooting & Limits

*   **Google Scholar Rate Limits**: If you scrape too fast, Google will block your IP.
    *   *Solution*: The tool has built-in delays, but for massive jobs, consider using a VPN or proxy.
*   **CAPTCHA**: If the scraper gets stuck, check the opened Chrome window. You may need to manually solve a CAPTCHA.
*   **Chrome Version**: Ensure your installed Chrome browser matches the ChromeDriver version (usually handled automatically by `undetected-chromedriver`).

## 🤝 Contributing

Contributions are welcome!
1.  Fork the repo.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes.
4.  Push to the branch.
5.  Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
