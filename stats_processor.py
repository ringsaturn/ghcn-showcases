from pathlib import Path
from typing import Literal

import polars as pl
import json

from data_quality import check_data_quality


def calculate_daily_statistics(df: pl.LazyFrame, element: str) -> pl.DataFrame:
    """Calculate daily statistics matching the required format."""
    # Compute daily statistics by grouping first annually by month/day, then across years
    return (
        df.filter(pl.col("DATE").dt.year() >= 1970)
        .with_columns(
            [
                pl.col("DATE").dt.month().alias("MONTH"),
                pl.col("DATE").dt.day().alias("DAY_OF_MONTH"),
                pl.col("DATE").dt.year().alias("YEAR"),
            ]
        )
        # First group by year, month, day_of_month to get annual values
        .group_by(["YEAR", "MONTH", "DAY_OF_MONTH"])
        .agg(
            [
                pl.col("DATA_VALUE").quantile(0.1).alias(f"ANNUAL_{element}_P10"),
                pl.col("DATA_VALUE").quantile(0.9).alias(f"ANNUAL_{element}_P90"),
                pl.col("DATA_VALUE").min().alias(f"ANNUAL_{element}_MIN"),
                pl.col("DATA_VALUE").max().alias(f"ANNUAL_{element}_MAX"),
                pl.col("DATA_VALUE").sum().alias(f"ANNUAL_{element}_SUM"),
            ]
        )
        # Then group by month, day_of_month to get multi-year averages
        .group_by(["MONTH", "DAY_OF_MONTH"])
        .agg(
            [
                pl.col(f"ANNUAL_{element}_P10").mean().alias(f"{element}_P10"),
                pl.col(f"ANNUAL_{element}_P90").mean().alias(f"{element}_P90"),
                pl.col(f"ANNUAL_{element}_MIN").min().alias(f"{element}_MIN"),
                pl.col(f"ANNUAL_{element}_MAX").max().alias(f"{element}_MAX"),
                pl.col(f"ANNUAL_{element}_SUM").mean().alias(f"{element}_SUM"),
            ]
        )
        # Sort by calendar order and assign sequential DAY index after sorting calendar days
        .sort(["MONTH", "DAY_OF_MONTH"])
        .with_row_index("DAY", offset=1)
        .collect()
    )


