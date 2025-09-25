import polars as pl

SCHEMA: pl.Schema = pl.Schema(
    {
        "ID": pl.Utf8,
        "DATE": pl.Utf8,
        "DATA_VALUE": pl.Int64,
    }
)

ELEMEMENTS: list[str] = ["TMIN", "TMAX", "PRCP"]

for element in ELEMEMENTS:
    fp_pattern: str = f"data/parquet/by-station/STATION=*/ELEMENT={element}/*.parquet"

    df: pl.DataFrame = (
        pl.scan_parquet(fp_pattern, schema=SCHEMA, extra_columns="ignore")
        .with_columns(
            pl.col("DATE").str.strptime(pl.Date, "%Y%m%d"),
        )
        .sort("ID", "DATE", descending=[False, False])
        .collect()
    )

    df.write_parquet(
        f"data/merged/{element}.parquet",
        mkdir=True,
    )
