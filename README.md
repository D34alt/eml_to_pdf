# EML to PDF Converter

Converts `.eml` email files to PDF. Preserves email headers, HTML body content, and lists any attachments.

## Requirements

- macOS with Homebrew
- Python 3 (via Homebrew)

## Setup

```bash
brew install pango gobject-introspection
/opt/homebrew/bin/python3 -m pip install weasyprint --break-system-packages
```

## Usage

Single file:
```bash
python3 eml_to_pdf.py email.eml
python3 eml_to_pdf.py email.eml -o output.pdf
```

Batch convert a directory:
```bash
python3 eml_to_pdf.py --batch ./emails/
python3 eml_to_pdf.py --batch ./emails/ --verbose
```

## Notes

- On macOS, use `/opt/homebrew/bin/python3` rather than `/usr/bin/python3`. The system Python is SIP-protected and cannot load Homebrew libraries.
- HTML email bodies are rendered as-is. Plain text bodies are rendered in monospace.
- Attachments are listed in the PDF but not embedded.