def calculate_monthly_statistics(
    df: pl.LazyFrame, element: str
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Calculate monthly statistics and provide the full month-by-month history.

    Returns:
        A tuple of (monthly_climatology, monthly_history) where:
            - monthly_climatology contains 12 rows (one per calendar month) with
              aggregated statistics across all available years.
            - monthly_history contains one row per year-month from 1970 onwards
              with the same statistics as the climatology, plus entry counts and
              the period start date.
    """

    # First, calculate the total days in each month and valid observations
    monthly_summary = (
        df.filter(pl.col("DATE").dt.year() >= 1970)
        .with_columns(
            [
                pl.col("DATE").dt.month().alias("MONTH"),
                pl.col("DATE").dt.year().alias("YEAR"),
                pl.col("DATE").dt.days_in_month().alias("DAYS_IN_MONTH"),
                pl.col("DATA_VALUE").is_not_null().alias("IS_VALID"),
            ]
        )
        .group_by(["YEAR", "MONTH"])
        .agg(
            [
                # Calculate valid data ratio and entry count
                pl.col("IS_VALID").sum().alias("VALID_COUNT"),
                pl.len().alias("ENTRY_COUNT"),  # Keep original ENTRY_COUNT for frontend
                pl.col("DAYS_IN_MONTH").first().alias("DAYS_IN_MONTH"),
                # Only calculate statistics on valid data
                pl.col("DATA_VALUE")
                .filter(pl.col("DATA_VALUE").is_not_null())
                .quantile(0.1)
                .alias(f"ANNUAL_{element}_P10"),
                pl.col("DATA_VALUE")
                .filter(pl.col("DATA_VALUE").is_not_null())
                .quantile(0.9)
                .alias(f"ANNUAL_{element}_P90"),
                pl.col("DATA_VALUE")
                .filter(pl.col("DATA_VALUE").is_not_null())
                .min()
                .alias(f"ANNUAL_{element}_MIN"),
                pl.col("DATA_VALUE")
                .filter(pl.col("DATA_VALUE").is_not_null())
                .max()
                .alias(f"ANNUAL_{element}_MAX"),
                pl.col("DATA_VALUE")
                .filter(pl.col("DATA_VALUE").is_not_null())
                .sum()
                .alias(f"ANNUAL_{element}_SUM"),
            ]
        )
        # Calculate completeness ratio and filter out months with insufficient data
        .with_columns(
            (pl.col("VALID_COUNT") / pl.col("DAYS_IN_MONTH")).alias(
                "COMPLETENESS_RATIO"
            )
        )
        .filter(pl.col("COMPLETENESS_RATIO") >= 0.7)
        .with_columns(
            pl.datetime(
                year=pl.col("YEAR"),
                month=pl.col("MONTH"),
                day=pl.lit(1),
            )
            .dt.date()
            .alias("PERIOD_START")
        )
        .sort(["YEAR", "MONTH"])
        .collect()
    )

    rename_map = {
        f"ANNUAL_{element}_P10": f"{element}_P10",
        f"ANNUAL_{element}_P90": f"{element}_P90",
        f"ANNUAL_{element}_MIN": f"{element}_MIN",
        f"ANNUAL_{element}_MAX": f"{element}_MAX",
        f"ANNUAL_{element}_SUM": f"{element}_SUM",
        "ENTRY_COUNT": f"{element}_ENTRY_COUNT",  # Keep original ENTRY_COUNT for frontend
    }

    monthly_history = monthly_summary.rename(rename_map).select(
        [
            "YEAR",
            "MONTH",
            "PERIOD_START",
            f"{element}_P10",
            f"{element}_P90",
            f"{element}_MIN",
            f"{element}_MAX",
            f"{element}_SUM",
            f"{element}_ENTRY_COUNT",  # Keep original ENTRY_COUNT for frontend
        ]
    )

    monthly_climatology = (
        monthly_history.lazy()
        .group_by("MONTH")
        .agg(
            [
                pl.col(f"{element}_P10").mean().alias(f"{element}_P10"),
                pl.col(f"{element}_P90").mean().alias(f"{element}_P90"),
                pl.col(f"{element}_MIN").min().alias(f"{element}_MIN"),
                pl.col(f"{element}_MAX").max().alias(f"{element}_MAX"),
                pl.col(f"{element}_SUM").mean().alias(f"{element}_SUM"),
            ]
        )
        .sort("MONTH")
        .collect()
    )

    return monthly_climatology, monthly_history


def process_station_data(
    station_id: str,
    time_window: Literal["1d", "1mo"],
    output_dir: Path,
    overwrite: bool = False,
) -> None:
    """
    Calculate statistics for TMIN, TMAX, PRCP of the specified station

    Args:
        station_id: Station ID, e.g., "JA000047662"
        time_window: Time window for grouping data, "1d" for daily, "1mo" for monthly
        output_dir: Directory to save the output CSV file
        overwrite: Whether to overwrite existing output files
    """
    # Elements to process: TMIN, TMAX, PRCP
    elements: list[str] = ["TMIN", "TMAX", "PRCP"]
    period = "daily" if time_window == "1d" else "monthly"
    output_file = output_dir / f"{station_id}-{period}.csv"

    if output_file.exists() and not overwrite:
        print(f"File already exists and overwrite not set, skipping: {output_file}")
        return

    # Store data for all elements
    tmin_data = None
    tmax_data = None
    prcp_data = None
    tmin_history = None
    tmax_history = None
    prcp_history = None
    raw_entry_counts: dict[str, int] = {}
    data_quality: dict[str, tuple[bool, float]] = {}

    for element in elements:
        try:
            # Read data from merged files and preprocess
            df = pl.scan_parquet(f"data/merged/{element}.parquet").filter(
                pl.col("ID") == station_id
            )

            # Check data quality
            is_quality_good, completeness_ratio = check_data_quality(df)
            data_quality[element] = (is_quality_good, completeness_ratio)

            if not is_quality_good:
                print(
                    f"Warning: Station {station_id} has poor data quality for {element} (completeness: {completeness_ratio:.2%})"
                )
                return

            # Count raw records that contribute to statistics
            raw_count = (
                df.filter(pl.col("DATE").dt.year() >= 1970)
                .filter(pl.col("DATA_VALUE").is_not_null())
                .select(pl.len().alias("row_count"))
                .collect()
                .item()
            )
            raw_entry_counts[element] = raw_count

            # Only TMIN and TMAX need to be divided by 10 for unit conversion
            if element in ["TMIN", "TMAX"]:
                df = df.with_columns(pl.col("DATA_VALUE") / 10)

            # Calculate statistics based on time window
            if time_window == "1d":
                stats_df = calculate_daily_statistics(df, element)
                if element == "TMIN":
                    tmin_data = stats_df
                elif element == "TMAX":
                    tmax_data = stats_df
                else:  # PRCP
                    prcp_data = stats_df
            else:  # "1mo"
                climatology_df, history_df = calculate_monthly_statistics(df, element)
                if element == "TMIN":
                    tmin_data = climatology_df
                    tmin_history = history_df
                elif element == "TMAX":
                    tmax_data = climatology_df
                    tmax_history = history_df
                else:  # PRCP
                    prcp_data = climatology_df
                    prcp_history = history_df

            print(f"Processed {element} data for {station_id}")

        except Exception as e:
            print(f"Error processing {element} data: {e}")
            continue

    # Combine the data
    monthly_history_df = None
    try:
        if any([tmin_data is not None, tmax_data is not None, prcp_data is not None]):
            if time_window == "1d":
                key_frames = []
                for df in [tmin_data, tmax_data, prcp_data]:
                    if df is not None:
                        key_frames.append(df.select(["MONTH", "DAY_OF_MONTH"]))
                keys_df = key_frames[0]
                for kdf in key_frames[1:]:
                    keys_df = keys_df.vstack(kdf)
                keys_df = (
                    keys_df.unique()
                    .sort(["MONTH", "DAY_OF_MONTH"])
                    .with_row_count("DAY", offset=1)
                )
                combined_df = keys_df
                if tmin_data is not None:
                    combined_df = combined_df.join(
                        tmin_data.drop("DAY"),
                        on=["MONTH", "DAY_OF_MONTH"],
                        how="left",
                    )
                if tmax_data is not None:
                    combined_df = combined_df.join(
                        tmax_data.drop("DAY"),
                        on=["MONTH", "DAY_OF_MONTH"],
                        how="left",
                    )
                if prcp_data is not None:
                    combined_df = combined_df.join(
                        prcp_data.drop("DAY"),
                        on=["MONTH", "DAY_OF_MONTH"],
                        how="left",
                    )
                combined_df = combined_df.select(
                    [
                        "DAY",
                        pl.col("TMIN_P10").round(2).alias("TMIN_P10"),
                        pl.col("TMAX_P90").round(2).alias("TMAX_P90"),
                        pl.col("TMIN_MIN").round(2).alias("TMIN_MIN"),
                        pl.col("TMAX_MAX").round(2).alias("TMAX_MAX"),
                        pl.col("PRCP_SUM").round(2).alias("PRCP_SUM"),
                        "MONTH",
                        "DAY_OF_MONTH",
                    ]
                )
            else:
                month_keys = []
                for df in [tmin_data, tmax_data, prcp_data]:
                    if df is not None:
                        month_keys.append(df.select(["MONTH"]))
                keys_df = month_keys[0]
                for mk in month_keys[1:]:
                    keys_df = keys_df.vstack(mk)
                keys_df = keys_df.unique().sort("MONTH")
                combined_df = keys_df
                if tmin_data is not None:
                    combined_df = combined_df.join(tmin_data, on="MONTH", how="left")
                if tmax_data is not None:
                    combined_df = combined_df.join(tmax_data, on="MONTH", how="left")
                if prcp_data is not None:
                    combined_df = combined_df.join(prcp_data, on="MONTH", how="left")
                combined_df = combined_df.select(
                    [
                        "MONTH",
                        pl.col("TMIN_P10").round(2).alias("TMIN_P10"),
                        pl.col("TMAX_P90").round(2).alias("TMAX_P90"),
                        pl.col("TMIN_MIN").round(2).alias("TMIN_MIN"),
                        pl.col("TMAX_MAX").round(2).alias("TMAX_MAX"),
                        pl.col("PRCP_SUM").round(2).alias("PRCP_SUM"),
                    ]
                )

                history_sources = [tmin_history, tmax_history, prcp_history]
                non_empty_history = [
                    df for df in history_sources if df is not None and not df.is_empty()
                ]
                if non_empty_history:
                    history_keys = non_empty_history[0].select(
                        ["YEAR", "MONTH", "PERIOD_START"]
                    )
                    for hist in non_empty_history[1:]:
                        history_keys = history_keys.vstack(
                            hist.select(["YEAR", "MONTH", "PERIOD_START"])
                        )
                    history_keys = (
                        history_keys.lazy()
                        .group_by(["YEAR", "MONTH"])
                        .agg(pl.col("PERIOD_START").min().alias("PERIOD_START"))
                        .sort(["YEAR", "MONTH"])
                        .collect()
                    )

                    monthly_history_df = history_keys
                    if tmin_history is not None:
                        monthly_history_df = monthly_history_df.join(
                            tmin_history.drop(["PERIOD_START"]),
                            on=["YEAR", "MONTH"],
                            how="left",
                        )
                    if tmax_history is not None:
                        monthly_history_df = monthly_history_df.join(
                            tmax_history.drop(["PERIOD_START"]),
                            on=["YEAR", "MONTH"],
                            how="left",
                        )
                    if prcp_history is not None:
                        monthly_history_df = monthly_history_df.join(
                            prcp_history.drop(["PERIOD_START"]),
                            on=["YEAR", "MONTH"],
                            how="left",
                        )

                    value_columns = [
                        f"{element}_{suffix}"
                        for element in ["TMIN", "TMAX", "PRCP"]
                        for suffix in ["P10", "P90", "MIN", "MAX", "SUM"]
                    ]
                    existing_value_columns = [
                        col
                        for col in value_columns
                        if col in monthly_history_df.columns
                    ]
                    entry_columns = [
                        col
                        for col in [
                            "TMIN_ENTRY_COUNT",
                            "TMAX_ENTRY_COUNT",
                            "PRCP_ENTRY_COUNT",
                        ]
                        if col in monthly_history_df.columns
                    ]
                    monthly_history_df = (
                        monthly_history_df.with_columns(
                            [pl.col(col).round(2) for col in existing_value_columns]
                        )
                        .select(
                            [
                                "PERIOD_START",
                                "YEAR",
                                "MONTH",
                                *existing_value_columns,
                                *entry_columns,
                            ]
                        )
                        .sort(["YEAR", "MONTH"])
                    )

            if len(combined_df) > 0:
                output_dir.mkdir(parents=True, exist_ok=True)
                stats_summary = {
                    "TMIN_raw_count": raw_entry_counts.get("TMIN", 0),
                    "TMAX_raw_count": raw_entry_counts.get("TMAX", 0),
                    "PRCP_raw_count": raw_entry_counts.get("PRCP", 0),
                }
                if time_window == "1mo" and monthly_history_df is not None:
                    stats_summary["monthly_history_rows"] = len(monthly_history_df)

                summary_file = output_dir / f"{station_id}-{period}-stats.json"
                with open(summary_file, "w") as sf:
                    json.dump(stats_summary, sf, indent=2)

                combined_df.write_csv(output_file, float_precision=2)
                if monthly_history_df is not None:
                    history_output = output_dir / f"{station_id}-monthly-history.csv"
                    monthly_history_df.write_csv(history_output, float_precision=2)
                    print(f"Monthly history saved to: {history_output}")

                print(f"{period.capitalize()} statistics saved to: {output_file}")
                print(f"Summary JSON saved to: {summary_file}")
                print(f"Total records: {len(combined_df)}")
            else:
                print(
                    f"No data for station {station_id}, skipping file creation: {output_file}"
                )
        else:
            print(f"Missing data for station {station_id}, cannot create output file")

    except Exception as e:
        print(f"Error combining data: {e}")
