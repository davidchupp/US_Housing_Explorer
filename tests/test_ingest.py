import pandas as pd
import pytest

from housing_explorer.ingest import SchemaError, clean_sales, load_sales, normalize_columns


def test_normalize_columns_maps_aliases_case_insensitively():
    raw = pd.DataFrame(
        {"PRICE": ["1"], "Closing_Date": ["2025-01-01"], "Lat": ["30"], "LNG": ["-97"],
         "unrelated": ["x"]}
    )
    out = normalize_columns(raw)
    assert list(out.columns) == ["sale_price", "sale_date", "latitude", "longitude"]


def test_normalize_columns_handles_spaces_and_hyphens():
    raw = pd.DataFrame(
        {"Sale Price": ["1"], "Sale-Date": ["2025-01-01"], "lat": ["30"], "lon": ["-97"]}
    )
    assert "sale_price" in normalize_columns(raw).columns


def test_normalize_columns_raises_on_missing_required():
    with pytest.raises(SchemaError, match="sale_date"):
        normalize_columns(pd.DataFrame({"price": [1], "lat": [1], "lon": [1]}))


def test_load_sample_drops_bad_rows_with_reasons(sample_path):
    df, report = load_sales(sample_path)

    assert report.rows_in == 14
    assert report.dropped == {
        "missing_required_value": 1,   # 1011 has no sale date
        "price_out_of_range": 1,       # 1007 sold for $1,250
        "coordinates_outside_us": 1,   # 1012 at (0, 0)
        "sqft_out_of_range": 1,        # 1013 has 90 sqft
        "duplicate": 1,                # 1009 appears twice
    }
    assert report.rows_out == len(df) == 9
    assert df["sale_date"].is_monotonic_increasing


def test_prices_and_zips_are_parsed(sample_path):
    df, _ = load_sales(sample_path)
    first = df.iloc[0]
    assert first["sale_price"] == 415_000
    assert first["price_per_sqft"] == pytest.approx(224.32)
    assert first["zip_code"] == "78701"


def test_zip_keeps_leading_zero_and_strips_plus_four():
    raw = pd.DataFrame(
        {"price": ["300000", "300000"], "date": ["2025-01-01", "2025-01-02"],
         "lat": ["42.36", "42.37"], "lon": ["-71.10", "-71.11"],
         "zip": ["02139", "02139-4307"]}
    )
    df, _ = clean_sales(raw)
    assert df["zip_code"].tolist() == ["02139", "02139"]
