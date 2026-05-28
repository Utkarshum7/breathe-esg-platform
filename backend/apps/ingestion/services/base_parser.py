"""
base_parser.py

Defines the contract every source-specific parser must satisfy.

WHY a base class:
  The ingestion service must be able to call parser.parse(path) on any
  source without knowing its internals. The Strategy Pattern + ABC forces
  each new parser to implement the same interface or fail at import time —
  a compile-time-style guardrail in Python.
"""
import abc
from dataclasses import dataclass, field


@dataclass
class ParsedRow:
    """
    Standardised intermediate row produced by every parser.

    All downstream services (validator, normalizer, ingestion_service) work
    exclusively against this structure — they never see raw CSV/JSON rows.
    This decouples parsers from the rest of the pipeline.

    Fields:
        row_index       : 1-indexed position in the source file.  Used for
                          lineage in EmissionRecord.row_index.
        source_type     : Matches DataSource.SourceType values.
        raw_data        : The verbatim original row (dict).  Stored in
                          EmissionRecord.raw_data_payload as source-of-truth.
        quantity        : The primary numeric value (fuel qty / kWh / distance).
                          None when parsing failed.
        unit            : Raw unit string as it appeared in the source.
        date            : ISO-8601 date string (YYYY-MM-DD) or None.
        site_reference  : Plant code / Meter MPAN / Employee ID — identifies
                          the physical or organisational source point.
        material_or_mode: Fuel material code (SAP) or travel mode (Travel).
        extra           : Source-specific fields that don't map to the common
                          schema — preserved for raw_data_payload completeness.
    """
    row_index: int
    source_type: str
    raw_data: dict
    quantity: float | None = None
    unit: str | None = None
    date: str | None = None          # ISO YYYY-MM-DD
    site_reference: str | None = None
    material_or_mode: str | None = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "row_index": self.row_index,
            "source_type": self.source_type,
            "raw_data": self.raw_data,
            "quantity": self.quantity,
            "unit": self.unit,
            "date": self.date,
            "site_reference": self.site_reference,
            "material_or_mode": self.material_or_mode,
            "extra": self.extra,
        }


class BaseParser(abc.ABC):
    """
    Abstract base class all parsers must subclass.

    Contract:
        parse(file_path) → (list[ParsedRow], list[parse_error_dicts])

    A parse_error_dict describes a row that could not be read at all
    (e.g., completely missing required columns, corrupt encoding).
    These rows are counted as failed_rows on the UploadBatch but are
    NOT stored as EmissionRecords — there's nothing safe to store.
    """

    # Must be set to a DataSource.SourceType value in each subclass.
    source_type: str = ""

    @abc.abstractmethod
    def parse(self, file_path: str) -> tuple[list[ParsedRow], list[dict]]:
        """
        Parse the source file at file_path.

        Returns:
            rows         : ParsedRow list — includes both clean and partially
                           broken rows.  The validator decides what to do with them.
            parse_errors : list of {row_index, raw_data, error} dicts for rows
                           that could not be represented as a ParsedRow at all.
        """
        ...
