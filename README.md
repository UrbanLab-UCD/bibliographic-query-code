# bibliographic-query-code

This repository contains Python scripts for querying scientific databases  and managing files to support bibliographic and systematic literature reviews.

## Structure

All source code is located in the `src/` directory. The available modules include:

- **`build_query.py`**: Helper functions to build search queries in the required format for different databases (Scopus, Web of Science, Google Scholar).
- **`scopus_query.py`**: Tools for querying Scopus using programmatic access.
- **`wos_query.py`**: Tools for querying Web of Science.
- **`scholar_search.py`**: Functions for searching articles in Google Scholar (limited by access restrictions).
- **`drive_conection.py`**: Functions to connect to Google Drive and list available files or directories (e.g., to access downloaded citation data).

## Purpose

These scripts aim to streamline the process of:

- Building standardized queries across platforms.
- Automating searches in multiple literature databases.
- Manage and review files stored in shared drives.

It is useful for anyone conducting systematic reviews, meta-analyses, or literature mapping.

## Requirements

- Python 3.8+
- `SerApi` (for Google Scholar)
- `pybliometrics` (for Scopus)
- `wos` (for WOS)
- `pydrive` or `gdrive` API access (for Drive connection)

Install requirements:

```bash
pip install -r requirements.txt

