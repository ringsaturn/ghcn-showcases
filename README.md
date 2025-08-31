# Have fun with `GHCN-D` data.

Data source: <https://registry.opendata.aws/noaa-ghcn/>

- Setup Dir

  ```bash
  mkdir -p data/parquet/by-station
  ```

- Sync data

  - Sync via AWS CLI

    ```bash
    aws s3 cp --region us-west-2 --no-sign-request s3://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-stations.txt data/ghcnd-stations.txt

    aws s3 cp --recursive --region us-west-2 --no-sign-request s3://noaa-ghcn-pds.s3.amazonaws.com/parquet/by_station data/parquet/by-station
    ```

  - Sync via JuiceFS(Alternative)

    ```bash
    juicefs sync s3://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-stations.txt data/ghcnd-stations.txt

    juicefs sync s3://noaa-ghcn-pds.s3.amazonaws.com/parquet/by_station data/parquet/by-station
    ```

- Run: `uv run process.py`
