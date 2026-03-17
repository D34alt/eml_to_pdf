#!/opt/homebrew/bin/python3
"""
Flight itinerary batch converter.

Converts all .eml files in the flights folder to PDF, organised into
subfolders named by flight departure date.

Output structure:
  flights_pdf/
    2022-08-23/
      2022-08-23_CEWTXY_emailed-2022-08-04.pdf
    2023-07-14/
      ...
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import weasyprint
except ImportError:
    print(
        "Error: weasyprint is not installed.\n"
        "Install it with:\n"
        "  brew install pango gobject-introspection\n"
        "  /opt/homebrew/bin/python3 -m pip install weasyprint --break-system-packages"
    )
    sys.exit(1)

# Import shared helpers from eml_to_pdf
sys.path.insert(0, str(Path(__file__).parent))
from eml_to_pdf import parse_eml, build_html

# Regex to parse the Jetstar filename format:
# Jetstar Flight Itinerary for (Booking ref# CEWTXY) JQ502 23_08_2022 ... - 2022-08-04 2046.eml
FILENAME_RE = re.compile(
    r"Booking ref# (\w+)\)"       # group 1: booking ref
    r".*?(\w+) (\d{2}_\d{2}_\d{4})"  # group 2: first flight number, group 3: first flight date (DD_MM_YYYY)
    r".*- (\d{4}-\d{2}-\d{2}) (\d{4})\.eml$"  # group 4: email date, group 5: email time
)


def parse_filename(filename: str) -> dict | None:
    """
    Extract booking ref, flight date, and email date from a Jetstar EML filename.
    Returns None if the filename does not match the expected pattern.
    """
    m = FILENAME_RE.search(filename)
    if not m:
        return None

    booking_ref, _flight_num, flight_date_raw, email_date, email_time = m.groups()

    # Convert flight date from DD_MM_YYYY to YYYY-MM-DD
    day, month, year = flight_date_raw.split("_")
    flight_date = f"{year}-{month}-{day}"

    return {
        "booking_ref": booking_ref,
        "flight_date": flight_date,       # e.g. 2022-08-23
        "email_date": email_date,         # e.g. 2022-08-04
        "email_time": email_time,         # e.g. 2046
    }


def make_pdf_name(info: dict) -> str:
    """Build a clean, date-identifiable PDF filename."""
    return (
        f"{info['flight_date']}"
        f"_{info['booking_ref']}"
        f"_emailed-{info['email_date']}-{info['email_time']}"
        ".pdf"
    )


def convert_file(eml_path: Path, output_path: Path) -> None:
    """Convert a single EML file to PDF at the given output path."""
    msg = parse_eml(eml_path)
    html = build_html(msg)
    weasyprint.HTML(string=html, base_url=str(eml_path.parent)).write_pdf(str(output_path))


def main() -> None:
    project_root = Path(__file__).parent
    flights_dir = project_root / "flights"
    output_root = project_root / "flights_pdf"

    if not flights_dir.is_dir():
        print(f"Error: '{flights_dir}' folder not found.")
        sys.exit(1)

    eml_files = sorted(flights_dir.glob("*.eml"))
    if not eml_files:
        print("No .eml files found in the flights folder.")
        sys.exit(0)

    print(f"Found {len(eml_files)} EML file(s). Converting...\n")

    success = 0
    skipped = 0

    for eml_file in eml_files:
        info = parse_filename(eml_file.name)

        if not info:
            print(f"  SKIP  {eml_file.name}  (filename did not match expected pattern)")
            skipped += 1
            continue

        # Create dated subfolder
        subfolder = output_root / info["flight_date"]
        subfolder.mkdir(parents=True, exist_ok=True)

        pdf_name = make_pdf_name(info)
        output_path = subfolder / pdf_name

        try:
            convert_file(eml_file, output_path)
            print(f"  OK    {info['flight_date']}/{pdf_name}")
            success += 1
        except Exception as exc:
            print(f"  FAIL  {eml_file.name}: {exc}")

    print(f"\nDone: {success} converted, {skipped} skipped.")
    if success:
        print(f"Output: {output_root}/")


if __name__ == "__main__":
    main()
