import polars as pl
from typing import Tuple


def check_data_quality(df: pl.LazyFrame, start_year: int = 1970) -> Tuple[bool, float]:
    """
    Check if the data quality is good enough from a specific start year.

    Args:
        df: LazyFrame containing the weather data
        start_year: The start year for quality check (default: 1970)

    Returns:
        Tuple[bool, float]: (is_quality_good, data_completeness_ratio)
        - is_quality_good: True if the data quality meets the requirements
        - data_completeness_ratio: The ratio of valid observations to total possible observations
    """
    stats = (
        df.filter(pl.col("DATE").dt.year() >= start_year)
        .select(
            [
                pl.col("DATA_VALUE").is_not_null().sum().alias("valid_count"),
                pl.len().alias("total_count"),
            ]
        )
        .collect()
    )

    valid_count = stats[0]["valid_count"].item()
    total_count = stats[0]["total_count"].item()

    # Calculate the ratio of valid data points
    completeness_ratio = valid_count / total_count if total_count > 0 else 0.0

    # Consider data quality good if we have at least 70% of the possible observations
    # You can adjust this threshold based on your needs
    is_quality_good = completeness_ratio >= 0.7

    return bool(is_quality_good), float(completeness_ratio)
