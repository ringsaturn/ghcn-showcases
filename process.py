from multiprocessing import Pool, freeze_support
from pathlib import Path

import polars as pl

from daily2dailystatics import process_station_daily_data
from daily2monthly import process_station_monthly_data
from plotdaily import ploat_station as plot_station_daily_data  # noqa
from plotmonthly import ploat_station as plot_station_monthly_data  # noqa

fp: str = "data/ghcnd-stations.txt"

SCHEMA: dict[str, pl.Any] = {
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

df = pl.DataFrame(
    lines,
    schema=SCHEMA,
)

matched = df.filter(
    pl.col("ID").str.starts_with("CHM")
    | pl.col("ID").str.starts_with("JA")
    | pl.col("ID").str.starts_with("KSM")
    | pl.col("ID").str.starts_with("FRE")
    | pl.col("ID").str.starts_with("GMM")
    | pl.col("ID").str.starts_with("UKE")
    | pl.col("ID").str.starts_with("IDM")
    | pl.col("ID").str.starts_with("MXM")
    | pl.col("ID").str.starts_with("NLE")
)


def process_data(input_df: pl.DataFrame) -> None:
    p = Pool(8)
    for station_id in input_df["ID"]:
        p.apply_async(process_station_monthly_data, args=(station_id,))
        p.apply_async(process_station_daily_data, args=(station_id,))

    p.close()
    p.join()


def process_plot(input_df: pl.DataFrame) -> None:
    p = Pool(8)
    for station_id in input_df["ID"]:
        prefix = station_id[:3]
        if prefix.endswith("0"):
            prefix = prefix[:-1]
        output_dir = Path(f"docs/plots/{prefix}/{station_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        p.apply_async(
            plot_station_monthly_data, args=(station_id, output_dir, False)
        )
        p.apply_async(
            plot_station_daily_data, args=(station_id, output_dir, False)
        )

    p.close()
    p.join()


def dump_matched_as_geojson(input_df: pl.DataFrame) -> None:
    features = []
    for row in input_df.iter_rows(named=True):
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
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    import json

    with open("docs/matched_stations.geojson", "w") as f:
        json.dump(geojson, f, indent=2)


if __name__ == "__main__":
    freeze_support()

    process_data(matched)
    process_plot(matched)
    dump_matched_as_geojson(matched)
