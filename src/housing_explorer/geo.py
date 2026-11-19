"""Geospatial helpers that work on plain pandas/numpy (no GIS stack required)."""

from __future__ import annotations

import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Accepts scalars or numpy-compatible arrays."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def add_distance_to(
    df: pd.DataFrame, name: str, lat: float, lon: float
) -> pd.DataFrame:
    """Return a copy of ``df`` with a ``dist_<name>_km`` column to a fixed point."""
    out = df.copy()
    out[f"dist_{name}_km"] = haversine_km(out["latitude"], out["longitude"], lat, lon).round(3)
    return out


def nearest_distance_km(df: pd.DataFrame, points: pd.DataFrame) -> pd.Series:
    """Distance from each row of ``df`` to the nearest row of ``points``.

    Both frames need ``latitude`` and ``longitude`` columns. Brute force is fine
    for a few thousand points; swap in a spatial index (e.g. BallTree) later.
    """
    if points.empty:
        return pd.Series(np.nan, index=df.index)
    d = haversine_km(
        df["latitude"].to_numpy()[:, None],
        df["longitude"].to_numpy()[:, None],
        points["latitude"].to_numpy()[None, :],
        points["longitude"].to_numpy()[None, :],
    )
    return pd.Series(d.min(axis=1).round(3), index=df.index)
