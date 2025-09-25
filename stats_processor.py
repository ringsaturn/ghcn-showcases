from pathlib import Path
from typing import Literal

import polars as pl
import json


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


def calculate_monthly_statistics(df: pl.LazyFrame, element: str) -> pl.DataFrame:
    """Calculate monthly statistics matching the required format."""
    return (
        df.filter(pl.col("DATE").dt.year() >= 1970)
        .with_columns(
            [
                pl.col("DATE").dt.month().alias("MONTH"),
                pl.col("DATE").dt.year().alias("YEAR"),
            ]
        )
        # First group by year and month to get annual values
        .group_by(["YEAR", "MONTH"])
        .agg(
            [
                pl.col("DATA_VALUE").quantile(0.1).alias(f"ANNUAL_{element}_P10"),
                pl.col("DATA_VALUE").quantile(0.9).alias(f"ANNUAL_{element}_P90"),
                pl.col("DATA_VALUE").min().alias(f"ANNUAL_{element}_MIN"),
                pl.col("DATA_VALUE").max().alias(f"ANNUAL_{element}_MAX"),
                pl.col("DATA_VALUE").sum().alias(f"ANNUAL_{element}_SUM"),
            ]
        )
        # Then group by month to get multi-year averages
        .group_by("MONTH")
        .agg(
            [
                pl.col(f"ANNUAL_{element}_P10").mean().alias(f"{element}_P10"),
                pl.col(f"ANNUAL_{element}_P90").mean().alias(f"{element}_P90"),
                pl.col(f"ANNUAL_{element}_MIN").min().alias(f"{element}_MIN"),
                pl.col(f"ANNUAL_{element}_MAX").max().alias(f"{element}_MAX"),
                pl.col(f"ANNUAL_{element}_SUM").mean().alias(f"{element}_SUM"),
            ]
        )
        .sort("MONTH")
        .collect()
    )


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

    for element in elements:
        try:
            # Read data from merged files and preprocess
            df = pl.scan_parquet(f"data/merged/{element}.parquet").filter(
                pl.col("ID") == station_id
            )
            
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
                stats_df = calculate_monthly_statistics(df, element)
                if element == "TMIN":
                    tmin_data = stats_df
                elif element == "TMAX":
                    tmax_data = stats_df
                else:  # PRCP
                    prcp_data = stats_df
                    
            print(f"Processed {element} data for {station_id}")

        except Exception as e:
            print(f"Error processing {element} data: {e}")
            continue

    # Combine the data
    try:
        # Combine data only if at least one element has stats
        if any([tmin_data is not None, tmax_data is not None, prcp_data is not None]):
            if time_window == "1d":
                # Build complete calendar of month/day and assign new DAY index
                key_frames = []
                for df in [tmin_data, tmax_data, prcp_data]:
                    if df is not None:
                        key_frames.append(df.select(["MONTH", "DAY_OF_MONTH"]))
                keys_df = key_frames[0]
                for kdf in key_frames[1:]:
                    keys_df = keys_df.vstack(kdf)
                keys_df = keys_df.unique().sort(["MONTH", "DAY_OF_MONTH"]).with_row_count("DAY", offset=1)
                # Left join stats to calendar
                combined_df = keys_df
                if tmin_data is not None:
                    combined_df = combined_df.join(tmin_data.drop("DAY"), on=["MONTH", "DAY_OF_MONTH"], how="left")
                if tmax_data is not None:
                    combined_df = combined_df.join(tmax_data.drop("DAY"), on=["MONTH", "DAY_OF_MONTH"], how="left")
                if prcp_data is not None:
                    combined_df = combined_df.join(prcp_data.drop("DAY"), on=["MONTH", "DAY_OF_MONTH"], how="left")
                # Select columns in the correct order
                combined_df = combined_df.select([
                    "DAY", "TMIN_P10", "TMAX_P90", "TMIN_MIN", "TMAX_MAX", "PRCP_SUM", "MONTH", "DAY_OF_MONTH"
                ])
            else:
                # Combine monthly data: build union of months and left join stats
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
                combined_df = combined_df.select([
                    "MONTH", 
                    pl.col("TMIN_P10").round(2), 
                    pl.col("TMAX_P90").round(2), 
                    pl.col("TMIN_MIN").round(2), 
                    pl.col("TMAX_MAX").round(2), 
                    pl.col("PRCP_SUM").round(2)
                ])
                
            # Write to CSV file if there is any combined data, else skip saving
            if len(combined_df) > 0:
                output_dir.mkdir(parents=True, exist_ok=True)
                # Generate JSON summary of counts
                stats_summary = {
                    "TMIN_count": 0 if tmin_data is None else tmin_data.height,
                    "TMAX_count": 0 if tmax_data is None else tmax_data.height,
                    "PRCP_count": 0 if prcp_data is None else prcp_data.height,
                    "combined_count": len(combined_df),
                }
                summary_file = output_dir / f"{station_id}-{period}-stats.json"
                with open(summary_file, "w") as sf:
                    json.dump(stats_summary, sf, indent=2)
                # Write CSV
                combined_df.write_csv(output_file)
                print(f"{period.capitalize()} statistics saved to: {output_file}")
                print(f"Summary JSON saved to: {summary_file}")
                print(f"Total records: {len(combined_df)}")
            else:
                print(f"No data for station {station_id}, skipping file creation: {output_file}")
        else:
            print(f"Missing data for station {station_id}, cannot create output file")
            
    except Exception as e:
        print(f"Error combining data: {e}")
