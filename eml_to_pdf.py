#!/opt/homebrew/bin/python3
"""
EML to PDF Converter
Converts .eml email files to PDF format.
"""
from __future__ import annotations

import argparse
import email
import email.policy
import os
import sys
import time
from email.utils import parsedate_to_datetime
from multiprocessing import Pool
from pathlib import Path


def parse_eml(eml_path: Path) -> email.message.EmailMessage:
    """Parse an EML file and return the email message object."""
    with open(eml_path, "rb") as f:
        return email.message_from_binary_file(f, policy=email.policy.default)


def extract_body(msg: email.message.EmailMessage) -> tuple[str, bool]:
    """
    Extract the email body content.
    Returns (content, is_html). Prefers HTML over plain text.
    """
    html_body = None
    text_body = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition:
                continue

            if content_type == "text/html" and html_body is None:
                html_body = _decode_part(part)
            elif content_type == "text/plain" and text_body is None:
                text_body = _decode_part(part)
    else:
        content_type = msg.get_content_type()
        body = _decode_part(msg)
        if content_type == "text/html":
            html_body = body
        else:
            text_body = body

    if html_body:
        return html_body, True
    return text_body or "", False


def _decode_part(part: email.message.Message) -> str:
    """Safely decode a message part to a string."""
    try:
        return part.get_content()
    except Exception:
        raw = part.get_payload(decode=True)
        charset = part.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace") if raw else ""


def get_attachments(msg: email.message.EmailMessage) -> list[str]:
    """Return a list of attachment filenames."""
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                filename = part.get_filename()
                if filename:
                    attachments.append(filename)
    return attachments


def format_date(date_str: str) -> str:
    """Format an email date string into a human-readable format."""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%A, %d %B %Y at %I:%M %p %Z")
    except Exception:
        return date_str


def escape_html(text: str) -> str:
    """Escape special HTML characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def build_html(msg: email.message.EmailMessage) -> str:
    """Construct a complete HTML document from the email message."""
    subject = msg.get("Subject", "(No Subject)")
    from_addr = msg.get("From", "")
    to_addr = msg.get("To", "")
    cc_addr = msg.get("CC", "") or msg.get("Cc", "")
    date_str = format_date(msg.get("Date", ""))

    body, is_html = extract_body(msg)
    attachments = get_attachments(msg)

    # Build header rows
    header_fields = [("From", from_addr), ("To", to_addr)]
    if cc_addr:
        header_fields.append(("CC", cc_addr))
    header_fields.append(("Date", date_str))

    header_rows = "".join(
        f'<tr><td class="lbl">{label}</td><td class="val">{escape_html(value)}</td></tr>'
        for label, value in header_fields
        if value
    )

    # Build attachments section
    attachments_html = ""
    if attachments:
        items = "".join(f"<li>{escape_html(a)}</li>" for a in attachments)
        attachments_html = f"""
        <div class="attachments">
            <span class="att-label">Attachments:</span>
            <ul>{items}</ul>
        </div>"""

    # Build body content
    body_content = (
        f'<div class="body">{body}</div>'
        if is_html
        else f'<div class="body plain">{escape_html(body)}</div>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{escape_html(subject)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: Arial, Helvetica, sans-serif;
            font-size: 11pt;
            color: #1a1a1a;
            background: #fff;
            padding: 24px;
        }}
        .email-container {{
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            overflow: hidden;
        }}
        .header-block {{
            background: #f7f7f7;
            border-bottom: 2px solid #d0d0d0;
            padding: 20px 24px;
        }}
        .subject {{
            font-size: 15pt;
            font-weight: bold;
            color: #111;
            margin-bottom: 14px;
            word-break: break-word;
        }}
        table.meta {{ border-collapse: collapse; width: 100%; }}
        td.lbl {{
            font-weight: bold;
            color: #666;
            width: 55px;
            padding: 2px 10px 2px 0;
            vertical-align: top;
            white-space: nowrap;
            font-size: 9.5pt;
        }}
        td.val {{
            color: #333;
            padding: 2px 0;
            font-size: 9.5pt;
            word-break: break-all;
        }}
        .attachments {{
            background: #fffbf0;
            border-bottom: 1px solid #e8e0c8;
            padding: 10px 24px;
            font-size: 9.5pt;
            color: #555;
        }}
        .att-label {{ font-weight: bold; }}
        .attachments ul {{ margin-top: 4px; padding-left: 20px; }}
        .attachments li {{ margin: 2px 0; }}
        .body {{
            padding: 24px;
            line-height: 1.6;
        }}
        .body.plain {{
            font-family: "Courier New", Courier, monospace;
            font-size: 10pt;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .body img {{ max-width: 100%; height: auto; }}
        a {{ color: #1a6fae; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header-block">
            <div class="subject">{escape_html(subject)}</div>
            <table class="meta">{header_rows}</table>
        </div>
        {attachments_html}
        {body_content}
    </div>
</body>
</html>"""


