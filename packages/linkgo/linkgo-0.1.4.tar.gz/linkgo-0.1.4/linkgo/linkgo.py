#!/usr/bin/env python3
import asyncio
import argparse
import sys
import time
import readline
import random
from ddgs import DDGS
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def print_gradient_banner():
    """Prints a banner with a random color gradient."""
    banner_text = [
        r" /$$ /$$           /$$                          ",
        r"| $$|__/          | $$                          ",
        r"| $$ /$$ /$$$$$$$ | $$   /$$  /$$$$$$   /$$$$$$ ",
        r"| $$| $$| $$__  $$| $$  /$$/ /$$__  $$ /$$__  $$",
        r"| $$| $$| $$  \ $$| $$$$$$/ | $$  \ $$| $$  \ $$",
        r"| $$| $$| $$  | $$| $$_  $$ | $$  | $$| $$  | $$",
        r"| $$| $$| $$  | $$| $$ \  $$|  $$$$$$$|  $$$$$$/",
        r"|__/|__/|__/  |__/|__/  \__/ \____  $$ \______/ ",
        r"                             /$$  \ $$          ",
        r"                            |  $$$$$$/          ",
        r"                             \______/           "
    ]

    start_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    end_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    lines = banner_text
    num_lines = len(lines)

    for i, line in enumerate(lines):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / (num_lines - 1))
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / (num_lines - 1))
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / (num_lines - 1))
        print(f"\033[38;2;{r};{g};{b}m{line}\033[0m")
    print()  # Add a newline for spacing
    github_link = "   < https://github.com/ghostescript/linkgo >"
    print(f"\033[91m{github_link}\033[0m")
    print() # Add another newline for spacing after the link

async def fetch(session, url):
    """Asynchronously fetch a single URL."""
    headers = {"Accept-Encoding": "gzip, deflate"} # Explicitly request gzip and deflate
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                return await response.text()
            return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def parse_links(html, base_url):
    """Parse HTML and extract all links."""
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        # Join relative URLs with the base URL
        full_link = urljoin(base_url, link)
        # Optional: filter out links that are just fragments
        if urlparse(full_link).scheme in ['http', 'https']:
            links.add(full_link)
    return links

async def run_link_finder(query, output):
    """The core logic of the link finder."""
    print(f"Searching for '{query}'...")
    try:
        with DDGS(timeout=20) as ddgs:
            # Hardcode max_results for a comprehensive scan
            raw_search_results = ddgs.text(query, max_results=200)
            search_results = [r['href'] for r in raw_search_results if r and r.get('href') and isinstance(raw_search_results, list)]
    except Exception as e:
        print(f"An error occurred during search: {e}")
        return

    print(f"Fetching and parsing links...")

    start_time = time.time()
    all_links = set()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in search_results]
        html_contents = await asyncio.gather(*tasks)

        for i, html in enumerate(html_contents):
            if html:
                base_url = search_results[i]
                links = await parse_links(html, base_url)
                all_links.update(links)
    end_time = time.time()
    elapsed_time = end_time - start_time

    if output:
        with open(output, 'w') as f:
            for link in sorted(all_links):
                f.write(link + '\n')
        print(f"\n\033[1;36mLinks saved to {output}")
    else:
        for link in sorted(all_links):
            print(link)

    print(f"\n\033[1;32mExtracted {len(all_links)} unique links in {elapsed_time:.2f} seconds for \"{query}\".\033[0m")


async def main():
    """Main function to run the link finder."""
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Find all links for multiple search queries.")
        parser.add_argument("query", nargs='+', help="The search query (can be multiple words separated by spaces).")
        parser.add_argument("-o", "--output", help="Output file to save the links.")
        args = parser.parse_args()
        query = " ".join(args.query)
        await run_link_finder(query, args.output)
    else:
        print() # Blank line before the banner
        print_gradient_banner()
        print("Entering interactive mode...")
        query = input("Enter the search query (separated by spaces for multiple): ")
        while not query:
            print("Search query cannot be empty.")
            query = input("Enter the search query (separated by spaces for multiple): ")

        output = input("Enter the output file to save links (or press Enter to print to console): ")
        if not output:
            output = None

        await run_link_finder(query, output)

def cli_main():
    """Wrapper function to run the async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\033[1;31m[ABORTED]\033[0m")

if __name__ == "__main__":
    cli_main()
