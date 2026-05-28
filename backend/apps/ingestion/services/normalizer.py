"""
normalizer.py

Converts ParsedRow quantities to standardised base units.

WHY deterministic unit conversion here (not in the parser):
  Parsers should return raw values as they appeared in the source.
  Normalisation is a business rule that can change (e.g., if the company
  switches from liters to GJ as the Scope 1 base unit).  Keeping it here
  means one file changes, not three parsers.

Base units chosen:
  SAP fuel        →  Liters (L)           — standard in EU fuel reporting
  Utility elec.   →  kWh                  — international standard
  Travel          →  km (class-adjusted)  — DEFRA flight class multipliers applied

Flight class multipliers follow DEFRA/GHG Protocol methodology:
  Economy        : 1.0×
  Premium Economy: 1.6×
  Business       : 2.9×
  First          : 4.0×

These multiply the physical distance to produce a "radiative forcing adjusted"
distance that reflects the higher per-seat GHG impact of premium seats.
"""
from decimal import Decimal, ROUND_HALF_UP
from .base_parser import ParsedRow

# ---------------------------------------------------------------------------
# SAP: unit → Liters conversion factors
# ---------------------------------------------------------------------------
SAP_TO_LITERS: dict[str, Decimal] = {
    "L":      Decimal("1"),
    "LTR":    Decimal("1"),
    "M3":     Decimal("1000"),          # 1 m³ = 1,000 L
    "KG":     Decimal("1.163"),         # diesel density average
    "T":      Decimal("1163"),          # 1 metric tonne diesel → L
    "GAL":    Decimal("3.785411784"),   # US gallon
    "MMBTU":  Decimal("28.317"),        # 1 MMBtu natural gas ≈ 28.317 m³ → L
    "GJ":     Decimal("26.137"),        # 1 GJ nat. gas ≈ 26.137 m³ → L
    "MJ":     Decimal("0.026137"),      # 1 MJ = 0.001 GJ
}

# ---------------------------------------------------------------------------
# Utility: unit → kWh conversion factors
# ---------------------------------------------------------------------------
UTILITY_TO_KWH: dict[str, Decimal] = {
    "kWh": Decimal("1"),
    "KWH": Decimal("1"),
    "MWh": Decimal("1000"),
    "MWH": Decimal("1000"),
}

# ---------------------------------------------------------------------------
# Travel: DEFRA flight class multipliers (applied to km distance)
# ---------------------------------------------------------------------------
FLIGHT_CLASS_MULTIPLIERS: dict[str, Decimal] = {
    "ECONOMY":         Decimal("1.0"),
    "ECONOMY CLASS":   Decimal("1.0"),
    "PREMIUM ECONOMY": Decimal("1.6"),
    "PREMIUM":         Decimal("1.6"),
    "BUSINESS":        Decimal("2.9"),
    "BUSINESS CLASS":  Decimal("2.9"),
    "FIRST":           Decimal("4.0"),
    "FIRST CLASS":     Decimal("4.0"),
}

DECIMAL_PRECISION = Decimal("0.000001")


class NormalizationResult:
    """
    Result from NormalizationService.normalize().

    value         : Normalised Decimal value in base unit.  None on failure.
    unit          : Base unit string (e.g. "L", "kWh", "km").
    scope_category: EmissionRecord.ScopeCategory value.
    error         : Human-readable error message when normalisation failed.
    """

    __slots__ = ("value", "unit", "scope_category", "error")

    def __init__(
        self,
        value: Decimal | None,
        unit: str | None,
        scope_category: str | None,
        error: str | None = None,
    ) -> None:
        self.value = value
        self.unit = unit
        self.scope_category = scope_category
        self.error = error

    @property
    def is_success(self) -> bool:
        return self.value is not None and self.error is None


class NormalizationService:
    """
    Converts ParsedRow quantities into base units.

    Stateless — create once, call repeatedly.
    All arithmetic uses Python's Decimal to avoid float rounding errors
    in financial/regulatory data.
    """

    def normalize(self, row: ParsedRow) -> NormalizationResult:
        if row.source_type == "SAP_FUEL":
            return self._normalize_sap(row)
        if row.source_type == "UTILITY_ELECTRICITY":
            return self._normalize_utility(row)
        if row.source_type == "CORP_TRAVEL":
            return self._normalize_travel(row)
        return NormalizationResult(
            None, None, None,
            f"Unknown source type '{row.source_type}' — no normalisation rule defined.",
        )

    # ------------------------------------------------------------------
    # Source-specific normalisation logic
    # ------------------------------------------------------------------

    def _normalize_sap(self, row: ParsedRow) -> NormalizationResult:
        if row.quantity is None:
            return NormalizationResult(None, None, "SCOPE_1", "Quantity is None — cannot normalise.")

        unit_key = (row.unit or "").upper().strip()
        factor = SAP_TO_LITERS.get(unit_key)
        if factor is None:
            return NormalizationResult(
                None, None, "SCOPE_1",
                f"No conversion factor found for SAP unit '{row.unit}'. "
                f"Supported: {sorted(SAP_TO_LITERS.keys())}",
            )

        value = (Decimal(str(row.quantity)) * factor).quantize(
            DECIMAL_PRECISION, rounding=ROUND_HALF_UP
        )
        return NormalizationResult(value, "L", "SCOPE_1")

    def _normalize_utility(self, row: ParsedRow) -> NormalizationResult:
        if row.quantity is None:
            return NormalizationResult(None, None, "SCOPE_2", "Quantity is None — cannot normalise.")

        # Accept both capitalisation variants from the parser
        unit_key = (row.unit or "").strip()
        factor = UTILITY_TO_KWH.get(unit_key) or UTILITY_TO_KWH.get(unit_key.upper())
        if factor is None:
            return NormalizationResult(
                None, None, "SCOPE_2",
                f"No conversion factor found for utility unit '{row.unit}'. "
                f"Supported: {sorted(UTILITY_TO_KWH.keys())}",
            )

        value = (Decimal(str(row.quantity)) * factor).quantize(
            DECIMAL_PRECISION, rounding=ROUND_HALF_UP
        )
        return NormalizationResult(value, "kWh", "SCOPE_2")

    def _normalize_travel(self, row: ParsedRow) -> NormalizationResult:
        if row.quantity is None:
            return NormalizationResult(None, None, "SCOPE_3", "Distance is None — cannot normalise.")

        distance = Decimal(str(row.quantity))

        # Apply DEFRA flight class multiplier when applicable
        travel_mode = (row.material_or_mode or "").upper()
        if travel_mode == "FLIGHT":
            travel_class = str(row.extra.get("travel_class") or "ECONOMY").upper().strip()
            multiplier = FLIGHT_CLASS_MULTIPLIERS.get(travel_class, Decimal("1.0"))
            distance = distance * multiplier

        value = distance.quantize(DECIMAL_PRECISION, rounding=ROUND_HALF_UP)
        return NormalizationResult(value, "km", "SCOPE_3")