def _ensure_weasyprint():
    """Import weasyprint or exit with a helpful message."""
    try:
        import weasyprint
        return weasyprint
    except ImportError:
        print(
            "Error: weasyprint is not installed.\n"
            "Install it with:\n"
            "  brew install pango gobject-introspection\n"
            "  /opt/homebrew/bin/python3 -m pip install weasyprint --break-system-packages\n"
            "\nNote: on macOS, run the script with /opt/homebrew/bin/python3 to avoid SIP library issues."
        )
        sys.exit(1)


def convert(eml_path: Path, output_path: Path | None = None) -> Path:
    """
    Convert a single EML file to PDF.
    Returns the path to the generated PDF.
    """
    weasyprint = _ensure_weasyprint()

    if not eml_path.exists():
        raise FileNotFoundError(f"File not found: {eml_path}")

    if output_path is None:
        output_path = eml_path.with_suffix(".pdf")

    msg = parse_eml(eml_path)
    html = build_html(msg)

    weasyprint.HTML(string=html, base_url=str(eml_path.parent)).write_pdf(
        str(output_path)
    )
    return output_path


def _batch_worker(args: tuple[str, str]) -> tuple[str, str, str | None]:
    """
    Worker function for multiprocessing in batch mode.
    Accepts and returns plain strings so the arguments are picklable.
    Returns (eml_name, pdf_name, error | None).
    """
    eml_str, out_str = args
    eml_path = Path(eml_str)
    try:
        convert(eml_path, Path(out_str))
        return (eml_path.name, Path(out_str).name, None)
    except Exception as exc:
        return (eml_path.name, "", str(exc))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert .eml email files to PDF format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python eml_to_pdf.py email.eml\n"
            "  python eml_to_pdf.py email.eml -o output.pdf\n"
            "  python eml_to_pdf.py --batch ./emails/\n"
        ),
    )
    parser.add_argument("input", nargs="?", help="Path to an EML file")
    parser.add_argument(
        "-o", "--output", help="Output PDF path (default: same name as input)"
    )
    parser.add_argument(
        "-b", "--batch", metavar="DIR", help="Convert all .eml files in a directory"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print each conversion result"
    )
    args = parser.parse_args()

    if args.batch:
        batch_dir = Path(args.batch)
        if not batch_dir.is_dir():
            print(f"Error: '{args.batch}' is not a directory.")
            sys.exit(1)

        eml_files = sorted(batch_dir.glob("*.eml"))
        if not eml_files:
            print(f"No .eml files found in '{args.batch}'.")
            sys.exit(0)

        workers = min(len(eml_files), os.cpu_count() or 4)
        print(
            f"Converting {len(eml_files)} EML file(s) in '{batch_dir}' "
            f"using {workers} parallel workers..."
        )

        start = time.perf_counter()
        success = 0

        # Build (input, output) string pairs for the pool
        jobs = [(str(f), str(f.with_suffix(".pdf"))) for f in eml_files]

        with Pool(processes=workers) as pool:
            for eml_name, pdf_name, error in pool.imap_unordered(_batch_worker, jobs):
                if error:
                    print(f"  FAIL  {eml_name}: {error}")
                else:
                    success += 1
                    if args.verbose:
                        print(f"  OK  {eml_name}  ->  {pdf_name}")

        elapsed = time.perf_counter() - start
        print(f"\nDone: {success}/{len(eml_files)} converted successfully in {elapsed:.1f}s.")

    elif args.input:
        eml_path = Path(args.input)
        out_path = Path(args.output) if args.output else None
        try:
            out = convert(eml_path, out_path)
            print(f"Converted: {eml_path}  ->  {out}")
        except FileNotFoundError as exc:
            print(f"Error: {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"Conversion failed: {exc}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
