# linkgo

`linkgo` is a Python-based command-line tool designed to discover and extract links from web pages. It leverages DuckDuckGo Search to find initial URLs based on a query, then delves into those pages to gather all outbound links.

## Features

- **DuckDuckGo Search Integration**: Utilizes DDGS to find relevant starting URLs for your queries.
- **Comprehensive Link Extraction**: Fetches web pages and parses their HTML content to extract all discoverable links.
- **Command-Line Interface**: Supports direct queries and output file specification via command-line arguments.
- **Interactive Mode**: Offers a user-friendly interactive prompt for dynamic searches.
- **Colorful Output**: Features an aesthetic gradient banner and colorized messages for better readability.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ghostescript/linkgo
    cd linkgo
    ```

2.  **Create and activate a virtual environment:**
    It's recommended to install dependencies in a virtual environment to avoid conflicts with system-wide packages.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Interactive Mode

Simply run the script without any arguments:
```bash
python3 linkgo.py
```
The tool will then prompt you to enter your search query and an optional output file.

### Command-Line Mode

Provide your search query directly. You can also specify an output file using the `-o` or `--output` flag.

**Example: Search for "python programming" and print results to console**
```bash
python3 linkgo.py "python programming"
```

**Example: Search for "web scraping tutorials" and save results to a file**
```bash
python3 linkgo.py "web scraping tutorials" -o scraped_links.txt
```

---

< https://github.com/ghostescript/linkgo >
