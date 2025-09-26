from pathlib import Path
from stats_processor import process_station_data


def process_station_daily_data(station_id: str, overwrite: bool = False) -> None:
    """
    Calculate daily statistics for TMIN, TMAX, PRCP of the specified station

    Args:
        station_id: Station ID, e.g., "JA000047662"
        overwrite: Whether to overwrite existing output files
    """
    prefix = station_id[:3]
    if prefix.endswith("0"):
        prefix = prefix[:-1]
    
    output_dir = Path(f"docs/plots/{prefix}/{station_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    process_station_data(station_id, "1d", output_dir, overwrite)


if __name__ == "__main__":
    # Add your test code here
    pass
    # Example: Process Tokyo station data
    # Tokyo: JA000047662
    # Beijing: CHM00054511
    # Shanghai: CHM00058362

    station_id = "JA000047662"  # Tokyo
    for station_id in ["JA000047662", "CHM00054511", "CHM00058362"]:
        process_station_daily_data(station_id, overwrite=True)
