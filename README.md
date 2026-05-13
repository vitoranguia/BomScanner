# BomScanner

Simple tool to sync and scan NVD (CVE) feeds and generate a BOM/report.

## Installation

It is recommended to create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

- Show help:

```bash
bomscanner help
```

- Sync NVD feeds:

```bash
bomscanner sync
```

- Run scanner against a `requirements.txt` or `pom.xml`:

```bash
bomscanner requirements.txt
bomscanner pom.xml
```

## Structure

- `bomscanner/` — main package with CLI and sync scripts.
- `data/` — where synced NVD feeds are stored.

## License

This project is licensed under the GNU General Public License v3 (GPL-3.0).
See the `COPYING` or `LICENSE` file for the full license text.
