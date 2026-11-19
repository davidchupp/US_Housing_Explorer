"""Summary statistics over cleaned sales data."""

from __future__ import annotations

import pandas as pd


def summarize_by_zip(df: pd.DataFrame, min_sales: int = 3) -> pd.DataFrame:
    """Median price and price-per-sqft by ZIP code.

    ZIPs with fewer than ``min_sales`` sales are excluded, since medians from
    one or two sales are misleading.
    """
    if "zip_code" not in df.columns:
        raise ValueError("data has no zip_code column")

    agg: dict[str, tuple[str, str]] = {
        "sales": ("sale_price", "size"),
        "median_price": ("sale_price", "median"),
    }
    if "price_per_sqft" in df.columns:
        agg["median_price_per_sqft"] = ("price_per_sqft", "median")

    out = (
        df.dropna(subset=["zip_code"])
        .groupby("zip_code")
        .agg(**agg)
        .query("sales >= @min_sales")
        .sort_values("median_price", ascending=False)
    )
    return out.round(2)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Median sale price and sale count per calendar month."""
    monthly = df.set_index("sale_date")["sale_price"].resample("MS")
    return pd.DataFrame({"sales": monthly.size(), "median_price": monthly.median()}).dropna()
