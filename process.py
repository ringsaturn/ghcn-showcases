import json
from multiprocessing import Pool
from pathlib import Path
from typing import Any
import polars as pl

from stats_processor import process_station_data

SCHEMA: dict[str, Any] = {
    "ID": pl.Utf8,
    "LATITUDE": pl.Float64,
    "LONGITUDE": pl.Float64,
    "ELEVATION": pl.Float64,
    "STATE": pl.Utf8,
    "NAME": pl.Utf8,
    "GSN_FLAG": pl.Utf8,
    "HCN_CRN_FLAG": pl.Utf8,
    "WMO_ID": pl.Utf8,
}


def read_stations() -> pl.DataFrame:
    """Read and parse stations data from ghcnd-stations.txt"""
    fp: str = "data/ghcnd-stations.txt"
    with open(fp, "r") as f:
        lines = []
        for line in f:
            if len(line.strip()) > 0:  # Skip empty lines
                id = line[0:11].strip()
                latitude = line[12:20].strip()
                longitude = line[21:30].strip()
                elevation = line[31:37].strip()
                state = line[38:40].strip()
                name = line[41:71].strip()
                gsn_flag = line[72:75].strip()
                hcn_crn_flag = line[76:79].strip()
                wmo_id = line[80:85].strip() if len(line) > 80 else ""
                lines.append(
                    [
                        id,
                        latitude,
                        longitude,
                        elevation,
                        state,
                        name,
                        gsn_flag,
                        hcn_crn_flag,
                        wmo_id,
                    ]
                )

    return pl.DataFrame(lines, schema=SCHEMA)


def filter_stations(df: pl.DataFrame) -> pl.DataFrame:
    """Filter stations based on predefined prefixes"""
    return df.filter(
        pl.col("ID").str.starts_with("CHM")
        | pl.col("ID").str.starts_with("JA")
        | pl.col("ID").str.starts_with("KSM")
        | pl.col("ID").str.starts_with("FRE")
        | pl.col("ID").str.starts_with("GMM")
        | pl.col("ID").str.starts_with("UKE")
        | pl.col("ID").str.starts_with("IDM")
        | pl.col("ID").str.starts_with("MXM")
    )


def process_data(input_df: pl.DataFrame) -> None:
    """Process both daily and monthly data for all stations in parallel"""
    p = Pool(8)
    for station_id in input_df["ID"]:
        prefix = station_id[:3]
        if prefix.endswith("0"):
            prefix = prefix[:-1]

        daily_dir = Path(f"docs/plots/{prefix}/{station_id}")
        monthly_dir = Path(f"docs/plots/{prefix}/{station_id}")
        daily_dir.mkdir(parents=True, exist_ok=True)
        monthly_dir.mkdir(parents=True, exist_ok=True)

        p.apply_async(process_station_data, args=(station_id, "1mo", monthly_dir, True))
        p.apply_async(process_station_data, args=(station_id, "1d", daily_dir, True))

    p.close()
    p.join()


def dump_matched_as_geojson(input_df: pl.DataFrame) -> None:
    """Convert matched stations data to GeoJSON format"""
    plots_dir = Path("docs/plots")
    features = []

    for row in input_df.iter_rows(named=True):
        station_id = row["ID"]

        # Check if plot data files exist for this station
        prefix = station_id[:3]
        if prefix.endswith("0"):
            prefix = prefix[:-1]
        station_dir = plots_dir / prefix / station_id
        if not station_dir.exists():
            missing_data = True
        else:
            daily_plot = station_dir / f"{station_id}-daily.csv"
            monthly_plot = station_dir / f"{station_id}-monthly.csv"
            missing_data = not (daily_plot.exists() and monthly_plot.exists())

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["LONGITUDE"], row["LATITUDE"]],
            },
            "properties": {
                "ID": row["ID"],
                "NAME": row["NAME"],
                "STATE": row["STATE"],
                "ELEVATION": row["ELEVATION"],
                "GSN_FLAG": row["GSN_FLAG"],
                "HCN_CRN_FLAG": row["HCN_CRN_FLAG"],
                "WMO_ID": row["WMO_ID"],
                "MISSING": missing_data,
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open("docs/matched_stations.geojson", "w") as f:
        json.dump(geojson, f, indent=2)


def main() -> None:
    """Main entry point"""
    # Read and filter stations
    stations_df = read_stations()
    matched_stations = filter_stations(stations_df)

    # Process data
    process_data(matched_stations)
    dump_matched_as_geojson(matched_stations)


if __name__ == "__main__":
    main()
