# Inbound Source Data Lineage & Reality Guide (`SOURCES.md`)

This document outlines the formats, fields, real-world constraints, and parsing limitations modeled for the three inbound ESG data streams: SAP Fuel, Utility Electricity, and Corporate Travel.

---

## 1. SAP Fuel ERP Export (CSV)

### Researched Format & Realism
In enterprise environments, SAP ERP systems (such as SAP S/4HANA or SAP ECC) export material postings as semicolon-delimited CSV logs. Our sample uses German headers representing standard SAP column structures:
- `Werk` (Site Reference / Plant)
- `Buchungsdatum` (Posting Date / Booking Date)
- `Material` / `Materialkurztext` (Material ID and Short Text, e.g. Diesel or Natural Gas)
- `Menge` (Quantity, formatted using European decimals: e.g. `1.200,50`)
- `Einheit` (Unit, e.g. `L` for Liters or `M3` for Cubic Meters)
- `Nettopreis` (Net Price)

### Model Realism
- **European Number Parsing**: Real-world SAP exports from European operations use comma decimal separators and dot thousands separators. The `SAPFuelParser` parses these formats automatically, converting them into standard floats.
- **Header Aliases**: Real SAP exports may use either German (`Menge`) or English (`Quantity`) column configurations. The parser includes a lookup mapping to support both configurations.

### Ingest Limitations
- The parser expects a clean, semicolon-separated grid. It does not support nested tables or extra text descriptions at the top of the CSV file.

---

## 2. Utility Electricity Portal Export (CSV)

### Researched Format & Realism
Standard energy portal exports (e.g. from Npower, E.ON, or British Gas) export monthly billing periods as standard comma-separated values (CSV):
- `Account Number`
- `Meter MPAN` (Meter Point Administration Number)
- `Site Name`
- `Billing Period Start` / `Billing Period End`
- `kWh Consumed` / `MWh Consumed`
- `Total Cost (GBP)`

### Model Realism
- **Unit Scaling**: Invoices scale consumption based on site sizes (larger plants use MWh, standard offices use kWh). The `UtilityElectricityParser` normalizes both scales automatically to a standard kWh baseline.
- **Date Range Mapping**: Tracks billing periods to prevent data overlaps or double-counting during auditing.

### Ingest Limitations
- If both `kWh Consumed` and `MWh Consumed` are empty on a row, the row fails validation.

---

## 3. Corporate Travel JSON Feed (TMC)

### Researched Format & Realism
Travel Management Companies (TMCs) stream travel records via REST API Webhooks or JSON exports:
- `trip_id`
- `travel_mode` (`FLIGHT` or `RAIL`)
- `origin` / `destination` (e.g. `LHR` to `JFK` airport sectors)
- `distance_km`
- `travel_date`
- `employee_id`
- `class` (DEFRA seating class: `ECONOMY`, `BUSINESS`, etc.)

### Model Realism
- **Haversine Distance Estimation**: If `distance_km` is null, the `TravelParser` references IATA airport codes, pulls coordinates from an embedded dictionary, and automatically estimates flight distances in kilometers using the **Haversine formula**.
- **DEFRA Seating Multipliers**: Applies standard carbon multipliers based on seating classes (e.g. Business class receives a $2.9\times$ multiplier due to the larger space footprint occupied per passenger).

### Ingest Limitations
- The Haversine distance estimator currently supports 20 major global airport codes. If an unmapped airport code is supplied, the row will fail validation unless a manual `distance_km` parameter is provided.
