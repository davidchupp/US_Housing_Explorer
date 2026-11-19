import pandas as pd
import pytest

from housing_explorer.geo import add_distance_to, haversine_km, nearest_distance_km
from housing_explorer.ingest import load_sales
from housing_explorer.stats import monthly_trend, summarize_by_zip


def test_haversine_known_distance():
    # Austin to Dallas is roughly 292 km in a straight line.
    assert haversine_km(30.2672, -97.7431, 32.7767, -96.7970) == pytest.approx(292, abs=3)


def test_haversine_zero_for_same_point():
    assert haversine_km(40.0, -100.0, 40.0, -100.0) == 0


def test_add_distance_to_creates_column():
    df = pd.DataFrame({"latitude": [30.2672], "longitude": [-97.7431]})
    out = add_distance_to(df, "downtown", 30.2672, -97.7431)
    assert out["dist_downtown_km"].iloc[0] == 0
    assert "dist_downtown_km" not in df.columns  # input untouched


def test_nearest_distance_picks_closest_point():
    homes = pd.DataFrame({"latitude": [30.0], "longitude": [-97.0]})
    schools = pd.DataFrame({"latitude": [31.0, 30.01], "longitude": [-97.0, -97.0]})
    assert nearest_distance_km(homes, schools).iloc[0] == pytest.approx(1.112, abs=0.01)


def test_summarize_by_zip(sample_path):
    df, _ = load_sales(sample_path)
    summary = summarize_by_zip(df, min_sales=3)
    assert list(summary.index) == ["78704", "78701", "78705"]
    assert summary.loc["78704", "median_price"] == 510_000
    assert summary.loc["78701", "sales"] == 3


def test_monthly_trend_counts(sample_path):
    df, _ = load_sales(sample_path)
    trend = monthly_trend(df)
    assert trend["sales"].sum() == len(df)
