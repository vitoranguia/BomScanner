"""Sync NVD feeds: download, extract and save JSON feeds.

Behavior: downloads 'modified', 'recent' and yearly feeds.
"""
from __future__ import annotations

import gzip
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import urllib.request
import ssl
import time
import urllib.error

BASE_URL = "https://nvd.nist.gov/feeds/json/cve/2.0"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def download(url: str, dest: Path, skip_if_same_size: bool = True, retries: int = 4) -> None:
    """Download `url` to `dest` with retries, backoff and User-Agent header.

    Uses only the v2.0 feed URLs as configured by `BASE_URL`.
    """
    headers = {"User-Agent": "bomscanner-sync/1.0 (+https://github.com/your/repo)"}
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()

    backoff = 1.0
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
                status = getattr(resp, 'status', None)
                if status and status >= 400:
                    raise urllib.error.HTTPError(url, status, f"HTTP {status}", resp.headers, None)

                remote_len = resp.getheader("Content-Length")
                if skip_if_same_size and remote_len is not None and dest.exists():
                    try:
                        local_size = dest.stat().st_size
                        if int(remote_len) == local_size:
                            print(f"Skipping download (same size): {dest}")
                            return
                    except Exception:
                        pass
                with open(dest, "wb") as out_f:
                    out_f.write(resp.read())
                return
        except ssl.SSLError as e:
            # SSL errors may be transient; log and retry with backoff
            print(f"SSL error on attempt {attempt}/{retries}: {e}")
        except urllib.error.HTTPError as he:
            # For 404, no need to retry; for 403 or 5xx, retry
            if he.code == 404:
                raise
            if 400 <= he.code < 500 and he.code != 403:
                # client error, don't retry
                raise
            print(f"HTTP error on attempt {attempt}/{retries}: {he}")
        except Exception as e:
            print(f"Network error on attempt {attempt}/{retries}: {e}")

        if attempt < retries:
            time.sleep(backoff)
            backoff *= 2

    # Last-resort: try once with unverified SSL context to help diagnose
    try:
        print("Final attempt with unverified SSL context (for diagnosis only)")
        with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=60) as resp:
            with open(dest, "wb") as out_f:
                out_f.write(resp.read())
            return
    except Exception as e:
        raise


def extract_gz(gz_path: Path, dest_json: Path) -> None:
    with gzip.open(gz_path, "rb") as f_in, open(dest_json, "wb") as f_out:
        f_out.write(f_in.read())


def sync_modified(out_dir: Path) -> None:
    ensure_dir(out_dir)
    fname = "nvdcve-2.0-modified.json.gz"
    url = f"{BASE_URL}/{fname}"
    gz_path = out_dir / fname
    json_path = out_dir / "nvdcve-2.0-modified.json"
    print("Downloading 'modified' feed...")
    download(url, gz_path)
    print("Extracting...")
    extract_gz(gz_path, json_path)
    print(f"Saved: {json_path}")


def sync_recent(out_dir: Path) -> None:
    ensure_dir(out_dir)
    fname = "nvdcve-2.0-recent.json.gz"
    url = f"{BASE_URL}/{fname}"
    gz_path = out_dir / fname
    json_path = out_dir / "nvdcve-2.0-recent.json"
    print("Downloading 'recent' feed...")
    download(url, gz_path)
    print("Extracting...")
    extract_gz(gz_path, json_path)
    print(f"Saved: {json_path}")


def sync_year(out_dir: Path, year: int) -> None:
    ensure_dir(out_dir)
    fname = f"nvdcve-2.0-{year}.json.gz"
    url = f"{BASE_URL}/{fname}"
    gz_path = out_dir / fname
    json_path = out_dir / f"nvdcve-2.0-{year}.json"
    print(f"Downloading feed for year {year}...")
    download(url, gz_path)
    print("Extracting...")
    extract_gz(gz_path, json_path)
    print(f"Saved: {json_path}")


def year_range_desc(start: int, end: int) -> Iterable[int]:
    for y in range(start, end - 1, -1):
        yield y


def main() -> int:
    out_dir = Path('data')
    ensure_dir(out_dir)

    try:
        sync_modified(out_dir)
    except Exception as e:
        print(f"Error syncing 'modified': {e}", file=sys.stderr)

    try:
        sync_recent(out_dir)
    except Exception as e:
        print(f"Error syncing 'recent': {e}", file=sys.stderr)

    current_year = datetime.now(timezone.utc).year
    for y in year_range_desc(current_year, 2002):
        try:
            sync_year(out_dir, y)
        except urllib.error.HTTPError as he:
            if he.code == 404:
                print(f"Feed not found for year {y}, skipping")
            else:
                print(f"HTTPError for {y}: {he}", file=sys.stderr)
        except Exception as e:
            print(f"Error for year {y}: {e}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
