from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample" / "sales_sample.csv"


@pytest.fixture
def sample_path() -> Path:
    return SAMPLE
