# PDF repository

These are the full-text PDFs served directly by the academic homepage. The current library contains **116 files (~211 MB)**, exported from the Google Drive folder `Public research articles`.

## How links are produced

`../publications.json → full_pdf_library` holds one record per PDF (`title`, `file`, `year`, `year_source`). `python build.py` turns each `file` into a download link and percent-encodes the URL, so the original filenames — including spaces and Chinese characters — are preserved and still work in browsers.

To make a publication's **PDF** button point at one of these files, add `"local": "papers/....pdf"` to that entry in `publications.json`. Any existing `pdf` URL is kept as a secondary **Mirror** link.

## Adding a file

1. Copy the PDF into this folder (subfolders such as `2023/` are fine).
2. Add a record to `full_pdf_library` in `../publications.json`.
3. Run `python build.py` from the project root.

The naming convention `YYYY-NN.pdf` is recommended for new files, but not required — existing filenames were kept as-is so titles stay recognisable.

## Year grouping

The PDF Repository groups files by year only when the year is **confirmed** — from a matched publication record (`year_source: publication`) or a dated folder/prefix such as `papers/2024/` (`year_source: filename`). Everything else is placed in the final "Earlier works & undated full texts" group (`year_source: unconfirmed`). PDF creation dates from the file metadata are stored as `file_date` for reference but are **not** shown as publication years, because bulk export rewrote many of them.

## Notes

- GitHub repos have a 1 GB soft limit and a 100 MB per-file limit. The largest file here is ~17 MB.
- Only publish PDFs you are allowed to distribute (check publisher copyright or use the accepted-manuscript / open-access version).
- Pushing ~211 MB will take a few minutes on a slow connection.
