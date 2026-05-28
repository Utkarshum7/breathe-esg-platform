"""
utility_parser.py

Parses utility electricity portal CSV exports.

WHY this is non-trivial:
  Utility portals emit billing rows, not meter readings.  A single row
  represents energy consumed over a date range (billing period), not at a
  point in time.  Some portals use kWh, others MWh.  Date formats vary
  by country.  The portal may include its own CO2e estimate — we must
  ignore it and compute our own from the authoritative grid emission factor.
"""
import csv
from datetime import datetime
from .base_parser import BaseParser, ParsedRow

UTILITY_HEADER_MAP: dict[str, str] = {
    "account number": "account_number",
    "account_number": "account_number",
    "account no": "account_number",
    "meter mpan": "meter_mpan",
    "meter_mpan": "meter_mpan",
    "mpan": "meter_mpan",
    "supply point": "meter_mpan",
    "site name": "site_name",
    "site_name": "site_name",
    "site": "site_name",
    "billing period start": "period_start",
    "billing_period_start": "period_start",
    "period start": "period_start",
    "start date": "period_start",
    "billing period end": "period_end",
    "billing_period_end": "period_end",
    "period end": "period_end",
    "end date": "period_end",
    # Energy columns — one of the two must be present
    "kwh consumed": "kwh_consumed",
    "kwh_consumed": "kwh_consumed",
    "consumption (kwh)": "kwh_consumed",
    "kwh": "kwh_consumed",
    "mwh consumed": "mwh_consumed",
    "mwh_consumed": "mwh_consumed",
    "consumption (mwh)": "mwh_consumed",
    "mwh": "mwh_consumed",
    # Optional informational columns
    "demand (kw)": "demand_kw",
    "demand_kw": "demand_kw",
    "tariff": "tariff",
    "rate": "tariff",
    "total cost (gbp)": "cost_gbp",
    "total cost": "cost_gbp",
    "cost": "cost_gbp",
    # Ignore utility CO2e estimates — never use them
    "co2e estimate (kg)": "_ignored_co2e",
    "co2e": "_ignored_co2e",
}

REQUIRED_CANONICAL_FIELDS: set[str] = {"period_start", "period_end"}
ENERGY_FIELDS: set[str] = {"kwh_consumed", "mwh_consumed"}


class UtilityElectricityParser(BaseParser):
    """
    Parses utility electricity portal CSV exports.

    Handles:
    - kWh and MWh columns (prefers kWh if both present)
    - DD/MM/YYYY and YYYY-MM-DD date formats
    - Comma-delimited (standard for utility portals)
    - Missing meter MPAN (stored as suspicious in validator)
    - UTF-8 BOM
    """

    source_type = "UTILITY_ELECTRICITY"

    def parse(self, file_path: str) -> tuple[list[ParsedRow], list[dict]]:
        rows: list[ParsedRow] = []
        parse_errors: list[dict] = []

        with open(file_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)

            for row_index, raw_row in enumerate(reader, start=1):
                if all(v is None or (v or "").strip() == "" for v in raw_row.values()):
                    continue

                canonical = {
                    UTILITY_HEADER_MAP.get(k.strip().lower(), k.strip().lower()): (v or "").strip()
                    for k, v in raw_row.items()
                    if k is not None
                }

                # Verify required date fields
                missing = REQUIRED_CANONICAL_FIELDS - canonical.keys()
                if missing:
                    parse_errors.append({
                        "row_index": row_index,
                        "raw_data": dict(raw_row),
                        "error": f"Missing required columns: {sorted(missing)}",
                    })
                    continue

                # Verify at least one energy column exists
                if not ENERGY_FIELDS.intersection(canonical.keys()):
                    parse_errors.append({
                        "row_index": row_index,
                        "raw_data": dict(raw_row),
                        "error": "No energy consumption column found (expected 'kWh Consumed' or 'MWh Consumed').",
                    })
                    continue

                quantity, unit = self._resolve_energy(canonical)
                period_start = self._parse_date(canonical.get("period_start", ""))
                period_end = self._parse_date(canonical.get("period_end", ""))

                rows.append(ParsedRow(
                    row_index=row_index,
                    source_type=self.source_type,
                    raw_data=dict(raw_row),
                    quantity=quantity,
                    unit=unit,
                    date=period_start,
                    site_reference=(
                        canonical.get("meter_mpan") or canonical.get("site_name") or None
                    ),
                    material_or_mode="ELECTRICITY",
                    extra={
                        "account_number": canonical.get("account_number"),
                        "period_start": period_start,
                        "period_end": period_end,
                        "site_name": canonical.get("site_name"),
                        "tariff": canonical.get("tariff"),
                        "cost_gbp": canonical.get("cost_gbp"),
                        "demand_kw": canonical.get("demand_kw"),
                    },
                ))

        return rows, parse_errors

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_energy(canonical: dict) -> tuple[float | None, str | None]:
        """Prefer kWh column over MWh; return (value, unit_string)."""
        for field, unit in (("kwh_consumed", "kWh"), ("mwh_consumed", "MWh")):
            raw = canonical.get(field, "").replace(",", "").strip()
            if raw:
                try:
                    return float(raw), unit
                except ValueError:
                    continue
        return None, None

    @staticmethod
    def _parse_date(date_str: str) -> str | None:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt).date().isoformat()
            except ValueError:
                continue
        return None
