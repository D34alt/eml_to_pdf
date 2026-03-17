# EML to PDF Converter

Converts `.eml` email files to PDF. Preserves email headers, HTML body content, and lists any attachments.

Batch conversions use multiprocessing to run across all available CPU cores for significantly faster throughput.

## Requirements

- macOS with Homebrew
- Python 3 (via Homebrew)

## Setup

```bash
brew install pango gobject-introspection
/opt/homebrew/bin/python3 -m pip install weasyprint --break-system-packages
```

## Usage

### Single file

```bash
python3 eml_to_pdf.py email.eml
python3 eml_to_pdf.py email.eml -o output.pdf
```

### Batch convert a directory

Converts all `.eml` files in a directory in parallel:

```bash
python3 eml_to_pdf.py --batch ./emails/
python3 eml_to_pdf.py --batch ./emails/ --verbose
```

### Flight itinerary converter

Converts Jetstar flight itinerary `.eml` files from the `flights/` folder into dated subfolders under `flights_pdf/`:

```bash
python3 convert_flights.py
```

Output structure:

```
flights_pdf/
  2022-08-23/
    2022-08-23_CEWTXY_emailed-2022-08-04-2046.pdf
  2023-07-14/
    ...
```

## Notes

- On macOS, use `/opt/homebrew/bin/python3` rather than `/usr/bin/python3`. The system Python is SIP-protected and cannot load Homebrew libraries.
- Batch modes automatically use all available CPU cores via `multiprocessing.Pool`.
- HTML email bodies are rendered as-is. Plain text bodies are rendered in monospace.
- Attachments are listed in the PDF but not embedded.
