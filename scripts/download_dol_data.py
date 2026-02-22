#!/usr/bin/env python3
"""
Download H1B disclosure data directly from the US Department of Labor.

Usage:
  python3 scripts/download_dol_data.py
  python3 scripts/download_dol_data.py --years 2023 2024
  python3 scripts/download_dol_data.py --output /custom/path/
"""

import argparse
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "downloads"

# Direct download URLs for H1B LCA disclosure data (updated annually)
# Source: https://www.dol.gov/agencies/eta/foreign-labor/performance
DOL_FILES = {
    2024: "https://www.dol.gov/sites/dolgov/files/ETA/oflc/pdfs/LCA_Disclosure_Data_FY2024_Q4.xlsx",
    2023: "https://www.dol.gov/sites/dolgov/files/ETA/oflc/pdfs/LCA_Disclosure_Data_FY2023_Q4.xlsx",
    2022: "https://www.dol.gov/sites/dolgov/files/ETA/oflc/pdfs/LCA_Disclosure_Data_FY2022_Q4.xlsx",
    2021: "https://www.dol.gov/sites/dolgov/files/ETA/oflc/pdfs/LCA_Disclosure_Data_FY2021_Q4.xlsx",
}


def download_file(url: str, dest: Path) -> bool:
    """Download a file with progress indicator."""
    if dest.exists():
        print(f"  Already downloaded: {dest.name}")
        return True

    print(f"  Downloading {dest.name}...")
    print(f"  URL: {url}")

    try:
        def progress(block_num, block_size, total_size):
            if total_size > 0:
                pct = min(100, block_num * block_size * 100 // total_size)
                bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
                print(f"\r  [{bar}] {pct}%", end="", flush=True)

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; H1BSalaryBot/1.0; +https://h1bsalary.info)"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 65536

            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = min(100, downloaded * 100 // total)
                        bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
                        mb = downloaded / 1_000_000
                        print(f"\r  [{bar}] {pct}% ({mb:.1f} MB)", end="", flush=True)

        print(f"\r  Done: {dest.name} ({dest.stat().st_size / 1_000_000:.1f} MB)")
        return True

    except urllib.error.HTTPError as e:
        print(f"\n  HTTP Error {e.code}: {e.reason}")
        print(f"  The URL may have changed. Check: https://www.dol.gov/agencies/eta/foreign-labor/performance")
        if dest.exists():
            dest.unlink()
        return False
    except Exception as e:
        print(f"\n  Error: {e}")
        if dest.exists():
            dest.unlink()
        return False


def main():
    parser = argparse.ArgumentParser(description="Download DOL H1B disclosure data")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2024, 2023],
        help="Fiscal years to download (default: 2024 2023)",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_DIR),
        help=f"Output directory (default: {OUTPUT_DIR})",
    )
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading H1B disclosure data → {out}")
    print(f"Years: {args.years}\n")

    successes = []
    failures = []

    for year in args.years:
        if year not in DOL_FILES:
            print(f"  Year {year} not available. Available: {list(DOL_FILES.keys())}")
            continue

        url = DOL_FILES[year]
        filename = f"H1B_LCA_FY{year}.xlsx"
        dest = out / filename

        ok = download_file(url, dest)
        if ok:
            successes.append(dest)
        else:
            failures.append(year)

    print(f"\n{'='*50}")
    print(f"Downloaded {len(successes)} file(s).")

    if failures:
        print(f"Failed: {failures}")
        print("Check the DOL website for updated URLs:")
        print("https://www.dol.gov/agencies/eta/foreign-labor/performance")

    if successes:
        print(f"\nNext step — process the data:")
        print(f"  python3 scripts/process_h1b_data.py --input {out}/ --output data/salaries.db")
        print(f"Then rebuild the site:")
        print(f"  npm run build")

    print()


if __name__ == "__main__":
    main()
