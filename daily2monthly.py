import os
from pathlib import Path
from typing import Literal

import polars as pl


def process_station_monthly_data(station_id: str, overwrite: bool = False) -> None:
    """
    Calculate monthly statistics for TMIN, TMAX, PRCP of the specified station

    Args:
        station_id: Station ID, e.g., "JA000047662"
    """
    elements: list[Literal["TMIN", "TMAX", "PRCP"]] = ["TMIN", "TMAX", "PRCP"]

    # Create output directory
    output_dir = Path(f"data/parquet/by-station-monthly/STATION={station_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{station_id}-monthly.parquet"
    if output_file.exists() and not overwrite:
        print(f"File already exists and overwrite not set, skipping: {output_file}")
        return

    # Store monthly data for all elements
    all_monthly_data = []

    for element in elements:
        data_dir = f"data/parquet/by-station/STATION={station_id}/ELEMENT={element}/"

        # Check if data directory exists
        if not os.path.exists(data_dir):
            print(f"Warning: Data directory does not exist {data_dir}")
            continue

        try:
            # Read data
            df = pl.scan_parquet(data_dir)

            # Data preprocessing
            df = df.with_columns(
                pl.col("DATE").str.strptime(pl.Datetime, "%Y%m%d"),
                pl.col("DATA_VALUE") / 10,
            )

            # Sort
            df = df.sort("DATE")

            # Calculate monthly statistics
            monthly_df = (
                df.group_by_dynamic("DATE", every="1mo")
                .agg(
                    pl.col("DATA_VALUE").mean().alias(f"{element}_MEAN"),
                    pl.col("DATA_VALUE").min().alias(f"{element}_MIN"),
                    pl.col("DATA_VALUE").max().alias(f"{element}_MAX"),
                    pl.col("DATA_VALUE").quantile(0.1).alias(f"{element}_P10"),
                    pl.col("DATA_VALUE").quantile(0.2).alias(f"{element}_P20"),
                    pl.col("DATA_VALUE").quantile(0.5).alias(f"{element}_P50"),
                    pl.col("DATA_VALUE").quantile(0.8).alias(f"{element}_P80"),
                    pl.col("DATA_VALUE").quantile(0.9).alias(f"{element}_P90"),
                    pl.col("DATA_VALUE").sum().alias(f"{element}_SUM"),
                    pl.col("DATA_VALUE").count().alias(f"{element}_COUNT"),
                )
                .collect()
            )

            all_monthly_data.append(monthly_df)
            print(f"Processed {element} data, total {len(monthly_df)} monthly records")

        except Exception as e:
            print(f"Error processing {element} data: {e}")
            continue

    if all_monthly_data:
        # Merge data for all elements using join operation
        combined_df: pl.DataFrame = all_monthly_data[0]

        for i in range(1, len(all_monthly_data)):
            combined_df = combined_df.join(
                all_monthly_data[i], on="DATE", how="full", suffix=f"_{i}"
            )

        # Clean up extra DATE columns (keep the original DATE column)
        date_columns = [col for col in combined_df.columns if col.startswith("DATE_")]
        if date_columns:
            combined_df = combined_df.drop(date_columns)

        # Save to parquet file
        output_file = output_dir / f"{station_id}-monthly.parquet"
        combined_df.write_parquet(output_file)
        combined_df.write_excel(output_file.with_suffix(".xlsx"))

        print(f"Monthly statistics saved to: {output_file}")
        print(f"Total records: {len(combined_df)}")
        print(f"Data columns: {combined_df.columns}")
    else:
        print("No data processed successfully")


if __name__ == "__main__":
    # Example: Process Tokyo station data
    # Tokyo: JA000047662
    # Beijing: CHM00054511
    # Shanghai: CHM00058362
    for station_id in ["JA000047662", "CHM00054511", "CHM00058362"]:
        process_station_monthly_data(station_id)
