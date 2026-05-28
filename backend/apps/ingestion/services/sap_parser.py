"""
sap_parser.py

Parses SAP fuel & procurement CSV exports.

WHY this complexity:
  SAP GUI exports are notorious for inconsistency.  Customers run SAP in
  their local language, so German field names (Werk, Menge, Einheit) are
  common alongside English equivalents.  Semicolons are the default SAP
  delimiter.  Dates are DD.MM.YYYY.  Quantities use European formatting
  (1.000,50 means one thousand and a half).  None of this is negotiable —
  we handle it or the ingestion silently drops data.
"""
import csv
from datetime import datetime
from .base_parser import BaseParser, ParsedRow

# ---------------------------------------------------------------------------
# Header alias table: every known SAP header variant → internal canonical name
# Add new variants here when clients complain about "column not found" errors.
# ---------------------------------------------------------------------------
SAP_HEADER_MAP: dict[str, str] = {
    # German SAP GUI headers
    "werk": "plant_code",
    "buchungsdatum": "posting_date",
    "material": "material_code",
    "materialkurztext": "material_description",
    "menge": "quantity",
    "einheit": "unit",
    "nettopreis": "net_price",
    "basismengeneinheit": "unit",       # alternate German unit field
    # English SAP equivalents
    "plant": "plant_code",
    "plant code": "plant_code",
    "posting date": "posting_date",
    "posting_date": "posting_date",
    "material code": "material_code",
    "material_code": "material_code",
    "material description": "material_description",
    "quantity": "quantity",
    "unit": "unit",
    "base unit": "unit",
    "net price": "net_price",
}

# Columns that must be present (by canonical name) for a row to be parseable.
REQUIRED_CANONICAL_FIELDS: set[str] = {
    "plant_code",
    "posting_date",
    "quantity",
    "unit",
    "material_code",
}


class SAPFuelParser(BaseParser):
    """
    Parses SAP fuel/procurement CSV exports into standardised ParsedRow objects.

    Handles:
    - Semicolon OR comma delimiters (auto-detected)
    - German and English header names
    - DD.MM.YYYY and YYYY-MM-DD date formats
    - European number formatting (1.000,50)
    - UTF-8 BOM (common in SAP exports)
    """

    source_type = "SAP_FUEL"

    def parse(self, file_path: str) -> tuple[list[ParsedRow], list[dict]]:
        rows: list[ParsedRow] = []
        parse_errors: list[dict] = []

        with open(file_path, newline="", encoding="utf-8-sig") as fh:
            # Auto-detect delimiter from first 4 KB
            sample = fh.read(4096)
            fh.seek(0)
            delimiter = ";" if sample.count(";") >= sample.count(",") else ","

            reader = csv.DictReader(fh, delimiter=delimiter)

            for row_index, raw_row in enumerate(reader, start=1):
                if all(v is None or v.strip() == "" for v in raw_row.values()):
                    continue  # Skip blank rows silently

                # Normalise headers to canonical names
                canonical = {
                    SAP_HEADER_MAP.get(k.strip().lower(), k.strip().lower()): (v or "").strip()
                    for k, v in raw_row.items()
                    if k is not None
                }

                # Check required fields are present in header
                missing = REQUIRED_CANONICAL_FIELDS - canonical.keys()
                if missing:
                    parse_errors.append({
                        "row_index": row_index,
                        "raw_data": dict(raw_row),
                        "error": f"Missing required columns after header mapping: {sorted(missing)}",
                    })
                    continue

                quantity = self._parse_quantity(canonical.get("quantity", ""))
                date_str = self._parse_date(canonical.get("posting_date", ""))

                rows.append(ParsedRow(
                    row_index=row_index,
                    source_type=self.source_type,
                    raw_data=dict(raw_row),
                    quantity=quantity,
                    unit=(canonical.get("unit", "") or "").upper().strip(),
                    date=date_str,
                    site_reference=canonical.get("plant_code") or None,
                    material_or_mode=canonical.get("material_code") or None,
                    extra={
                        "material_description": canonical.get("material_description"),
                        "net_price": canonical.get("net_price"),
                    },
                ))

        return rows, parse_errors

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_date(date_str: str) -> str | None:
        """Try multiple format patterns; return ISO date string or None."""
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt).date().isoformat()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_quantity(qty_str: str) -> float | None:
        """
        Handle both European (1.000,50) and English (1000.50) number formats.
        """
        s = qty_str.strip()
        if not s:
            return None
        try:
            if "," in s and "." in s:
                if s.rindex(",") > s.rindex("."):
                    # European: 1.200,50 -> 1200.50
                    s = s.replace(".", "").replace(",", ".")
                else:
                    # English: 1,200.50 -> 1200.50
                    s = s.replace(",", "")
            elif "," in s:
                # Comma only. Check digits after comma.
                parts = s.split(",")
                if len(parts) == 2 and len(parts[1]) == 3:
                    # English thousands: 1,000 -> 1000
                    s = s.replace(",", "")
                else:
                    # European decimal: 500,00 -> 500.00
                    s = s.replace(",", ".")
            return float(s)
        except ValueError:
            return None
