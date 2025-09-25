from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

plt.style.use("seaborn-v0_8-darkgrid")


def ploat_station(
    station_id: str,
    saved_dir: Path = Path("data/plots"),
    overwrite: bool = False,
    csv_only: bool = True,
) -> None:
    fp: str = (
        f"data/parquet/by-station-daily/STATION={station_id}/{station_id}-daily.parquet"
    )
    # saved_fp = f"data/plots/{station_id}-monthly.png"
    # output_dir.mkdir(parents=True, exist_ok=True)
    saved_dir.mkdir(parents=True, exist_ok=True)
    saved_fp = saved_dir / f"{station_id}-daily.webp"
    if (not overwrite) and saved_fp.exists():
        print(f"{saved_fp} exists, skip.")
        return

    df: pl.LazyFrame = pl.scan_parquet(fp)

    # Requirement: Calculate the temperature range for 366 days of the year (P10 of TMIN and P90 of TMAX), average over data from 1970 to present. Also daily precipitation, output to a df

    agg_df: pl.DataFrame = (
        df.filter(pl.col("DATE").dt.year() >= 1970)
        .with_columns(
            [
                pl.col("DATE").dt.year().alias("YEAR"),
                pl.col("DATE")
                .dt.ordinal_day()
                .alias("DAY"),  # Use ordinal_day to get day of year
                pl.col("DATE").dt.month().alias("MONTH"),
                pl.col("DATE").dt.day().alias("DAY_OF_MONTH"),
            ]
        )
        .group_by("DAY")
        .agg(
            [
                pl.col("TMIN_P10").mean().alias("TMIN_P10"),
                pl.col("TMAX_P90").mean().alias("TMAX_P90"),
                pl.col("TMIN_MIN").min().alias("TMIN_MIN"),
                pl.col("TMAX_MAX").max().alias("TMAX_MAX"),
                pl.col("PRCP_SUM").mean().alias("PRCP_SUM"),
                pl.col("MONTH").first().alias("MONTH"),
                pl.col("DAY_OF_MONTH").first().alias("DAY_OF_MONTH"),
            ]
        )
        .sort("DAY")
        .collect()
    )
    if agg_df.is_empty():
        print(f"{station_id} has no data after 1970, skip.")
        return
    # save to csv for debug
    agg_df.write_csv(saved_fp.with_suffix(".csv"), float_precision=2)
    if csv_only:
        print(f"Saved CSV only to {saved_fp.with_suffix('.csv')}, skip plotting.")
        return

    # Visualize monthly average TMIN_P10, TMAX_P90, PRCP_SUM of agg_df

    # Create a larger figure and set higher DPI
    fig, ax1 = plt.subplots(figsize=(12, 8), dpi=300)

    # Plot TMIN_P10 and TMAX_P90
    ax1.plot(
        agg_df["DAY"],
        agg_df["TMIN_P10"],
        label="TMIN_P10",
        color="tab:blue",
        alpha=0.7,
    )
    ax1.plot(
        agg_df["DAY"],
        agg_df["TMAX_P90"],
        label="TMAX_P90",
        color="tab:red",
        alpha=0.7,
    )
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Temperature (°C)")

    # Set x-axis ticks and labels
    # Select the 1st of each month as major tick points
    tick_df = agg_df.filter(pl.col("DAY_OF_MONTH") == 1)
    major_ticks = tick_df["DAY"].to_list()
    major_labels = [f"{m}/1" for m in tick_df["MONTH"].to_list()]

    ax1.set_xticks(major_ticks)
    ax1.set_xticklabels(major_labels, rotation=45)

    # Add grid lines for easier viewing
    ax1.grid(True, which="major", linestyle="-", alpha=0.2)
    ax1.legend(loc="upper left")

    # Use second y-axis for precipitation
    ax2 = ax1.twinx()
    ax2.bar(
        agg_df["DAY"],
        agg_df["PRCP_SUM"],
        alpha=0.2,
        color="tab:green",
        label="PRCP_SUM",
        width=1,  # Set bar width to 1 day
    )
    ax2.set_ylabel("Precipitation (mm)")
    ax2.legend(loc="upper right")

    plt.title(f"{station_id} Daily Mean TMIN_P10, TMAX_P90, and PRCP_SUM")
    plt.suptitle("Data from 1970 to Present", fontsize=10)
    plt.tight_layout()

    plt.rcParams["figure.dpi"] = 500

    # Use highest quality settings when saving image
    plt.savefig(
        saved_fp,
        bbox_inches="tight",  # Automatically adjust margins
        pad_inches=0.1,  # Set margins
        dpi=500,
    )  # Ensure using high DPI
    plt.close()


if __name__ == "__main__":
    for station_id in ["JA000047662", "CHM00054511", "CHM00058362"]:
        ploat_station(station_id, csv_only=False)
