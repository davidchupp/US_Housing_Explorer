"""Load and clean raw home-sales CSV files into a consistent schema.

Public sales data (county assessor exports, open-data portals) uses many
different column names and formats. This module maps them onto one schema,
coerces types, and drops rows that cannot be trusted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Canonical column -> accepted aliases (compared case-insensitively).
COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "sale_id": ("sale_id", "id", "parcel_id", "apn"),
    "sale_price": ("sale_price", "price", "saleprice", "sale_amount"),
    "sale_date": ("sale_date", "date", "saledate", "closing_date"),
    "sqft": ("sqft", "living_area", "square_feet", "building_sqft"),
    "bedrooms": ("bedrooms", "beds", "bed"),
    "bathrooms": ("bathrooms", "baths", "bath"),
    "latitude": ("latitude", "lat", "y"),
    "longitude": ("longitude", "lon", "lng", "long", "x"),
    "zip_code": ("zip_code", "zip", "zipcode", "postal_code"),
}

REQUIRED_COLUMNS = ("sale_price", "sale_date", "latitude", "longitude")

# Sanity bounds; rows outside these are almost always data-entry errors.
MIN_PRICE = 10_000
MAX_PRICE = 50_000_000
MIN_SQFT = 200
MAX_SQFT = 30_000
US_LAT_RANGE = (18.0, 72.0)  # includes Hawaii and Alaska
US_LON_RANGE = (-180.0, -65.0)


class SchemaError(ValueError):
    """Raised when a file is missing columns the pipeline cannot work without."""


@dataclass
class CleaningReport:
    """How many rows were read, kept, and dropped (with reasons)."""

    rows_in: int = 0
    rows_out: int = 0
    dropped: dict[str, int] = field(default_factory=dict)

    def record(self, reason: str, count: int) -> None:
        if count:
            self.dropped[reason] = self.dropped.get(reason, 0) + count


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename known aliases to canonical names and drop unknown columns."""
    lookup = {
        alias.lower(): canonical
        for canonical, aliases in COLUMN_ALIASES.items()
        for alias in aliases
    }
    renamed: dict[str, str] = {}
    for col in df.columns:
        key = re.sub(r"[\s\-]+", "_", str(col).strip().lower())
        canonical = lookup.get(key)
        if canonical and canonical not in renamed.values():
            renamed[col] = canonical
    out = df.rename(columns=renamed)[list(renamed.values())]

    missing = [c for c in REQUIRED_COLUMNS if c not in out.columns]
    if missing:
        raise SchemaError(f"missing required columns: {', '.join(missing)}")
    return out


def _to_number(series: pd.Series) -> pd.Series:
    """Parse numbers like '$415,000' or ' 1,850 ' into floats; bad values -> NaN."""
    cleaned = series.astype("string").str.replace(r"[$,\s]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def clean_sales(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """Normalize, type-coerce and filter a raw sales table.

    Returns the cleaned frame and a report explaining every dropped row.
    """
    report = CleaningReport(rows_in=len(raw))
    df = normalize_columns(raw).copy()

    for col in ("sale_price", "sqft", "bedrooms", "bathrooms", "latitude", "longitude"):
        if col in df.columns:
            df[col] = _to_number(df[col])
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    if "zip_code" in df.columns:
        # Keep leading zeros (e.g. 02139) and strip ZIP+4 suffixes.
        df["zip_code"] = (
            df["zip_code"].astype("string").str.strip().str.extract(r"^(\d{5})", expand=False)
        )

    def drop(mask: pd.Series, reason: str) -> None:
        nonlocal df
        mask = mask.fillna(False)
        report.record(reason, int(mask.sum()))
        df = df[~mask]

    drop(df[list(REQUIRED_COLUMNS)].isna().any(axis=1), "missing_required_value")
    drop(~df["sale_price"].between(MIN_PRICE, MAX_PRICE), "price_out_of_range")
    drop(
        ~df["latitude"].between(*US_LAT_RANGE) | ~df["longitude"].between(*US_LON_RANGE),
        "coordinates_outside_us",
    )
    if "sqft" in df.columns:
        drop(
            df["sqft"].notna() & ~df["sqft"].between(MIN_SQFT, MAX_SQFT),
            "sqft_out_of_range",
        )

    before = len(df)
    dedupe_on = ["sale_id"] if "sale_id" in df.columns else ["sale_price", "sale_date",
                                                               "latitude", "longitude"]
    df = df.drop_duplicates(subset=dedupe_on, keep="last")
    report.record("duplicate", before - len(df))

    if "sqft" in df.columns:
        df["price_per_sqft"] = (df["sale_price"] / df["sqft"]).round(2)

    df = df.sort_values("sale_date").reset_index(drop=True)
    report.rows_out = len(df)
    return df, report


def load_sales(path: str | Path) -> tuple[pd.DataFrame, CleaningReport]:
    """Read a sales CSV from disk and clean it."""
    raw = pd.read_csv(path, dtype=str)
    return clean_sales(raw)
